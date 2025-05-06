import requests
import json
from kazoo.client import KazooClient

BASE_URL = "https://localhost:5000"
ZK_HOSTS = '127.0.0.1:2181'

class CoinCenterClient:
    def __init__(self):
        self.session = requests.Session()
        self.session.verify = 'ca.crt'  # CA证书
        self.current_user = None
        
        # ZooKeeper监听
        self.zk = KazooClient(hosts=ZK_HOSTS)
        self.zk.start()
        self.watch_assets()
    
    def watch_assets(self):
        @self.zk.ChildrenWatch("/Assets")
        def asset_watch(children):
            print("\n[通知] 新资产上线:", children)
    
    def login(self, user_id=None):
        res = self.session.post(f"{BASE_URL}/login", json={"client_id": user_id})
        if res.ok:
            self.current_user = res.json()
            print("登录成功! 用户ID:", self.current_user['client_id'])
        else:
            print("错误:", res.json().get('error'))
    
    def get_asset(self, symbol):
        res = self.session.get(f"{BASE_URL}/asset?symbol={symbol}")
        print(json.dumps(res.json(), indent=2) if res.ok else print("错误:", res.status_code))
    
    # 其他方法实现类似...
    # asset_set, user_info, buy, sell, deposit, withdraw, transactions

def main():
    client = CoinCenterClient()
    print("CoinCenter 客户端 (输入help查看命令)")
    
    while True:
        cmd = input("> ").strip().split()
        if not cmd:
            continue
            
        if cmd[0] == 'login':
            client.login(cmd[1] if len(cmd) > 1 else None)
        elif cmd[0] == 'asset':
            client.get_asset(cmd[1])
        # 其他命令处理...
        elif cmd[0] == 'exit':
            break

if __name__ == '__main__':
    main()