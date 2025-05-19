import requests
import json
import requests
from datetime import datetime

BASE_URL = 'https://localhost:5000'
CERT = ('cli.crt', 'cli.key')
CA = 'root.pem'

session = requests.Session()
current_user_id = None
def safe_print_response(r):
    print("Status code:", r.status_code)
    try:
        print("Response JSON:", r.json())
    except Exception:
        print("Response text:", r.text)
print('Please select a command: LOGIN, ASSET, USER, DEPOSIT, WITHDRAW, SELL, TRANSACTIONS]')
while True:
    cmd = input("Command: ").strip().upper()

    if cmd == 'LOGIN':
        inp=input("Enter client ID (or press ENTER to creat new):").strip()
        if inp:
            client_id=int(inp)
            r=session.post(f"{BASE_URL}/login", json={"client_id": client_id}, cert=CERT, verify=CA)
        else:
            r = session.post(f"{BASE_URL}/login", json={}, cert=CERT, verify=CA)
        
        if r.status_code==200:
            current_user_id = r.json()["client_id"]
            print(f"Login successful\nLogged in as user ID:{current_user_id}")
        safe_print_response(r)

    elif cmd == 'ASSET':
        symbol = input("Symbol: ")
        name = input("Name: ")
        price = float(input("Price: "))
        supply = int(input("Supply: "))
        r = session.post(f"{BASE_URL}/asset", json={"symbol": symbol, "name": name, "price": price, "supply": supply}, cert=CERT, verify=CA)
        safe_print_response(r)

    elif cmd == 'USER':
        if current_user_id== None:
            print("Please login first.")
            continue
        else:
            r = session.get(f"{BASE_URL}/user", params={"client_id": current_user_id}, cert=CERT, verify=CA)
            if r.status_code == 200:
                data = r.json()
                print(f"ID: {data['client_id']}")
                print(f"Balance: {data['balance']}")
                print("Assets:")
                for asset in data['assets']:
                    print(f"  Symbol: {asset['symbol']}, Quantity: {asset['quantity']}")
            else:
                safe_print_response(r)

    elif cmd == 'DEPOSIT':
        if current_user_id== None:
            print("Please login first.")
            continue
        else:
            amount = float(input("Amount: "))
            r = session.post(f"{BASE_URL}/deposit", json={"client_id": current_user_id, "amount": amount}, cert=CERT, verify=CA)
            safe_print_response(r)

    elif cmd == 'WITHDRAW':
        if current_user_id== None:
            print("Please login first.")
            continue
        else:
            symbol = input("Symbol: ")
            quantity = float(input("Quantity: "))
            r = session.post(f"{BASE_URL}/buy", json={"client_id": current_user_id, "asset_symbol": symbol, "quantity": quantity}, cert=CERT, verify=CA)
            safe_print_response(r)
    
    elif cmd == 'BUY':
        if current_user_id== None:
            print("Please login first.")
            continue
        else:
            symbol = input("Symbol: ")
            quantity = float(input("Quantity: "))
            r = session.post(f"{BASE_URL}/buy", json={"client_id": current_user_id, "asset_symbol": symbol, "quantity": quantity}, cert=CERT, verify=CA)
            safe_print_response(r)

    elif cmd == 'SELL':
        if current_user_id== None:
            print("Please login first.")
            continue
        else:
            symbol = input("Symbol: ")
            quantity = float(input("Quantity: "))
            r = session.post(f"{BASE_URL}/sell", json={"client_id": current_user_id, "asset_symbol": symbol, "quantity": quantity}, cert=CERT, verify=CA)
            safe_print_response(r)

    elif cmd == 'TRANSACTIONS':
        if current_user_id== None:
            print("Please login first.")
            continue
        else:
            r = session.get(f"{BASE_URL}/transactions",params={"client_id": current_user_id},cert=CERT,verify=CA)
            if r.status_code == 403:
                print("Access denied: This user is not a manager.")
                continue

            if r.status_code == 404:
                print("User not found.")
                continue
            if r.status_code == 200:
                start = input("Start (YYYY-MM-DD): ")
                end = input("End (YYYY-MM-DD): ")
                r = session.get(f"{BASE_URL}/transactions", params={"client_id": current_user_id, "start": start, "end": end}, cert=CERT, verify=CA)
                data = r.json()
                print("Transactions:")
                for d in data['datas']:
                    print(f"    Nº: {d['num']},     Time: {datetime.fromisoformat(d['time']).strftime("%Y-%m-%d %H:%M")},  User: {d['user']},  Type: {d['type']},  Symbol: {d['symbol']},  Quantity: {d['quantity']},  Price: {d['price']}")
                    
            else:    
                safe_print_response(r)

    else:
        print("Unknown command. Please try again.")