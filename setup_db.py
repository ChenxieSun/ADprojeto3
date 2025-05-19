import sqlite3
import sys
from pathlib import Path
import os

DATABASE = 'coincenter.db'

def init_db():
    """Inicializar a estrutura da tabela da base de dados e os dados iniciais"""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()

        schema_file = Path(__file__).parent / 'schema.sql'
        if not schema_file.exists():
            raise FileNotFoundError(f"schema.sql file not found: {schema_file}")
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
    cursor.execute("SELECT COUNT(*) FROM Clients WHERE is_manager = 1")
    if cursor.fetchone()[0] == 0:
        for i in range(5):
            if i == 0:
                cursor.execute("INSERT INTO clients (client_id, is_manager, balance) VALUES (0, 1, 0.0)")
                print("Administrator account created (client_id=0)")
            else:
                cursor.execute("INSERT INTO clients (client_id, is_manager, balance) VALUES (?, 0, 0.0)", (i,))
                print(f"User account created (client_id={i})")

    # Add initial cryptocurrencies
    initial_assets = [
        ('BTC', 'Bitcoin', 50000.0, 10),
        ('ETH', 'Ethereum', 3000.0, 50),
        ('XRP', 'Ripple', 2.11, 1000),
        ('SOL', 'Solana', 162.0, 200),
        ('BNB', 'BinanceCoin', 400.0, 150)
    ]

    for asset in initial_assets:
        try:
            cursor.execute("""INSERT INTO Assets (asset_symbol, asset_name, price, available_quantity) VALUES (?, ?, ?, ?)""", asset)
        except sqlite3.IntegrityError:
            continue

    print(f"{len(initial_assets)} initial cryptocurrencies added")

def reset_db():
    """Repor base de dados (apagar todos os dados)"""
    confirm = input("This will delete all data! Are you sure?(y/n): ")
    if confirm.lower() != 'y':
        return

    try:
        # Ensure the correct path
        db_path = Path(DATABASE)
        if db_path.exists():
            db_path.unlink()  # Equivalent to os.remove, but works with Path objects
            print(f"Database {DATABASE} deleted successfully.")
        else:
            print(f"Database {DATABASE} not found.")
        
        
    except Exception as e:
        print(f"Reset failed: {e}", file=sys.stderr)
    # Reinitialize the database after deletion
    init_db()

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
