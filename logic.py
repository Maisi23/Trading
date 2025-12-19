import pandas as pd

class BotAnalyzer:
    def __init__(self,trades,initial_balance=5000,risk=0.01):
        self.df = trades.copy()

        self.initial_balance = initial_balance
        self.risk = risk 
        
        required = {"Profit","Balance"}
        if not required.issubset(self.df.columns):
            raise KeyError("Columns 'Profit' and 'Balance' are required")


    def win_rate(self,BE = False):
        """
        Calcula los ratios para el bots o para el total de la cuenta
        Nota: Se considera BE cuando el profit fue menor que el 0.15% del balance actual
        """
         
        data= self.df

        #Calculo
        total = data["Profit"].count()
        if total==0: return 0

        percent = lambda x: round(x*100/total,2)  

        win = (
            (data["Profit"] > 0) & 
           (data["Profit"] > data["Balance"]*0.0015)
        ).sum()
         
        losses = (data["Profit"] < 0 ).sum()
        
        #Diccionario base
        dicc =  {
            "Win":[f"{percent(win)}%",win],
            "Loss":[f"{percent(losses)}%",losses]
        }

        

        #Queres los breakeven?
        if BE:
            breakeven = (
                (data["Profit"] <= data["Balance"]*0.0015) & 
                (data["Profit"] > 0)
            ).sum()
            
            dicc["BE"] = [f"{percent(breakeven)}%",breakeven]
        
        #Añado el total
        
        dicc["Total"] = ["100%", total]


        return pd.DataFrame(dicc,index=["Percent","n"])


    def profit_factor(self):
        """
        #* Profit Factor =  sum(positive profits) 
        #*                  --------------------------
        #*                  abs(sum(negative profits))
        """
        profits = self.df["Profit"]
        
        if "Profit" not in self.df.columns:
            raise KeyError("Column 'Profit' is required")


        total_profit = profits[profits > 0].sum()
        total_loss = profits[profits < 0].sum()

        if total_loss == 0:
            return float("inf")
        
        return round(total_profit / abs(total_loss), 2)