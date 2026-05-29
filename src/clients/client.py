from socket import *
from tkinter import *
from tkinter import ttk
from tkinter import messagebox as msg, simpledialog as dialog
import threading
import time
import sys
import subprocess

# IP and port of the host (server), combined into an address
HOST = "localhost"
PORT = 4545
ADDRESS = (HOST,PORT)

BUFSIZE = 1024    # The size of the buffer used to receive data from the server
FORMAT = "utf-8"  # The format used to encode and decode data before sending and after receieving

# Creates the client socket, which will be used to connect to the server socket,
# and through which data can be send and received
client = socket(AF_INET,SOCK_STREAM)

class App:
    def __init__(self):
        # Shared response variable which holds responses from the network thread
        self.response = ""
        
        # Used to store the assets and their prices
        self.assets = {}
        
        # Used to store a copy of the users portfolio
        self.portfolio = []
        
        # Connects to the server and loads assets
        client.connect(ADDRESS)
        self.load_assets()
        
        # Creates the window for the main app (temporarily hidden until the user logs-in/signs-up)
        self.root = Tk()
        self.root.title("Crypto Exchange")
        self.root.geometry("1000x600")
        self.root.resizable(False,False)
        self.root.withdraw()
        
        # New window used for logging into or creating an account
        self.login_page = Toplevel()
        self.login_page.title("Login or Sign Up")
        self.login_page.geometry("800x500")
        
        # Heading for login page
        Label(self.login_page,text="LOGIN OR SIGN UP",
              font=("Ariel",20)).place(x=0,y=-50,relx=0.5,rely=0.3,anchor="center")

        # Username prompt and input entry area
        Label(self.login_page,text="Username:",font=("Ariel",20)).place(x=0,y=20,relx=0.5,rely=0.3,anchor="center")
        self.username_entry = Entry(self.login_page,width=30)
        self.username_entry.place(x=0,y=55,relx=0.5,rely=0.3,anchor="center")

        # Password promp and input entry area
        Label(self.login_page,text="Password:",font=("Ariel",20)).place(x=0,y=100,relx=0.5,rely=0.3,anchor="center")
        self.password_entry = Entry(self.login_page,width=30)
        self.password_entry.place(x=0,y=135,relx=0.5,rely=0.3,anchor="center")

        # Login and sign up buttons, linked to the login() and signup() functions respectively
        self.login_button = Button(self.login_page,text="LOGIN",bg="teal",width=7,height=1,
                            command=lambda: self.on_login(self.username_entry.get(),self.password_entry.get()))
        self.login_button.place(x=40,y=180,relx=0.5,rely=0.3,anchor="center")
        self.signup_button = Button(self.login_page,text="SIGN UP",bg="skyblue",width=7,height=1,
                            command=lambda: self.on_signup(self.username_entry.get(),self.password_entry.get()))
        self.signup_button.place(x=-40,y=180,relx=0.5,rely=0.3,anchor="center")
        
        # Schedule self.check_response after 100 ms
        self.root.after(100,self.check_response)
        
        # Bind the close event for exiting the app
        self.login_page.protocol("WM_DELETE_WINDOW",self.on_close)
        
        self.root.mainloop()
    
    def send_data(self,data):
        """Sends data to the server."""
        try:
            # Attempts to send data to the server, casting to string, and encoding using a pre-defined format
            client.send(str(data).encode(FORMAT))
        except Exception as e:
            # If an exception is raised, set self.response to an Error code so that an error is output
            self.response = f"Error: {e}"
        
    def recv_data(self):
        """Receives data from the server."""
        try:
            # Receives data from the server in a pre-defined buffer size, and decodes it using a pre-defined
            # format, before returning the message (data).
            msg = client.recv(BUFSIZE).decode(FORMAT)
            return msg
        except Exception as e:
            # If an exception is raised, set self.response to an Error code so that an error is output
            self.response = f"Error: {e}"
    
    def disable_buttons(self):
        """Disables all main app buttons so data is not repeatedly send to the server."""
        self.buy_button.config(state="disabled")
        self.sell_button.config(state="disabled")
        self.deposit_button.config(state="disabled")
        self.withdraw_button.config(state="disabled")
    
    def enable_buttons(self):
        """Enables all main app buttons so they can be used again."""
        self.buy_button.config(state="normal")
        self.sell_button.config(state="normal")
        self.deposit_button.config(state="normal")
        self.withdraw_button.config(state="normal")
    
    def on_login(self,username,password):
        """Runs on login button click, to start a new thread running login networking logic."""
        # Temporarily disables the login/signup buttons to prevent the LOGIN/SIGNUP code from being sent repeatedly
        self.login_button.config(state="disabled")
        self.signup_button.config(state="disabled")
        
        # Starts a login networking thread, which is a daemon 
        # thread (will be terminated when the main thread terminates)
        threading.Thread(target=self.login,args=(username,password),daemon=True).start()
        
    def on_signup(self,username,password):
        """Runs on signup button click, to start a new thread running signup networking logic."""
        # Temporarily disables the login/signup buttons to prevent the LOGIN/SIGNUP code from being sent repeatedly
        self.login_button.config(state="disabled")
        self.signup_button.config(state="disabled")
        
        # Starts a signup networking thread, which is a daemon 
        # thread (will be terminated when the main thread terminates)
        threading.Thread(target=self.signup,args=(username,password),daemon=True).start()
    
    def login(self,username,password):
        """Allows the client to login to an account."""
        try:
            if " " in username or " " in password:
                # Error message is output, the login and signup buttons are reactivated, and the function is exited
                msg.showerror("Error","Username/password cannot contain a space")
                self.login_button.config(state="normal")
                self.signup_button.config(state="normal")
                return
            elif not username or not password:
                # Error message is output, the login and signup buttons are reactivated, and the function is exited
                msg.showerror("Error","Username/password cannot be left blank")
                self.login_button.config(state="normal")
                self.signup_button.config(state="normal")
                return
            else:
                # If input is valid, send the LOGIN data to the server, and set self.response to the received
                self.send_data(f"LOGIN {username} {password}") # C1
                self.response = self.recv_data() # S1
        except Exception as e:
            self.response = f"Error: {e}"
    
    def signup(self,username,password):
        """Allows the client to create a new account."""
        try:
            if " " in username or " " in password:
                # Error message is output, the login and signup buttons are reactivated, and the function is exited
                msg.showerror("Error","Username/password cannot contain a space")
                self.login_button.config(state="normal")
                self.signup_button.config(state="normal")
                return
            elif not username or not password:
                # Error message is output, the login and signup buttons are reactivated, and the function is exited
                msg.showerror("Error","Username/password cannot be left blank")
                self.login_button.config(state="normal")
                self.signup_button.config(state="normal")
                return
            else:
                # Asks the user to enter an initial deposit (float), with validation
                temp_win = Tk()
                temp_win.withdraw()
                deposit = dialog.askfloat("Initial Deposit","Enter initial deposit (GBP)",parent=temp_win)
                
                # If the user cancels the sign up, the login/signup buttons are reactivated, and the function exited
                if not deposit:
                    self.login_button.config(state="normal")
                    self.signup_button.config(state="normal")
                    temp_win.destroy()
                    return
                
                # Sends the SIGNUP data to the server, receives the response, and destroy the temp window
                self.send_data(f"SIGNUP {username} {password} {str(deposit)}")
                self.response = self.recv_data() # S1
                temp_win.destroy()
        except Exception as e:
            self.response = f"Error: {e}"
    
    def setup_main_app(self,username,balance):
        """Sets up the layout for the main app GUI."""
        # Destroys the login page and shows the main app window (using deiconify)
        self.root.after(0,self.login_page.destroy)
        self.root.deiconify()
        
        # Trading frame (for the exchange)
        self.trading_frame = Frame(self.root,bg="white",width=450,height=450)
        self.trading_frame.place(x=30,y=40)
        # Account frame (for account management)
        self.account_frame = Frame(self.root,bg="white",width=450,height=220)
        self.account_frame.place(x=520,y=40)
        # Portfolio frame (to display portfolio info)
        self.portfolio_frame = Frame(self.root,bg="white",width=450,height=220)
        self.portfolio_frame.place(x=520,y=300)
        
        # Assets table for assets and current prices
        self.trading_tree = ttk.Treeview(self.trading_frame,columns=("Asset","Price"),show="headings",height=18)
        self.trading_tree.heading("Asset",text="ASSET")
        self.trading_tree.heading("Price",text="PRICE")
        self.trading_tree.column("Asset",width=225,anchor="center")
        self.trading_tree.column("Price",width=225,anchor="center")
        
        # Adds all assets and their prices to the Treeview object
        self.display_assets()
        
        # Displays the table
        self.trading_tree.pack()
        
        # Stores the currently selected item in Treeview table
        self.selected_asset = "No Asset Selected"
        
        # Schedules to get the currently selected item in the assets Treeview table
        self.root.after(100,self.get_selected_asset)
        
        # Displays the currently selected asset
        self.selected_asset_label = Label(self.root,text=self.selected_asset,font=("Ariel",18))
        self.selected_asset_label.place(x=-240,y=280,relx=0.5,rely=0.3,anchor="center")
        
        # Buy button, used to buy a quantity of an asset
        self.buy_button = Button(self.root,text="BUY",bg="lightgreen",width=13,height=2,
                            command=lambda: self.execute_trade("BUY"))
        self.buy_button.place(x=-310,y=320,relx=0.5,rely=0.3,anchor="center")
        
        # Sell button, used to sell a quantity of an asset
        self.sell_button = Button(self.root,text="SELL",bg="red",width=13,height=2,
                            command=lambda: self.execute_trade("SELL"))
        self.sell_button.place(x=-170,y=320,relx=0.5,rely=0.3,anchor="center")
        
        # Username label
        Label(self.account_frame,text=username,bg="white",
              font=("Ariel",20)).place(x=0,y=-20,relx=0.5,rely=0.3,anchor="center")
        
        # Account balance label
        self.account_balance_label = Label(self.account_frame,text=f"£{balance:,.2f}",bg="white",font=("Ariel",18))
        self.account_balance_label.place(x=0,y=20,relx=0.5,rely=0.3,anchor="center")
        
        # Deposit button, used to add funds to the account
        self.deposit_button = Button(self.account_frame,text="DEPOSIT",font=("Ariel",13),
                                 bg="lightgray",width=13,height=1,
                                 command=self.add_funds)
        self.deposit_button.place(x=-80,y=80,relx=0.5,rely=0.3,anchor="center")
        
        # Withdraw button, used to withdraw funds from the account
        self.withdraw_button = Button(self.account_frame,text="WITHDRAW",font=("Ariel",13),
                                  bg="lightgray",width=13,height=1,
                                  command=self.withdraw_funds)
        self.withdraw_button.place(x=80,y=80,relx=0.5,rely=0.3,anchor="center")
        
        # Portfolio table for assets, quantities, and values (displays holdings)
        self.portfolio_tree = ttk.Treeview(self.portfolio_frame,
                                           columns=("Asset","Value","Quantity"),show="headings",height=10)
        self.portfolio_tree.heading("Asset",text="ASSET")
        self.portfolio_tree.heading("Value",text="VALUE")
        self.portfolio_tree.heading("Quantity",text="QUANTITY")
        self.portfolio_tree.column("Asset",width=150,anchor="center")
        self.portfolio_tree.column("Value",width=150,anchor="center")
        self.portfolio_tree.column("Quantity",width=150,anchor="center")
        
        # Displays the table
        self.portfolio_tree.pack()
        
        # Total value label (for the total value of all the holdings in the portfolio)
        self.total_value_label = Label(self.portfolio_frame,text="Total Value: £0.00",bg="white",font=("Calibri",13))
        self.total_value_label.place(x=20,y=190)
        
        # Loading label
        self.portfolio_loading_label = Label(self.portfolio_frame,text="",bg="white",font=("Calibri",35))
        self.portfolio_loading_label.place(x=400,y=160)
        
        # Load and display portfolio
        self.load_portfolio()
        
        # Help button
        self.help_button = Button(self.root,text="?",font=("Calibri",13),bg="lightgray",
                                    width=3,height=1,command=self.help)
        self.help_button.place(x=25,y=550)
        
        # Log out button
        self.logout_button = Button(self.root,text="LOGOUT",font=("Ariel",13),bg="lightgray",
                                    width=8,height=1,command=self.logout)
        self.logout_button.place(x=885,y=550)
        
        # Bind the close event for exiting the app
        self.root.protocol("WM_DELETE_WINDOW",self.on_close)
    
    def add_funds(self):
        """Deposits an amount money into the account."""
        # Deactivate buttons to prevent multiple clicks from occurring by accident
        self.disable_buttons()
        # Asks the user to enter a quantity to buy (float), with validation
        temp_win = Tk()
        temp_win.withdraw()
        amount = dialog.askfloat("Amount","Enter amount (GBP)",parent=temp_win)
        
        # If the user cancels the deposit, the buttons are reactivated, and the function exited
        if not amount:
            self.enable_buttons()
            temp_win.destroy()
            return
        # If the user enters an amount <= to 0, the buttons are reactivated, and the function exited
        elif amount <= 0:
            self.enable_buttons()
            temp_win.destroy()
            self.response = "Error: Enter an amount greater than 0"
            return
        else:
            # Send the DEPOSIT data to the server, wait for a response, then destroy the temp window
            self.send_data(f"DEPOSIT {amount}")
            self.response = self.recv_data()
            temp_win.destroy()
    
    def withdraw_funds(self):
        """Attempts to withdraw an amount of money from the account"""
        # Deactivate buttons to prevent multiple clicks from occurring by accident
        self.disable_buttons()
        # Asks the user to enter a quantity to buy (float), with validation
        temp_win = Tk()
        temp_win.withdraw()
        amount = dialog.askfloat("Amount","Enter amount (GBP)",parent=temp_win)
        
        # Amount input validation
        if not amount:
            # Runs if user cancels
            self.enable_buttons()
            temp_win.destroy()
            return
        elif amount <= 0:
            self.enable_buttons()
            temp_win.destroy()
            self.response = "Error: Enter an amount greater than 0"
            return
        else:
            # Send the WITHDRAW data to the server, wait for a response, then destroy the temp window
            self.send_data(f"WITHDRAW {amount}")
            self.response = self.recv_data()
            temp_win.destroy()
    
    def execute_trade(self,action):
        """Allows the user to buy or sell a quantity of an asset."""
        if self.selected_asset != "No Asset Selected":
            # Deactivate buttons to prevent multiple clicks from occurring by accident
            self.disable_buttons()
            # Asks the user to enter a quantity to buy (float), with validation
            temp_win = Tk()
            temp_win.withdraw()
            quantity = dialog.askfloat("Quantity","Enter quantity",parent=temp_win)
            
            # Quantity input validation
            if not quantity:
                # Runs if user cancels
                self.enable_buttons()
                temp_win.destroy()
                return
            elif quantity <= 0:
                self.enable_buttons()
                temp_win.destroy()
                self.response = "Error: Enter a quantity greater than 0"
                return
            else:
                # Send the TRADE data to the server, wait for a response, then destroy the temp window
                self.send_data(f"{action} {self.selected_asset} {quantity}")
                self.response = self.recv_data()
                temp_win.destroy()
        else:
            # If there is no currently selected asset, set self.response to an error which will then be output
            self.response = f"Error: No Asset Selected"
    
    def load_assets(self):
        """Loads assets and prices from the server."""
        # Loops continuously, receiving data from the server
        while True:
            self.response = self.recv_data()
            # Stop loading if the received data starts with the code END_ASSET_LOAD
            if self.response.startswith("END_ASSET_LOAD"):
                break
            # Otherwise get the data (asset and price) and add the asset to the dictionary, 
            # with price as the value
            code,*data = self.response.split(" ")
            self.assets[data[0]] = data[1]
    
    def display_assets(self):
        """Displays assets and their prices in the assets Treeview table."""
        # Loops through the asset items in self.assets, getting the key and the value
        for asset,price in self.assets.items():
            # Adds the items (asset and price) to the Treeview table
            price = f"£{float(price):,.2f}"
            self.trading_tree.insert("","end",values=(asset,price))
    
    def portfolio_load_anim(self):
        """Displays an animation using self.portfolio_loading_label when loading portfolio."""
        for i in range(1,4):
            time.sleep(0.1)
            text = "." * i
            self.portfolio_loading_label.config(text=text)
        for i in range(2,-1,-1):
            time.sleep(0.1)
            text = (" " * (3-i)) + ("." * i)
            self.portfolio_loading_label.config(text=text)
        
    def load_portfolio(self):
        """Loads a copy of the users portfolio from the server."""
        self.portfolio = []
        # Loops continuously, receiving data from the server
        while True:
            self.response = self.recv_data()
            # Stop loading if the received data starts with the code END_PORTFOLIO_LOAD
            if self.response.startswith("END_PORTFOLIO_LOAD"):
                break
            # Otherwise get the data (asset,price,quantity) and add the asset to the portfolio dictionary
            code,*data = self.response.split(" ")
            self.portfolio.append([data[0],data[1],data[2]])
        self.display_portfolio()
    
    def display_portfolio(self):
        """Displays assets, values, and quantities in the portfolio Treeview table."""
        # Empties self.portfolio_tree so that entries can be replaced
        for row in self.portfolio_tree.get_children():
            self.portfolio_tree.delete(row)

        # Start a thread to play the portfolio loading animation so that the loading itself is not blocked
        threading.Thread(target=self.portfolio_load_anim,daemon=True).start()
        
        # Loops through the asset items in self.assets, getting the key and the value
        for asset,value,quantity in self.portfolio:
            # Adds the items (asset, values, and quantities) to the Treeview table
            value = f"£{float(value):,.2f}"
            quantity = f"{float(quantity):,.2f}"
            self.portfolio_tree.insert("","end",values=(asset,value,quantity))
        
        total_value = sum(float(item[1]) for item in self.portfolio)
        self.total_value_label.config(text=f"Total Value: £{total_value:,.2f}")
    
    def get_selected_asset(self):
        """Gets the currently selected asset in the assets Treeview table,
        and sets the text of self.selected_asset_label to the value, before rescheduling itself."""
        selected_row = self.trading_tree.selection() # Gets the current selection in the Treeview table
        # If there is a row selected, set self.selected_asset to the selected Asset name
        if selected_row:
            self.selected_asset = self.trading_tree.item(selected_row[0])["values"][0]
            self.selected_asset_label.config(text=self.selected_asset)
        else: # If no row is selected set it to "No Asset Selected"
            self.selected_asset = "No Asset Selected"
        self.root.after(100,self.get_selected_asset) # Reschedules itself (get_selected_asset)
    
    def help(self):
        """Displays helpful tips on how to use the app."""
        go_tour = msg.askokcancel("Tour?","Press OK to start tour of app features")
        if go_tour:
            # Tour for trading area
            msg.showinfo("Assets Table","The table on the left contains assets and their prices")
            msg.showinfo("Selecting Assets","Clicking on an asset in the table will select it")
            msg.showinfo("Making Trades","After selecting an asset, click BUY or SELL to make a trade")
            msg.showinfo("Buying/Selling","This will prompt you to enter the quantity to trade")
            # Tour for accounts area
            msg.showinfo("Accounts Area","The upper right area contains functions relating to your account")
            msg.showinfo("Current Balance","The balance shown under your username is your current balance")
            msg.showinfo("Deposit or Withdraw","Clicking DEPOSIT or WITHDRAW will prompt you to enter an amount")
            msg.showinfo("Manipulating Balance","This amount will then be added to or withdrawn from your account")
            # Tour of portfolio area
            msg.showinfo("Portfolio Area","The lower right table contains your portfolio")
            msg.showinfo("Entries","The entries in this table show the holdings for your account")
            msg.showinfo("Elements","This includes the asset name, total value for the asset, and the quantity held")
            msg.showinfo("Total Value","The Total Value is the sum of the values of all holdings in the portfolio")
    
    def logout(self):
        """Logs the user out of the account."""
        should_logout = msg.askyesno("Logout?","Are you sure you want to logout?")
        if should_logout:
            # Send the EXIT code to the server to it knows that the connection will be terminated
            self.send_data("EXIT")
            # Destroy the GUI
            self.root.destroy()
            # Exit the program and restart it (ensures no trace of the prev logged in account is still accessible)
            sys.exit(subprocess.call([sys.executable] + sys.argv))
    
    def on_close(self):
        """Runs a shutdown sequence when the GUI is closed."""
        self.send_data("EXIT")
        self.root.destroy()
    
    def check_response(self):
        """Checks the shared response variable for updates from the network thread."""
        if self.response is not None:
            if self.response.startswith("Error"):
                msg.showerror("Error",self.response)
            else:
                code,*data = self.response.split(" ")
                match code:
                    case "INVALID_LOGIN":
                        # Error message is output, and login/signup buttons are reactivated
                        msg.showerror("Error","Incorrect username or password")
                        self.login_button.config(state="normal")
                        self.signup_button.config(state="normal")
                    case "INVALID_SIGNUP":
                        # Error message is output, and the login/signup buttons are reactivated
                        msg.showerror("Error","Username taken")
                        self.login_button.config(state="normal")
                        self.signup_button.config(state="normal")
                    case "VALID_LOGIN":
                        self.setup_main_app(data[0],float(data[1]))
                    case "LOAD_BALANCE":
                        self.account_balance_label.config(text=data[0])
                        self.enable_buttons()
                    case "INSUFFICIENT_FUNDS":
                        # Error message is output, and buttons are reactivated
                        msg.showerror("Error","Insufficient funds in account to complete transaction")
                        self.enable_buttons()
                    case "INSUFFICIENT_QUANTITY":
                        # Error message is output, and buttons are reactivated
                        msg.showerror("Error",f"Insufficient quantity of {data[0]} in portfolio")
                        self.enable_buttons()
                    case "ASSET_NOT_IN_PORTFOLIO":
                        # Error message is output, and buttons are reactivated
                        msg.showerror("Error",f"No {data[0]} in portfolio")
                        self.enable_buttons()
                    case "DEPOSITED":
                        # Balance is updated, confirmation message is output, and buttons are re-enabled
                        self.account_balance_label.config(text=f"£{float(data[1]):,.2f}")
                        msg.showinfo("Deposit Complete",f"£{data[0]} deposited")
                        self.enable_buttons()
                    case "WITHDRAWN":
                        # Balance is updated, confirmation message is output, and buttons are re-enabled
                        self.account_balance_label.config(text=f"£{float(data[1]):,.2f}")
                        msg.showinfo("Withdrawal Complete",f"£{data[0]} withdrawn")
                        self.enable_buttons()
                    case "BOUGHT":
                        # Balance is updated, confirmation message is output, and buttons are re-enabled
                        self.account_balance_label.config(text=f"£{float(data[2]):,.2f}")
                        msg.showinfo("Asset Bought",f"{data[1]} {data[0]} bought")
                        self.send_data("RELOAD_PORTFOLIO") # Reload the portfolio
                        self.load_portfolio()
                        self.enable_buttons()
                    case "SOLD":
                        # Balance is updated, confirmation message is output, and buttons are re-enabled
                        self.account_balance_label.config(text=f"£{float(data[2]):,.2f}")
                        msg.showinfo("Asset Sold",f"{data[1]} {data[0]} sold")
                        self.send_data("RELOAD_PORTFOLIO") # Reload the portfolio
                        self.load_portfolio()
                        self.enable_buttons()
                    # The following codes (besides the catchall _) are to be ignored as they are handled
                    # elswhere in the program (ignored by using pass)
                    case "LOAD_ASSET":
                        pass
                    case "END_ASSET_LOAD":
                        pass
                    case "END_PORTFOLIO_LOAD":
                        pass
                    case "":
                        pass
                    case _: # Catchall, used in the case of an unknown code
                        msg.showerror("Error","Unknown code from server")
            self.response = None
        self.root.after(100,self.check_response) # Reschedules the check_response function

if __name__ == "__main__":
    app = App()