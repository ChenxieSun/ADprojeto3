import requests
import json
from kazoo.client import KazooClient
from datetime import datetime
import ssl

class CoinCenterClient:
    def __init__(self):
        self.base_url = "https://localhost:5000"
        
        # SSL/TLS 配置
        self.session = requests.Session()
        self.session.verify = 'root.pem'  # 信任的CA根证书
        self.session.cert = ('cli.crt', 'cli.key')  # 客户端证书和私钥
        
        # 禁用不安全的SSL警告(仅开发环境)
        requests.packages.urllib3.disable_warnings()
        
        self.current_user = None
        
        # ZooKeeper初始化
        self.zk = KazooClient(hosts='127.0.0.1:2181')
        self.zk.start()
        self.setup_asset_watch()
    
    def setup_asset_watch(self):
        """设置ZooKeeper资产变更监控"""
        @self.zk.ChildrenWatch("/Assets")
        def watch_children(children):
            if children:
                print(f"\n[ZooKeeper通知] 检测到资产变更: {children}")
    
    def login(self, client_id=None):
        """用户登录/注册"""
        url = f"{self.base_url}/login"
        data = {"client_id": client_id} if client_id else {}
        
        try:
            # 调试输出
            print(f"发送登录请求到 {url}，数据: {data}")
            
            response = self.session.post(
                url,
                json=data,
                headers={'Content-Type': 'application/json'}
            )
            
            # 打印原始响应（调试用）
            print("原始响应:", response.text)
            
            if response.status_code == 204:  # 无内容
                raise ValueError("服务器返回空响应")
                
            json_data = response.json()  # 尝试解析JSON
            self.current_user = json_data
            print(f"登录成功! 用户ID: {json_data.get('client_id')}")
            
        except ValueError as e:
            print(f"JSON解析错误: {e}，响应内容: '{response.text}'")
        except Exception as e:
            print(f"登录失败: {str(e)}")
    
    def get_asset(self, symbol):
        """获取单个资产信息"""
        try:
            response = self.session.get(f"{self.base_url}/asset", params={"symbol": symbol})
            self._handle_response(response)
        except requests.exceptions.RequestException as e:
            print(f"连接错误: {str(e)}")
    
    def get_asset_set(self, symbols):
        """获取多个资产信息"""
        try:
            response = self.session.get(
                f"{self.base_url}/assetset",
                params={"symbols": ",".join(symbols)}
            )
            self._handle_response(response)
        except requests.exceptions.RequestException as e:
            print(f"连接错误: {str(e)}")
    
    def get_user_info(self):
        """获取当前用户信息"""
        if not self.current_user:
            print("请先登录")
            return
            
        try:
            response = self.session.get(
                f"{self.base_url}/user",
                params={"client_id": self.current_user['client_id']}
            )
            self._handle_response(response)
        except requests.exceptions.RequestException as e:
            print(f"连接错误: {str(e)}")
    
    def buy_asset(self, symbol, quantity):
        """购买资产"""
        self._trade_asset("buy", symbol, quantity)
    
    def sell_asset(self, symbol, quantity):
        """出售资产"""
        self._trade_asset("sell", symbol, quantity)
    
    def _trade_asset(self, action, symbol, quantity):
        if not self.current_user:
            print("请先登录")
            return
            
        try:
            response = self.session.post(
                f"{self.base_url}/{action}",
                json={
                    "client_id": self.current_user['client_id'],
                    "symbol": symbol,
                    "quantity": float(quantity)
                }
            )
            self._handle_response(response)
        except requests.exceptions.RequestException as e:
            print(f"连接错误: {str(e)}")
    
    def deposit(self, amount):
        """存款"""
        self._manage_funds("deposit", amount)
    
    def withdraw(self, amount):
        """取款"""
        self._manage_funds("withdraw", amount)
    
    def _manage_funds(self, action, amount):
        if not self.current_user:
            print("请先登录")
            return
            
        try:
            response = self.session.post(
                f"{self.base_url}/{action}",
                json={
                    "client_id": self.current_user['client_id'],
                    "amount": float(amount)
                }
            )
            self._handle_response(response)
        except requests.exceptions.RequestException as e:
            print(f"连接错误: {str(e)}")
    
    def get_transactions(self, start_time=None, end_time=None):
        """获取交易记录(仅管理员)"""
        if not self.current_user:
            print("请先登录")
            return
            
        params = {}
        if start_time:
            params["start"] = datetime.strptime(start_time, "%Y-%m-%d").isoformat()
        if end_time:
            params["end"] = datetime.strptime(end_time, "%Y-%m-%d").isoformat()
            
        try:
            response = self.session.get(
                f"{self.base_url}/transactions",
                params=params
            )
            self._handle_response(response)
        except requests.exceptions.RequestException as e:
            print(f"连接错误: {str(e)}")
    
    def _handle_response(self, response):
        """统一处理响应"""
        try:
            data = response.json()
            if response.ok:
                print(json.dumps(data, indent=2, ensure_ascii=False))
            else:
                print(f"错误 {response.status_code}: {data.get('detail', '未知错误')}")
        except ValueError:
            print(f"无效的响应: {response.text}")

def print_help():
    print("""
commdos:
  LOGIN [client_id]       - 登录/注册用户
  ASSET <symbol>          - 查询资产信息
  ASSETSET <sym1,sym2>   - 查询多个资产
  USER                   - 查看用户信息
  BUY <symbol> <qty>     - 购买资产
  SELL <symbol> <qty>    - 出售资产
  DEPOSIT <amount>       - 存款
  WITHDRAW <amount>      - 取款
  TRANSACTIONS [start end]- 查看交易记录(格式:YYYY-MM-DD)
  help                   - 显示帮助
  exit                   - 退出
""")

def main():
    client = CoinCenterClient()
    print("CoinCenter 交易系统客户端")
    print_help()
    
    while True:
        try:
            cmd = input("> ").strip().split()
            if not cmd:
                continue
                
            if cmd[0] == 'login' or cmd[0] == 'LOGIN':
                client.login(cmd[1] if len(cmd) > 1 else None)
            elif (cmd[0] == 'asset' or cmd[0] == 'ASSET') and len(cmd) > 1:
                client.get_asset(cmd[1])
            elif (cmd[0] == 'assetset' or cmd[0] == 'ASSETSET') and len(cmd) > 1:
                client.get_asset_set(cmd[1].split(','))
            elif cmd[0] == 'user' or cmd[0]=='USER':
                client.get_user_info()
            elif cmd[0] == 'buy' and len(cmd) > 2:
                client.buy_asset(cmd[1], cmd[2])
            elif cmd[0] == 'sell' and len(cmd) > 2:
                client.sell_asset(cmd[1], cmd[2])
            elif cmd[0] == 'deposit' and len(cmd) > 1:
                client.deposit(cmd[1])
            elif cmd[0] == 'withdraw' and len(cmd) > 1:
                client.withdraw(cmd[1])
            elif cmd[0] == 'transactions':
                client.get_transactions(
                    cmd[1] if len(cmd) > 1 else None,
                    cmd[2] if len(cmd) > 2 else None
                )
            elif cmd[0] == 'help':
                print_help()
            elif cmd[0] == 'exit':
                break
            else:
                print("无效命令，输入help查看帮助")
                
        except KeyboardInterrupt:
            print("\n使用'exit'命令退出程序")
        except Exception as e:
            print(f"错误: {str(e)}")

if __name__ == '__main__':
    # 创建自定义SSL上下文
    ssl_context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
    ssl_context.load_cert_chain(certfile='cli.crt', keyfile='cli.key')
    ssl_context.load_verify_locations(cafile='root.pem')
    ssl_context.verify_mode = ssl.CERT_REQUIRED
    
    # 应用SSL配置到requests
    requests.session().verify = 'root.pem'
    requests.session().cert = ('cli.crt', 'cli.key')
    
    client = CoinCenterClient()
    print("CoinCenter 客户端 (双向SSL认证已启用)")
    main()