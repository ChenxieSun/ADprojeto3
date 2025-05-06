#!/usr/bin/env python3
import sqlite3
import sys
from pathlib import Path

DATABASE = 'coincenter.db'

def init_db():
    """Inicializar a estrutura da tabela da base de dados e os dados iniciais"""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()

        schema_file = Path(__file__).parent / 'schema.sql'
        if not schema_file.exists():
            raise FileNotFoundError(f"schema.sql文件未找到: {schema_file}")
        with open(schema_file, 'r', encoding='utf-8') as f:
            cursor.executescript(f.read())
        
        insert_initial_data(cursor)
        conn.commit()
        print("Database initialization successful!")

    except sqlite3.Error as e:
        print(f"Database Error: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        if conn:
            conn.close()
def insert_initial_data(cursor):

    cursor.execute("SELECT COUNT(*) FROM clients WHERE is_manager = 1")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO clients (is_manager, balance) VALUES (1, 0.0)")
        print("已创建管理员账户 (client_id=1)")

    # 初始加密货币数据
    initial_assets = [
        ('BTC', 'Bitcoin', 50000.0, 100),
        ('ETH', 'Ethereum', 3000.0, 500),
        ('ADA', 'Cardano', 1.5, 10000)
    ]
    
    for asset in initial_assets:
        try:
            cursor.execute(
                """INSERT INTO Assets 
                (asset_symbol, asset_name, price, available_quantity) 
                VALUES (?, ?, ?, ?)""",
                asset
            )
        except sqlite3.IntegrityError:
            continue  # 如果资产已存在则跳过

    print(f"已添加 {len(initial_assets)} 种初始加密货币")

def reset_db():
    """Repor base de dados (apagar todos os dados)"""
    confirm = input("This will delete all data! Are you sure?(y/n): ")
    if confirm.lower() != 'y':
        return
    
    try:
        import os
        if os.path.exists(DATABASE):
            os.remove(DATABASE)
            print("Database deleted")
        init_db()
    except Exception as e:
        print(f"Reset failed: {e}", file=sys.stderr)

if __name__ == '__main__':
    print("CoinCenter Database Configuration Tool")
    print("1. Initialize the database")
    print("2. Reset Database")
    print("3. Exit")
    
    choice = input("Please select an operation: ").strip()
    
    if choice == '1':
        init_db()
    elif choice == '2':
        reset_db()
    else:
        print("Exit")