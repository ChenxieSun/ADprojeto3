import sqlite3
from datetime import datetime

def get_db_connection():
    conn = sqlite3.connect('coincenter.db')
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def create_user(client_id,is_manager):
    conn = get_db_connection()
    cur = conn.cursor()
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
    cur.execute("SELECT price, available_quantity FROM Assets WHERE asset_symbol = ?", (asset_symbol,))
    asset = cur.fetchone()
    if not asset or asset["available_quantity"] < quantity:
        conn.close()
        return False
    total_price = asset["price"] * quantity
    cur.execute("SELECT balance FROM Clients WHERE client_id = ?", (client_id,))
    balance = cur.fetchone()["balance"]
    if balance < total_price:
        conn.close()
        return False
    cur.execute("UPDATE Clients SET balance = balance - ? WHERE client_id = ?", (total_price, client_id))
    cur.execute("UPDATE Assets SET available_quantity = available_quantity - ? WHERE asset_symbol = ?", (quantity, asset_symbol))
    cur.execute(""" INSERT INTO ClientAssets (client_id, asset_symbol, quantity) VALUES (?, ?, ?) 
                ON CONFLICT(client_id, asset_symbol) DO UPDATE SET quantity = quantity + excluded.quantity
                """, (client_id, asset_symbol, quantity))    
    cur.execute("INSERT INTO Transactions (client_id, asset_symbol, type, quantity, price, time) VALUES (?, ?, 'BUY', ?, ?, ?)",
                (client_id, asset_symbol, quantity, total_price, datetime.now().isoformat()))
    conn.commit()
    conn.close()
    return True

def sell_asset(client_id, asset_symbol, quantity):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT quantity FROM ClientAssets WHERE client_id = ? AND asset_symbol = ?", (client_id, asset_symbol))
    user_asset = cur.fetchone()
    if not user_asset or user_asset["quantity"] < quantity:
        conn.close()
        return False
    cur.execute("SELECT price FROM Assets WHERE asset_symbol = ?", (asset_symbol,))
    price = cur.fetchone()["price"]
    total_price = price * quantity
    cur.execute("UPDATE ClientAssets SET quantity = quantity - ? WHERE client_id = ? AND asset_symbol = ?", (quantity, client_id, asset_symbol))
    cur.execute("UPDATE Assets SET available_quantity = available_quantity + ? WHERE asset_symbol = ?", (quantity, asset_symbol))
    cur.execute("UPDATE Clients SET balance = balance + ? WHERE client_id = ?", (total_price, client_id))
    cur.execute("INSERT INTO Transactions (client_id, asset_symbol, type, quantity, price, time) VALUES (?, ?, 'SELL', ?, ?, ?)",
                (client_id, asset_symbol, quantity, total_price, datetime.now().isoformat()))
    conn.commit()
    conn.close()
    return True

def get_transactions(start, end):
    if len(end) == 10:  # YYYY-MM-DD
        end += "T23:59:59"
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM Transactions WHERE time BETWEEN ? AND ?", (start, end))
    transactions = cur.fetchall()
    conn.close()
    return transactions