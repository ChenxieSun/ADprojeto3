import requests

BASE_URL = 'https://localhost:5000'
CERT = ('certs/cli.crt', 'certs/cli.key')
CA = 'certs/root.pem'

session = requests.Session()

def safe_print_response(r):
    print("Status code:", r.status_code)
    try:
        print("Response JSON:", r.json())
    except Exception:
        print("Response text:", r.text)

while True:
    cmd = input("Command: ").strip().upper()

    if cmd == 'LOGIN':
        is_manager = int(input("Is Manager (0/1): "))
        r = session.post(f"{BASE_URL}/login", json={"is_manager": is_manager}, cert=CERT, verify=CA)
        safe_print_response(r)

    elif cmd == 'ASSET':
        symbol = input("Symbol: ")
        name = input("Name: ")
        price = float(input("Price: "))
        supply = int(input("Supply: "))
        r = session.post(f"{BASE_URL}/asset", json={"symbol": symbol, "name": name, "price": price, "supply": supply}, cert=CERT, verify=CA)
        safe_print_response(r)

    elif cmd == 'USER':
        client_id = input("Client ID: ")
        r = session.get(f"{BASE_URL}/user", params={"id": client_id}, cert=CERT, verify=CA)
        if r.status_code == 200:
            data = r.json()
            print(f"Balance: {data['balance']}")
            print("Assets:")
            for asset in data['assets']:
                print(f"  Symbol: {asset['symbol']}, Quantity: {asset['quantity']}")
        else:
            safe_print_response(r)

    # 其余命令类似，只是参数名称和字段名称根据新接口调整
    # 例如 BUY/SELL 里的 client_id 和 symbol 等字段名称不变

    elif cmd == 'DEPOSIT':
        client_id = input("Client ID: ")
        amount = float(input("Amount: "))
        r = session.post(f"{BASE_URL}/deposit", json={"client_id": client_id, "amount": amount}, cert=CERT, verify=CA)
        safe_print_response(r)

    elif cmd == 'WITHDRAW':
        client_id = input("Client ID: ")
        amount = float(input("Amount: "))
        r = session.post(f"{BASE_URL}/withdraw", json={"client_id": client_id, "amount": amount}, cert=CERT, verify=CA)
        safe_print_response(r)

    elif cmd == 'BUY':
        client_id = input("Client ID: ")
        symbol = input("Symbol: ")
        quantity = int(input("Quantity: "))
        r = session.post(f"{BASE_URL}/buy", json={"client_id": client_id, "asset_symbol": symbol, "quantity": quantity}, cert=CERT, verify=CA)
        safe_print_response(r)

    elif cmd == 'SELL':
        client_id = input("Client ID: ")
        symbol = input("Symbol: ")
        quantity = int(input("Quantity: "))
        r = session.post(f"{BASE_URL}/sell", json={"client_id": client_id, "asset_symbol": symbol, "quantity": quantity}, cert=CERT, verify=CA)
        safe_print_response(r)

    elif cmd == 'TRANSACTIONS':
        start = input("Start (YYYY-MM-DD): ")
        end = input("End (YYYY-MM-DD): ")
        r = session.get(f"{BASE_URL}/transactions", params={"start": start, "end": end}, cert=CERT, verify=CA)
        safe_print_response(r)

    else:
        print("Unknown command. Please try again.")
