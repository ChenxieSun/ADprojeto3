from flask import Flask, request, jsonify
from coincenter_data import *
import ssl
from kazoo.client import KazooClient

app = Flask(__name__)
zk = KazooClient(hosts='127.0.0.1:2181')
zk.start()
zk.ensure_path("/assets")

def problem(detail, status):
    return jsonify({
        "type": "https://example.com/problem",
        "title": "Erro",
        "status": status,
        "detail": detail
    }), status

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    is_manager = data.get('is_manager', 0)
    try:
        user_id = create_user(is_manager)
        return jsonify({"client_id": user_id})
    except Exception as e:
        return problem(f"Login failed: {str(e)}", 400)

@app.route('/asset', methods=['POST'])
def asset():
    data = request.get_json()
    symbol = data.get('symbol')
    name = data.get('name')
    price = data.get('price')
    supply = data.get('supply')
    if not all([symbol, name, price, supply]):
        return problem("Missing asset parameters", 400)
    if add_asset(symbol, name, price, supply):
        zk.set("/assets", symbol.encode())
        return jsonify({"status": "added"})
    else:
        return problem("Asset already exists or invalid", 400)

@app.route('/user', methods=['GET'])
def user():
    client_id = request.args.get('id')
    balance, assets = get_user_assets(client_id)
    if balance is None:
        return problem("User not found", 404)
    return jsonify({
        "balance": balance["balance"],
        "assets": [{"symbol": a["asset_symbol"], "quantity": a["quantity"]} for a in assets]
    })

# 其余接口类似调整，确保字段名称对应最新数据库结构
