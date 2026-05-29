class Account:
    def __init__(self,username,password,balance):
        self.username = username
        self.password = password
        self.balance = balance
        
    def deposit(self,amount):
        """Deposits funds into account."""
        self.balance += amount
    
    def withdraw(self,amount):
        """Withdraws funds from account."""
        if amount <= self.balance:
            self.balance -= amount
            return 0
        else:
            return "INSUFFICIENT_FUNDS"