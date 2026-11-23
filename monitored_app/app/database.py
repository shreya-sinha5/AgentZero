"""Database & repository layer for demo e-commerce app."""
import sqlite3
import time
from typing import Dict, List, Optional, Any

# In-memory / file-based SQLite database
DB_PATH = ":memory:"

def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

class Database:
    def __init__(self):
        self.conn = get_connection()
        self.active_connections = 1
        self.max_connections = 10
        self.init_schema()

    def init_schema(self):
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    category TEXT NOT NULL,
                    price REAL NOT NULL,
                    stock INTEGER NOT NULL
                )
            """)
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    total_amount REAL NOT NULL,
                    status TEXT NOT NULL,
                    created_at REAL NOT NULL
                )
            """)
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS cart_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    product_id INTEGER NOT NULL,
                    quantity INTEGER NOT NULL
                )
            """)
            # Seed products if empty
            cursor = self.conn.execute("SELECT COUNT(*) FROM products")
            if cursor.fetchone()[0] == 0:
                self.conn.executemany("""
                    INSERT INTO products (name, category, price, stock)
                    VALUES (?, ?, ?, ?)
                """, [
                    ("Production Server Rack", "Hardware", 1299.99, 15),
                    ("Load Balancer Pro", "Network", 499.00, 30),
                    ("NVMe Storage Array", "Storage", 899.50, 20),
                    ("Managed Switch 48-port", "Network", 349.99, 45),
                    ("Monitoring Sensor Hub", "Hardware", 120.00, 100),
                ])

    def list_products(self) -> List[Dict[str, Any]]:
        cursor = self.conn.execute("SELECT * FROM products")
        return [dict(row) for row in cursor.fetchall()]

    def get_product(self, product_id: int) -> Optional[Dict[str, Any]]:
        cursor = self.conn.execute("SELECT * FROM products WHERE id = ?", (product_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def add_to_cart(self, user_id: str, product_id: int, quantity: int) -> Dict[str, Any]:
        with self.conn:
            cursor = self.conn.execute("""
                INSERT INTO cart_items (user_id, product_id, quantity)
                VALUES (?, ?, ?)
            """, (user_id, product_id, quantity))
            return {"id": cursor.lastrowid, "user_id": user_id, "product_id": product_id, "quantity": quantity}

    def get_cart(self, user_id: str) -> List[Dict[str, Any]]:
        cursor = self.conn.execute("""
            SELECT c.id, c.product_id, p.name, p.price, c.quantity, (p.price * c.quantity) as subtotal
            FROM cart_items c
            JOIN products p ON c.product_id = p.id
            WHERE c.user_id = ?
        """, (user_id,))
        return [dict(row) for row in cursor.fetchall()]

    def create_order(self, user_id: str, amount: float) -> Dict[str, Any]:
        with self.conn:
            now = time.time()
            cursor = self.conn.execute("""
                INSERT INTO orders (user_id, total_amount, status, created_at)
                VALUES (?, ?, 'COMPLETED', ?)
            """, (user_id, amount, now))
            order_id = cursor.lastrowid
            self.conn.execute("DELETE FROM cart_items WHERE user_id = ?", (user_id,))
            return {"order_id": order_id, "user_id": user_id, "total_amount": amount, "status": "COMPLETED", "created_at": now}

db = Database()
