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
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    input_id = data.get('client_id')

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        if input_id is not None:
            cur.execute("SELECT client_id FROM Clients WHERE client_id = ?", (input_id,))
            row = cur.fetchone()
            if row:
                # client exists
                conn.close()
                return jsonify({"client_id": input_id})
            else:
                # client not exists
                cur.execute("INSERT INTO Clients(client_id, is_manager, balance) VALUES (?, 0, 0.0)", (input_id,))
                conn.commit()
                conn.close()
                return jsonify({"client_id": input_id})
        else:
            # client_id is None, insert new and return generated id
            cur.execute("INSERT INTO Clients(is_manager, balance) VALUES (0, 0.0)")
            conn.commit()
            new_id = cur.lastrowid
            conn.close()
            return jsonify({"client_id": new_id})
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
    client_id = request.args.get('client_id')
    balance, assets = get_user_assets(client_id)
    if balance is None:
        return problem("User not found", 404)
    return jsonify({"client_id":client_id,
                    "balance": balance["balance"],
                    "assets": [{"symbol": a["asset_symbol"], "quantity": a["quantity"]} for a in assets]})

@app.route('/deposit', methods=['POST'])
def deposit_route():
    data = request.get_json()
    client_id = data.get('client_id')
    amount = data.get('amount')
    deposit(client_id, amount)
    return jsonify({"status": "deposited"})

@app.route('/withdraw', methods=['POST'])
def withdraw_route():
    data = request.get_json()
    client_id = data.get('client_id')
    amount = data.get('amount')
    if withdraw(client_id, amassetsount):[{"symbol": a["asset_symbol"], 
                    "quantity": a["quantity"]} for a in assets]
    return problem("Buy failed", 400)

@app.route('/buy', methods=['POST'])
def buy_route():
    data = request.get_json()
    if buy_asset(data['client_id'], data['asset_symbol'], data['quantity']):
        return jsonify({"status": "bought"})
    return problem("Buy failed", 400)

@app.route('/sell', methods=['POST'])
def sell_route():
    data = request.get_json()
    if sell_asset(data['client_id'], data['asset_symbol'], data['quantity']):
        return jsonify({"status": "sold"})
    return problem("Sell failed", 400)

@app.route('/transactions', methods=['GET'])
def transactions():
    client_id = request.args.get('client_id')

    if not client_id:
        return problem("Missing client_id", 400)

    # 先检查是否为经理
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT is_manager FROM Clients WHERE client_id = ?", (client_id,))
    row = cur.fetchone()
    conn.close()

    if not row:
        return problem("User not found", 404)

    if row["is_manager"] != 1:
        return problem("Access denied: Only managers can view transactions", 403)
    
    
    start = request.args.get('start')
    end = request.args.get('end')
    if not start or not end:
        return jsonify({"status": "manager verified"}), 200

    if len(end) == 10:
        end += "T23:59:59"

    txs = get_transactions(start, end)
    return jsonify({"datas": [{"num":row["id"],"time":row["time"],"user":row["client_id"],"type":row["type"],"symbol":row["asset_symbol"],"quantity":row["quantity"],"price":row["price"]} for row in txs]})
    #"assets": [{"symbol": a["asset_symbol"], "quantity": a["quantity"]} for a in assets]}

    


if __name__ == '__main__':
    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    context.load_cert_chain(certfile='serv.crt', keyfile='serv.key')
    context.load_verify_locations(cafile='root.pem')
    context.verify_mode = ssl.CERT_REQUIRED

    app.run(host='localhost', ssl_context=context, debug=True)
