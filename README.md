# stock_screener
A desktop application built with Python and Tkinter for screening stocks, charting price data, and managing a watchlist.  This application fetches real-time stock data using the `yfinance` library and stores watchlist data in a MySQL database.

Database Setup

    Create a MySQL database: Create a database named "stocks" (or change the database name in database.py).

    Create a user: Create a MySQL user with appropriate permissions to access the "stocks" database. Update the user credentials (user and password) in database.py to match your setup.

Running the Application

    Clone this repository.

    Install the required packages.

    Configure the database settings in database.py.

    Run app.py: python app.py
