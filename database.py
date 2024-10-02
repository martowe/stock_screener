import mysql.connector
from tkinter import messagebox


class Database:
    def __init__(self):
        self.db_config = {
            "host": "localhost",
            "user": "root",
            "password": "123123",
            "database": "stocks"
        }
        self.connection = self.connect_to_db()
        self.create_watchlist_table()

    def connect_to_db(self):
        try:
            connection = mysql.connector.connect(**self.db_config)
            return connection
        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", f"Failed to connect to database: {err}")
            return None

    def create_watchlist_table(self):
        if self.connection:
            cursor = self.connection.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS watchlist (
                    symbol VARCHAR(255) PRIMARY KEY,
                    price DECIMAL(10, 2),
                    pe_ratio DECIMAL(10, 2),
                    market_cap BIGINT,
                    full_name VARCHAR(255),
                    industry VARCHAR(255)
                )
            """)
            self.connection.commit()
            cursor.close()

    def add_to_watchlist(self, symbol, price, pe_ratio, market_cap, full_name, industry):
        if self.connection:
            cursor = self.connection.cursor()
            query = """
                INSERT INTO watchlist (symbol, price, pe_ratio, market_cap, full_name, industry)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            values = (symbol, price, pe_ratio, market_cap, full_name, industry)
            cursor.execute(query, values)
            self.connection.commit()
            cursor.close()

    def remove_from_watchlist(self, symbol):
        if self.connection:
            cursor = self.connection.cursor()
            query = "DELETE FROM watchlist WHERE symbol = %s"
            cursor.execute(query, (symbol,))
            self.connection.commit()
            cursor.close()

    def get_watchlist(self):
        if self.connection:
            cursor = self.connection.cursor()
            cursor.execute("SELECT * FROM watchlist")
            rows = cursor.fetchall()
            cursor.close()
            return rows
        return []

    def close(self):
        if self.connection:
            self.connection.close()