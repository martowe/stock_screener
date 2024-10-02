import tkinter as tk
from tkinter import ttk
import threading


import database
import stock_data
import ui

BACKGROUND_COLOR = "#34495e"
FOREGROUND_COLOR = "#ecf0f1"
ACCENT_COLOR = "#1abc9c"
FONT = ("Helvetica", 12)
BUTTON_FONT = ("Helvetica", 10)
NOTIFICATION_INTERVAL = 60

class StockScreenerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Stock Screener')
        self.configure(bg=BACKGROUND_COLOR)
        self.geometry('1000x800')
        self.resizable(True, True)

        self.style = ttk.Style(self)
        self.style.theme_use('clam')
        self.style.configure('TLabel', background=BACKGROUND_COLOR, foreground=FOREGROUND_COLOR, font=FONT)
        self.style.configure('TButton', background=ACCENT_COLOR, foreground=FOREGROUND_COLOR, font=BUTTON_FONT, padding=6)
        self.style.configure('TEntry', font=FONT, padding=6)
        self.style.configure('TFrame', background=BACKGROUND_COLOR)

        self.db = database.Database()
        self.stock_data_manager = stock_data.StockDataManager()
        self.ui = ui.UI(self, self.stock_data_manager, self.db)
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.load_watchlist_data()
        self.check_target_price_event = threading.Event()
        self.after(60000, self.periodic_target_check)

    def load_watchlist_data(self):
        self.ui.load_watchlist_data()

    def periodic_target_check(self):
        if not self.check_target_price_event.is_set():
            try:
                self.ui.check_target_price()
            except Exception as e:
                print(f"Error in check_target_price: {e}")
            self.after(60000, self.periodic_target_check)

    def on_close(self):
        self.check_target_price_event.set()
        self.ui.on_close()
        self.destroy()



if __name__ == '__main__':
    app = StockScreenerApp()
    app.mainloop()