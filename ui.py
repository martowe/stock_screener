import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
import yfinance as yf
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.dates as mdates
from queue import Queue
import threading
import time

class UI:
    def __init__(self, master, stock_data_manager, db):
        self.master = master
        self.stock_data_manager = stock_data_manager
        self.db = db
        self.data_queue = Queue()
        self.update_thread = threading.Thread(target=self.process_data_queue, daemon=True)
        self.update_thread.start()
        self.target_price = None
        self.target_symbol = None
        self.sort_direction = {col: False for col in ["Symbol", "Price", "P/E Ratio", "Market Cap", "Full Name", "Industry"]}
        self.create_widgets()

    def create_widgets(self):
        main_frame = ttk.Frame(self.master, padding="20", style='TFrame')
        main_frame.pack(fill=tk.BOTH, expand=True)

        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        self.chart_frame = ttk.Frame(self.notebook, style='TFrame')
        self.notebook.add(self.chart_frame, text='Chart')
        self.details_frame = ttk.Frame(self.notebook, style='TFrame')
        self.notebook.add(self.details_frame, text='Details')
        self.watchlist_frame = ttk.Frame(self.notebook, style='TFrame')
        self.notebook.add(self.watchlist_frame, text='My Stocks')

        input_frame = ttk.Frame(self.chart_frame)
        input_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(input_frame, text='Stock Symbol:').pack(side=tk.LEFT, padx=(0, 5))
        self.symbol_entry = ttk.Entry(input_frame, width=20)
        self.symbol_entry.pack(side=tk.LEFT, padx=(0, 10))
        self.search_button = ttk.Button(input_frame, text='Search', command=self.on_search)
        self.search_button.pack(side=tk.LEFT)
        ttk.Label(input_frame, text='Target Price:').pack(side=tk.LEFT, padx=(20, 5))
        self.target_entry = ttk.Entry(input_frame, width=10)
        self.target_entry.pack(side=tk.LEFT, padx=(0, 10))
        self.set_target_button = ttk.Button(input_frame, text='Set Target', command=self.set_target_price)
        self.set_target_button.pack(side=tk.LEFT)

        self.current_price_label = ttk.Label(self.chart_frame, text='Current Price: N/A', font=("Helvetica", 16))
        self.current_price_label.pack(pady=(0, 10), anchor=tk.W)

        self.fig, self.ax = plt.subplots(figsize=(10, 5))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.chart_frame)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(fill=tk.BOTH, expand=True)
        self.period_buttons_frame = ttk.Frame(self.chart_frame)
        self.period_buttons_frame.pack(fill=tk.X, pady=(10, 20))
        self.period_var = tk.StringVar(value='1d')
        self.create_period_buttons()
        self.status_label = ttk.Label(self.chart_frame, text='Ready', anchor=tk.W)
        self.status_label.pack(fill=tk.X, pady=(5, 10))
        self.loading_spinner = ttk.Progressbar(self.chart_frame, orient='horizontal', mode='indeterminate', style='TProgressbar')
        self.loading_spinner.pack(fill=tk.X, pady=(5, 10))

        self.details_tree = ttk.Treeview(self.details_frame, columns=("Attribute", "Value"), show='headings')
        self.details_tree.heading("Attribute", text="Attribute")
        self.details_tree.heading("Value", text="Value")
        self.details_tree.pack(fill=tk.BOTH, expand=True)

        watchlist_control_frame = ttk.Frame(self.watchlist_frame)
        watchlist_control_frame.pack(fill=tk.X, pady=(0, 10))
        self.watchlist_symbol_entry = ttk.Entry(watchlist_control_frame, width=20)
        self.watchlist_symbol_entry.pack(side=tk.LEFT, padx=(0, 10))
        self.add_to_watchlist_button = ttk.Button(watchlist_control_frame, text='Add to Watchlist', command=self.add_to_watchlist)
        self.add_to_watchlist_button.pack(side=tk.LEFT)
        self.remove_from_watchlist_button = ttk.Button(watchlist_control_frame, text='Remove from Watchlist', command=self.remove_from_watchlist)
        self.remove_from_watchlist_button.pack(side=tk.LEFT, padx=(10, 0))

        self.watchlist_tree = ttk.Treeview(self.watchlist_frame, columns=("Symbol", "Price", "P/E Ratio", "Market Cap", "Full Name", "Industry"), show='headings')
        self.watchlist_tree.heading("Symbol", text="Symbol", command=lambda: self.sort_watchlist("Symbol"))
        self.watchlist_tree.heading("Price", text="Price", command=lambda: self.sort_watchlist("Price", numeric=True))
        self.watchlist_tree.heading("P/E Ratio", text="P/E Ratio", command=lambda: self.sort_watchlist("P/E Ratio", numeric=True))
        self.watchlist_tree.heading("Market Cap", text="Market Cap", command=lambda: self.sort_watchlist("Market Cap", numeric=True))
        self.watchlist_tree.heading("Full Name", text="Full Name", command=lambda: self.sort_watchlist("Full Name"))
        self.watchlist_tree.heading("Industry", text="Industry", command=lambda: self.sort_watchlist("Industry"))
        self.watchlist_tree.pack(fill=tk.BOTH, expand=True)
        self.watchlist_tree.bind("<Double-1>", self.on_watchlist_item_double_click)

    def create_period_buttons(self):
        for period, label in {'1d': '1 Day', '5d': '5 Days', '1mo': '1 Month', '3mo': '3 Months', '6mo': '6 Months', '1y': '1 Year', 'ytd': 'Year To Date', 'max': 'Max'}.items():
            button = ttk.Button(self.period_buttons_frame, text=label, command=lambda p=period: self.select_period(p), width=8)
            button.pack(side=tk.LEFT, padx=5)

    def select_period(self, period):
        self.period_var.set(period)
        self.on_search()

    def fetch_and_enqueue_data(self, symbol, period):
        try:
            df = self.stock_data_manager.fetch_stock_data(symbol, period)
            self.data_queue.put((symbol, period, df))
        except ValueError as e:
            self.status_label.config(text=f"Error: {e}")
            self.loading_spinner.stop()

    def process_data_queue(self):
        while True:
            data = self.data_queue.get()
            if data is None:
                break
            symbol, period, df = data
            self.master.after(0, self.update_plot, df, symbol, period)
            self.master.after(0, self.update_details_tab, symbol)
            current_price = df['Close'].iloc[-1]
            self.master.after(0, self.update_current_price, current_price)
            self.master.after(0, self.status_label.config, {"text": "Ready"})
            self.master.after(0, self.loading_spinner.stop)


    def update_plot(self, df, symbol, period):
        self.ax.clear()
        self.ax.plot(df['Date'], df['Close'], label=f'{symbol} ({period})')
        self.ax.set_title(f'{symbol} Stock Price ({period})')
        self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        self.ax.xaxis.set_tick_params(rotation=45)
        self.ax.legend()
        self.canvas.draw()

    def update_details_tab(self, symbol):
        stock_info = self.stock_data_manager.get_stock_info(symbol)
        details = [
            ('Symbol', stock_info.get('symbol', 'N/A')),
            ('Short Name', stock_info.get('shortName', 'N/A')),
            ('Industry', stock_info.get('industry', 'N/A')),
            ('Sector', stock_info.get('sector', 'N/A')),
            ('Market Cap', stock_info.get('marketCap', 'N/A')),
            ('P/E Ratio', stock_info.get('trailingPE', 'N/A')),
            ('Dividend Yield', stock_info.get('dividendYield', 'N/A')),
            ('52 Week High', stock_info.get('fiftyTwoWeekHigh', 'N/A')),
            ('52 Week Low', stock_info.get('fiftyTwoWeekLow', 'N/A')),
            ('Description', stock_info.get('longBusinessSummary', 'N/A')),
        ]

        for i in self.details_tree.get_children():
            self.details_tree.delete(i)

        for attribute, value in details:
            self.details_tree.insert("", tk.END, values=(attribute, value))

    def update_current_price(self, price):
        self.current_price_label.config(text=f'Current Price: {price:.2f}')
        if self.target_price and price <= self.target_price:
            self.notify_target_price_reached(price)

    def on_search(self):
        symbol = self.symbol_entry.get().upper()
        period = self.period_var.get()
        if not symbol:
            messagebox.showwarning('Input Error', 'Please enter a stock symbol.')
            return
        self.status_label.config(text='Fetching data...')
        self.loading_spinner.start()
        self.fetch_and_enqueue_data(symbol, period)

    def set_target_price(self):
        try:
            target = float(self.target_entry.get())
            self.target_price = target
            self.target_symbol = self.symbol_entry.get().upper()
            messagebox.showinfo('Target Price Set', f'Target price of {target} set for {self.target_symbol}')
        except ValueError:
            messagebox.showerror('Invalid Input', 'Please enter a valid number for target price.')

    def check_target_price(self):
        if self.target_symbol:
            current_price = self.stock_data_manager.get_current_price(self.target_symbol)
            if current_price and current_price <= self.target_price:
                def update_gui():
                    self.notify_target_price_reached(current_price)
                self.master.after(0, update_gui)

    def notify_target_price_reached(self, price):
        messagebox.showinfo('Target Price Reached', f'{self.target_symbol} has reached your target price of {self.target_price}. Current price: {price:.2f}')

    def add_to_watchlist(self):
        symbol = self.watchlist_symbol_entry.get().upper()
        if not symbol:
            messagebox.showwarning('Input Error', 'Please enter a stock symbol.')
            return
        try:
            stock = yf.Ticker(symbol)
            stock_info = stock.info
            if not stock_info:
                raise ValueError("Unable to fetch data for this symbol.")

            price = stock.history(period='1d')['Close'].iloc[-1]
            pe_ratio = stock_info.get('trailingPE', None)
            market_cap = stock_info.get('marketCap', None)
            full_name = stock_info.get('longName', None)
            industry = stock_info.get('industry', None)

            self.db.add_to_watchlist(symbol, price, pe_ratio, market_cap, full_name, industry)
            self.watchlist_tree.insert("", tk.END, values=(symbol, price, pe_ratio, market_cap, full_name, industry))

        except ValueError as e:
            messagebox.showerror('Error', str(e))
        except Exception as e:
            messagebox.showerror('Error', f"An unexpected error occurred: {e}")

    def remove_from_watchlist(self):
        selected_items = self.watchlist_tree.selection()
        if not selected_items:
            messagebox.showwarning('Selection Error', 'Please select a stock from your watchlist to remove.')
            return

        for item in selected_items:
            try:
                symbol = self.watchlist_tree.item(item)['values'][0]
                self.db.remove_from_watchlist(symbol)
                self.watchlist_tree.delete(item)
            except IndexError:
                messagebox.showwarning("Error", "Could not retrieve symbol for selected item.")
                continue

    def on_watchlist_item_double_click(self, event):
        selected_item = self.watchlist_tree.selection()
        if selected_item:
            symbol = self.watchlist_tree.item(selected_item[0])['values'][0]
            self.symbol_entry.delete(0, tk.END)
            self.symbol_entry.insert(0, symbol)
            self.on_search()
            self.notebook.select(self.chart_frame)


    def load_watchlist_data(self):
        rows = self.db.get_watchlist()
        for row in rows:
            self.watchlist_tree.insert("", tk.END, values=row)

    def sort_watchlist(self, column, numeric=False):
        items = list(self.watchlist_tree.get_children())
        data = [(self.watchlist_tree.item(k, 'values'), k) for k in items]
        col_idx = self.watchlist_tree["columns"].index(column)

        if numeric:
            data.sort(key=lambda t: float(t[0][col_idx]) if t[0][col_idx] != 'N/A' else float('inf'), reverse=self.sort_direction[column])
        else:
            data.sort(key=lambda t: t[0][col_idx], reverse=self.sort_direction[column])

        for index, (_, k) in enumerate(data):
            self.watchlist_tree.move(k, "", index)

        self.sort_direction[column] = not self.sort_direction[column]

    def on_close(self):
        self.data_queue.put(None)
        self.stock_data_manager.executor.shutdown(wait=False)
        self.db.close()