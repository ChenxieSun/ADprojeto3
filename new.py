import sqlite3
from datetime import datetime

def get_db_connection():
    conn = sqlite3.connect('coincenter.db')
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def create_user(is_manager):
    conn = get_db_connection()
    cur = conn.cursor()
    # Clients表中没有name字段，只有client_id, is_manager, balance
    cur.execute("INSERT INTO Clients (is_manager, balance) VALUES (?, ?)", (is_manager, 0.0))
    conn.commit()
    user_id = cur.lastrowid
    conn.close()
    return user_id

def get_user_assets(client_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT balance FROM Clients WHERE client_id = ?", (client_id,))
    balance = cur.fetchone()
    cur.execute("SELECT asset_symbol, quantity FROM ClientAssets WHERE client_id = ?", (client_id,))
    assets = cur.fetchall()
    conn.close()
    return balance, assets

def add_asset(asset_symbol, asset_name, price, available_quantity):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO Assets (asset_symbol, asset_name, price, available_quantity) VALUES (?, ?, ?, ?)",
                    (asset_symbol, asset_name, price, available_quantity))
        conn.commit()
        return True
    except:
        return False
    finally:
        conn.close()

def deposit(client_id, amount):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE Clients SET balance = balance + ? WHERE client_id = ?", (amount, client_id))
    conn.commit()
    conn.close()

def withdraw(client_id, amount):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT balance FROM Clients WHERE client_id = ?", (client_id,))
    row = cur.fetchone()
    if row is None:
        conn.close()
        return False
    balance = row["balance"]
    if balance >= amount:
        cur.execute("UPDATE Clients SET balance = balance - ? WHERE client_id = ?", (amount, client_id))
        conn.commit()
        result = True
    else:
        result = False
    conn.close()
    return result

def buy_asset(client_id, asset_symbol, quantity):
    conn = get_db_connection()
    cur = conn.cursor()
    # 查询资产价格和库存
    cur.execute("SELECT price, available_quantity FROM Assets WHERE asset_symbol = ?", (asset_symbol,))
    asset = cur.fetchone()
    if not asset or asset["available_quantity"] < quantity:
        conn.close()
        return False
    total_price = asset["price"] * quantity
    # 查询余额
    cur.execute("SELECT balance FROM Clients WHERE client_id = ?", (client_id,))
    balance = cur.fetchone()["balance"]
    if balance < total_price:
        conn.close()
        return False
    # 扣除余额，减少库存
    cur.execute("UPDATE Clients SET balance = balance - ? WHERE client_id = ?", (total_price, client_id))
    cur.execute("UPDATE Assets SET available_quantity = available_quantity - ? WHERE asset_symbol = ?", (quantity, asset_symbol))
    # 更新客户资产（插入或更新）
    cur.execute("""
        INSERT INTO ClientAssets (client_id, asset_symbol, quantity) VALUES (?, ?, ?)
        ON CONFLICT(client_id, asset_symbol) DO UPDATE SET quantity = quantity + excluded.quantity
    """, (client_id, asset_symbol, quantity))
    # 记录交易
    cur.execute("INSERT INTO Transactions (client_id, asset_symbol, type, quantity, price, time) VALUES (?, ?, 'BUY', ?, ?, ?)",
                (client_id, asset_symbol, quantity, asset["price"], datetime.now().isoformat()))
    conn.commit()
    conn.close()
    return True

def sell_asset(client_id, asset_symbol, quantity):
    conn = get_db_connection()
    cur = conn.cursor()
    # 查询客户持有资产数量
    cur.execute("SELECT quantity FROM ClientAssets WHERE client_id = ? AND asset_symbol = ?", (client_id, asset_symbol))
    client_asset = cur.fetchone()
    if not client_asset or client_asset["quantity"] < quantity:
        conn.close()
        return False
    # 查询资产价格
    cur.execute("SELECT price FROM Assets WHERE asset_symbol = ?", (asset_symbol,))
    price = cur.fetchone()["price"]
    total_price = price * quantity
    # 扣减客户资产，增加库存，增加余额
    cur.execute("UPDATE ClientAssets SET quantity = quantity - ? WHERE client_id = ? AND asset_symbol = ?", (quantity, client_id, asset_symbol))
    cur.execute("UPDATE Assets SET available_quantity = available_quantity + ? WHERE asset_symbol = ?", (quantity, asset_symbol))
    cur.execute("UPDATE Clients SET balance = balance + ? WHERE client_id = ?", (total_price, client_id))
    # 记录交易
    cur.execute("INSERT INTO Transactions (client_id, asset_symbol, type, quantity, price, time) VALUES (?, ?, 'SELL', ?, ?, ?)",
                (client_id, asset_symbol, quantity, price, datetime.now().isoformat()))
    conn.commit()
    conn.close()
    return True

def get_transactions(start, end):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM Transactions WHERE time BETWEEN ? AND ?", (start, end))
    txs = cur.fetchall()
    conn.close()
    return txs
