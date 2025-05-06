from flask import Flask, request, jsonify
import sqlite3
import ssl
from kazoo.client import KazooClient

app = Flask(__name__)
DATABASE = 'coincenter.db'
ZK_HOSTS = '127.0.0.1:2181'

# ZooKeeper初始化
zk = KazooClient(hosts=ZK_HOSTS)
zk.start()

# 数据库连接
def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# 初始化数据库
def init_db():
    with get_db() as conn:
        with open('schema.sql', 'r') as f:
            conn.executescript(f.read())
        # 初始化管理员账户
        conn.execute("INSERT INTO clients (is_manager, balance) VALUES (1, 0)")

# API路由
@app.route('/asset', methods=['GET', 'POST'])
def handle_asset():
    if request.method == 'POST':
        # 添加新资产 (仅管理员)
        data = request.json
        try:
            with get_db() as conn:
                conn.execute("INSERT INTO Assets VALUES (?, ?, ?, ?)", 
                           (data['symbol'], data['asset_name'], data['price'], data['quantity']))
                # ZooKeeper通知
                zk.ensure_path("/Assets")
                zk.create(f"/Assets/{data['symbol']}", b"new asset", ephemeral=True)
            return jsonify({"status": "success"}), 201
        except Exception as e:
            return jsonify({"error": str(e)}), 400
    else:
        # 获取资产信息
        symbol = request.args.get('symbol')
        with get_db() as conn:
            asset = conn.execute("SELECT * FROM Assets WHERE asset_symbol=?", (symbol,)).fetchone()
            return jsonify(dict(asset)) if asset else ('', 404)

# 其他路由实现类似...
# /login, /user, /buy, /sell, /deposit, /withdraw, /transactions

if __name__ == '__main__':
    # SSL配置
    context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_3)
    context.load_cert_chain('server.crt', 'server.key')
    
    # 启动服务
    app.run(host='0.0.0.0', port=5000, ssl_context=context, debug=True)