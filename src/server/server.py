from socket import *
from userdata import UserData
from account import Account
from portfolio import Portfolio
import asset_prices as ap
import time
import threading
import sqlite3
import signal

conn = sqlite3.connect("exchangedata.db",check_same_thread=False)
c = conn.cursor()  # create a cursor so commands can be executed

clients = []   # will be used to store all active client connections so they can be shutdown
lock = threading.Lock()

def server_setup():
    """Sets up the server (sets up tables in database and call relevant functions)."""
    c.execute("""
              CREATE TABLE IF NOT EXISTS accounts (
                  username TEXT PRIMARY KEY,                    -- Username is the primary key
                  password TEXT NOT NULL,                       -- Password for the account
                  balance REAL DEFAULT 0.0                      -- Balance for the account
        )""")
    c.execute("""
              CREATE TABLE IF NOT EXISTS portfolios (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,         -- Unique identifier for each portfolio entry
                  username TEXT NOT NULL,                       -- Username for the owner of the asset
                  asset TEXT NOT NULL,                          -- Name of the asset
                  quantity REAL DEFAULT 0.0                     -- Quantity of the asset owned by a user
        )""")
    c.execute("""
              CREATE TABLE IF NOT EXISTS transactions (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,         -- Unique identifier for each transaction entry
                  username TEXT NOT NULL,                       -- Username of the user performing the transaction
                  asset TEXT NOT NULL,                          -- Name of the asset
                  quantity REAL NOT NULL,                       -- Quantity transferred (is a REAL/Float)
                  action TEXT NOT NULL,                         -- Action being performed (bought/sold)
                  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP  -- Time of the transaction
        )""")
    conn.commit()
    load_accounts()
    load_portfolios()

def load_accounts():
    """Loads accounts from accounts file."""
    try:
        # Gets all the accounts from the accounts table, and fetches them into a list
        c.execute("SELECT * FROM accounts")
        accounts_list = c.fetchall()
        # Loops through all the accounts in the accounts_list, creates an instance of UserData
        # with UserData.account being an Account instance and UserData.portfolio being a Portfolio instance
        for username,password,balance in accounts_list:
            new_user_data = UserData(Account(username,password,balance),Portfolio(username))
            # Adds the new user to the users dictionary for quick lookup
            users[username] = new_user_data
    except Exception as e:
        print(f"Error loading accounts: {e}")

def load_portfolios():
    """Loads portfolios from portfolios file."""
    try:
        # Loops through all the users in the users dictionary and
        # gets all the asset and quantity entries from the portfolios table for their username
        for user in users:
            portfolio = users[user].portfolio # Gets the loaded portfolio for this user
            c.execute("""SELECT asset, quantity FROM portfolios WHERE username = ?""",(user,))
            # Fetches the assets and quantities for this user into a list
            portfolio_assets = c.fetchall()
            # Loops through portfolio_assets, getting the asset and quantity for each index
            for asset,quantity in portfolio_assets:
                # Loads the asset with it's quantity to the assets dictionary in the portfolio
                portfolio.load_asset(asset,quantity)
    except Exception as e:
        print(f"Error loading portfolios: {e}")
            
def write_accounts():
    """Saves accounts to file."""
    with lock:
        try:
            # Loop through all the values for users in the users dictionary (UserData instance)
            for userdata in users.values():
                # Get the Account instance for the user, and add or
                # update it's data (username, password, balance) into the accounts table
                account = userdata.account
                c.execute("""INSERT OR REPLACE INTO accounts (username, password, balance) VALUES (?, ?, ?)""",
                        (account.username,account.password,account.balance))
                conn.commit()
        except Exception as e:
            print(f"Error writing accounts: {e}")

def write_portfolio(user):
    """Overwrites portfolio entries to file for a user."""
    with lock:
        try:
            # Deletes all currently existing portfolio entries for this user
            c.execute("""DELETE FROM portfolios WHERE username = ?""",(user,))
            portfolio = users[user].portfolio
            # Loop through all the assets in this users loaded portfolio
            for asset in portfolio.assets.values():
                # Add all loaded assets from this users portfolio as new entries in the portfolios table
                c.execute("""INSERT INTO portfolios (username, asset, quantity) VALUES (?, ?, ?)""",
                        (user,asset.name,asset.quantity))
                conn.commit()
        except Exception as e:
            print(f"Error writing portfolios: {e}")

def create_account(username,password,deposit):
    """Creates an account with a username, password, and initial deposit."""
    try:
        # Creates a new UserData instance, with UserData.account being an 
        # Account instance and UserData.portfolio being a Portfolio instance,
        # before writing the new account to file
        users[username] = UserData(Account(username,password,deposit),Portfolio(username))
        write_accounts()
    except Exception as e:
        print(f"Error creating account: {e}")

def send_data(client,data):
    """Sends data to the client. Should include a code (INVALID_LOGIN, VALID_LOGIN), 
    and can also contain data. Data is seperating using a space."""
    try:
        # Attempt to send data to the client, casting the data to string and encoding using a pre-defined format
        client.send(str(data).encode("utf-8"))
    except Exception as e:
        # If an exception is raised, output an error message
        print(f"Error sending data: {e}")

def recv_data(client):
    """Receives data from the client. Will contain a code (LOGIN, SIGNUP etc.) and can also contain information
    (username, password etc.), and returns the received data."""
    try:
        # Attempt to receive data from the client, using a pre-defined buffer size,
        # and decoding it using a pre-defined format, before returning the received message
        data = client.recv(BUFSIZE).decode("utf-8")
        return data
    except Exception as e:
        # If an exception is raised, output an error message
        print(f"Error receiving data: {e}")

def send_portfolio(client,username):
    """Sends a users portfolio to the relevant client."""
    for asset in users[username].portfolio.assets.values():
        # Loops through all the Assets in this users portfolio, and sends its relevant data to the client
        data = f"LOAD_PORTFOLIO_ASSET {asset.name} {str(asset.get_value())} {str(asset.quantity)}"
        send_data(client,data)
        time.sleep(0.4)
    send_data(client,"END_PORTFOLIO_LOAD")

def authenticate_user(username,password,action):
    """Authenticates the entered credentials from a client, returns VALID if valid and INVALID if invalid."""
    if action == "SIGNUP":
        # Returns True if the username is NOT in users, otherwise False
        return username not in users
    elif action == "LOGIN":
        # Returns True if the username IS in users and the input password is equal to the account password
        return username in users and password == users[username].account.password
    return False # Handles errors cleanly

def login(login_data):
    """Allows a client to login to an account."""
    # In the case of the client attempting to login, authenticate login data,
    # then return a validity flag (Boolean) and the username
    code,username,password = login_data.split(" ")
    is_valid = authenticate_user(username,password,code)
    return is_valid,username

def signup(login_data):
    """Allows the user to create a new account."""
    # In the case of the client attempting to signup, authenticate signup data,
    # then return a validity flag (Boolean) and the username
    code,username,password,deposit = login_data.split(" ")
    is_valid = authenticate_user(username,password,code)
    if is_valid:
        create_account(username,password,float(deposit))
    return is_valid,username

def deposit(client,username,amount):
    """Deposits money into an account for a user."""
    try:
        # Deposit funds and update the account in the database table
        users[username].account.deposit(float(amount))
        write_accounts()
        # Inform the client that the withdrawal was successful
        new_balance = users[username].account.balance
        send_data(client,f"DEPOSITED {amount} {new_balance}")
    except Exception as e:
        print(f"Error depositing amount for {username}: {e}")

def withdraw(client,username,amount):
    """Attempts to withdraw an amount from an account for a user."""
    try:
        # Attempt to withdraw funds
        withdraw_flag = users[username].account.withdraw(float(amount))
        if withdraw_flag == 0:
            # If the withdrawal was successful update the account in the database table
            write_accounts()
            # Inform the client that the withdrawal was successful
            new_balance = users[username].account.balance
            send_data(client,f"WITHDRAWN {amount} {new_balance}")
        else:
            send_data(client,withdraw_flag)
    except Exception as e:
        print(f"Error withdrawing amount for {username}: {e}")

def save_transaction(username,asset,quantity,action):
    """Saves a transaction to file."""
    with lock:
        try:
            # Attempt to save a transaction to file (saves to the transactions table in the database)
            c.execute("""INSERT INTO transactions (username, asset, quantity, action) VALUES (?, ?, ?, ?)""",
                    (username,asset,quantity,action))
            conn.commit()
        except Exception as e:
            print(f"Error saving transaction: {e}")

def buy(client,username,asset,quantity):
    """Allows a user to buy a quantity of an asset."""
    try:
        # Attempt to buy the asset and getting the returned flag
        balance = users[username].account.balance
        trade_flag = users[username].portfolio.add_asset(asset,quantity,balance)
        if trade_flag == 0:
            # If the trade was successful, update the balance in the account
            amount = asset_prices[asset] * float(quantity)
            users[username].account.withdraw(float(amount))
            # Rewrite the portfolio entries for this user, and update their account in the database table
            write_portfolio(username)
            write_accounts()
            # Inform the client that the trade was successful
            new_balance = users[username].account.balance
            send_data(client,f"BOUGHT {asset} {quantity} {new_balance}")
            # Save the transaction to file
            save_transaction(username,asset,quantity,"BOUGHT")
        else:
            # Otherwise, send the error code
            send_data(client,trade_flag)
    except Exception as e:
        print(f"Error buying {quantity} {asset} for {username}: {e}")

def sell(client,username,asset,quantity):
    """Allows a user to sell a quantity of an asset."""
    try:
        trade_flag = users[username].portfolio.remove_asset(asset,quantity)
        if trade_flag == 0:
            # If the trade was successful, update the balance in the account
            amount = asset_prices[asset] * float(quantity)
            users[username].account.deposit(float(amount))
            # Rewrite the portfolio entries for this user, and update their account in the database table
            write_portfolio(username)
            write_accounts()
            # Inform the client that the trade was successful
            new_balance = users[username].account.balance
            send_data(client,f"SOLD {asset} {quantity} {new_balance}")
            # Save the transaction to file
            save_transaction(username,asset,quantity,"SOLD")
        else:
            # Otherwise, send the error code
            send_data(client,trade_flag)
    except Exception as e:
        print(f"Error selling {quantity} {asset} for {username}: {e}")

def handle_client(client,addr):
    """Handles client interaction with server."""
    # Adds the client to the clients list (of active connections)
    # and handles all interaction with the client whilst the connection is still open
    client_username = ""
    try:
        with lock:
            # Adds the client to the clients list so that it can be accessed outside the thread
            clients.append(client)
        
        # Loop through all assets and send them to the client so that they can be displayed
        for asset,price in asset_prices.items():
            data = f"LOAD_ASSET {asset} {str(price)}"
            send_data(client,data)
            time.sleep(0.4) # Used time.sleep to prevent data streams from getting received together
        send_data(client,"END_ASSET_LOAD")
        
        # Repeatedly waits for a valid login/signup attempt from the user
        while True:
            login_data = recv_data(client)
            if login_data.startswith("LOGIN"):
                # Validate login data
                is_valid,client_username = login(login_data)
                if not is_valid:
                    send_data(client,"INVALID_LOGIN")
                else:
                    break
            elif login_data.startswith("SIGNUP"):
                # Validate signup data
                is_valid,client_username = signup(login_data)
                if not is_valid:
                    send_data(client,"INVALID_SIGNUP")
                else:
                    break
            elif login_data.startswith("EXIT"):
                return
        balance = users[client_username].account.balance
        send_data(client,f"VALID_LOGIN {client_username} {str(balance)}")
        
        # Sends the users portfolio to their associated client
        send_portfolio(client,client_username)

        # Repeatedly waits for actions sent by the client, 
        # then performs relevant operations and returns results to client
        action,*data = recv_data(client).split(" ")
        while not action.startswith("EXIT"):
            match action:
                case a if a.startswith("DEPOSIT"):
                    deposit(client,client_username,data[0])
                case a if a.startswith("WITHDRAW"):
                    withdraw(client,client_username,data[0])
                case a if a.startswith("BUY"):
                    buy(client,client_username,data[0],data[1])
                case a if a.startswith("SELL"):
                    sell(client,client_username,data[0],data[1])
                case a if a.startswith("RELOAD_PORTFOLIO"):
                    send_portfolio(client,client_username)
            action,*data = recv_data(client).split(" ")
    except Exception as e:
        print(f"Error: {e}")
    finally:  # Runs once the client has closed the connection (will always run)
        with lock:
            # Safely shuts down connection with client and removes it from clients list
            clients.remove(client)
            client.shutdown(SHUT_RDWR) # Closes read and write (sending and receving)
            client.close()
            print(f"Connection closed from {addr}")

def shutdown_connections():
    """Closes all active client connections."""
    with lock:
        for client in clients:
            try:
                # Shutdown method from socket library, used to safely shutdown the
                # sending and receiving directions of a socket, before closing the connection
                client.shutdown(SHUT_RDWR)
                client.close()
            except Exception as e:
                print(f"Error closing client connection: {e}")
        clients.clear()  # Empties clients list of all previous connections

def shutdown_server(server):
    """Cleanly shuts down the server."""
    print("Shutting down server...")
    shutdown_connections()  # Closes all active client connections
    conn.close()            # Closes the database connection
    server.close()          # Closes the server socket
    print("Server shutdown successfully.")

users = {}   # Loaded user data will be stored here 
             # (key: username, value: UserData instance (containing an account and a portfolio))
asset_prices = ap.assets # Loads the assets dictionary from the ap python file into the asset_prices dictionary

# Initialisation for host (server) address and buffer size
HOST = "localhost"
PORT = 4545
ADDRESS = (HOST,PORT)

BUFSIZE = 1024

def main():
    """Main server body, where requests are handled and other functions are called."""
    server_setup()
    
    # reates and binds a socket that can be connected to, and listens for upto 5 connections
    server = socket(AF_INET,SOCK_STREAM)
    server.bind(ADDRESS)
    server.listen(5)
    print(f"Server is listening on port {PORT}...")
    
    # Handle server shutdown on force exit
    signal.signal(signal.SIGINT,shutdown_server)
    signal.signal(signal.SIGTERM,shutdown_server)
    
    # Loop continuously, accepting connections from clients and starting threads that
    # can handle each client individually
    try:
        while True:
            client, addr = server.accept()
            print(f"Connection from {addr}")
            client_handler = threading.Thread(target=handle_client,args=(client,addr))
            client_handler.start()
    except Exception as e:
        print(f"Error accepting connections: {e}")
        

if __name__ == "__main__":
    main()