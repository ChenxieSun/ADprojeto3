import sqlite3
import ssl
from kazoo.client import KazooClient
from typing import Dict, Optional

class CoinCenterData:
    def __init__(self, db_path='coincenter.db'):
        self.db_path = db_path
        self.zk = KazooClient(hosts='127.0.0.1:2181')
        self.zk.start()
        
    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def add_asset(self, asset: Dict) -> bool:
        with self._get_conn() as conn:
            try:
                conn.execute("""
                INSERT INTO Assets VALUES (?, ?, ?, ?)
                """, (asset['symbol'], asset['name'], asset['price'], asset['quantity']))
                
                # Notify ZooKeeper
                self.zk.create(
                    f"/assets/{asset['symbol']}", 
                    b"new_asset", 
                    ephemeral=True
                )
                return True
            except sqlite3.IntegrityError:
                return False

    def get_ssl_context(self, client: bool = False) -> ssl.SSLContext:
        """Create SSL context per PL08 guidelines"""
        context = ssl.SSLContext(
            ssl.PROTOCOL_TLS_CLIENT if client else ssl.PROTOCOL_TLS_SERVER
        )
        context.verify_mode = ssl.CERT_REQUIRED
        context.load_verify_locations('certs/root.pem')
        
        if client:
            context.load_cert_chain(
                'certs/cli.crt', 
                'certs/cli.key'
            )
        else:
            context.load_cert_chain(
                'certs/serv.crt', 
                'certs/serv.key'
            )
        return context