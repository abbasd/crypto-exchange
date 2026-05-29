class Asset:
    def __init__(self,name,price,quantity):
        self.name = name
        self.price = price
        self.quantity = quantity
        
    def get_value(self):
        """Returns the total value based on the price and quantity held."""
        total_value = self.price * self.quantity
        return total_value