from asset import Asset
import asset_prices

class Portfolio:
    def __init__(self,name):
        self.name = name
        self.asset_names = asset_prices.assets
        self.assets = {}
    
    def load_asset(self,asset,quantity) :
        """Loads an asset to the portfolio, with a price and a quantity (loaded on start)."""
        self.assets[asset] = Asset(asset,self.asset_names[asset],quantity)
    
    def add_asset(self,asset,quantity,balance) :
        """Adds/updates an asset to the portfolio, with a quantity."""
        quantity = float(quantity)
        if balance >= (self.asset_names[asset] * quantity):
            if asset in self.assets:
                self.assets[asset].quantity += quantity
                return 0
            else:
                self.assets[asset] = Asset(asset,self.asset_names[asset],quantity)
                return 0
        else:
            return "INSUFFICIENT_FUNDS"
    
    def remove_asset(self,asset,quantity):
        """Removes quantity from an asset if holdings are sufficient."""
        quantity = float(quantity)
        if asset in self.assets:
            if self.assets[asset].quantity >= quantity:
                self.assets[asset].quantity -= quantity
                return 0
            else:
                return f"INSUFFICIENT_QUANTITY {asset}"
        else:
            return f"ASSET_NOT_IN_PORTFOLIO {asset}"