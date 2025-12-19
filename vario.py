import pandas as pd


class BotAnalyzer:
    def __init__(self, trades):
        self.df = trades.copy()

        if "Profit" not in self.df.columns:
            raise KeyError("Column 'Profit' is required")



    def profit_factor(self):
        """
        Profit Factor = sum(positive profits) / abs(sum(negative profits))
        """

        profits = self.df["Profit"]

        total_profit = profits[profits > 0].sum()
        total_loss = profits[profits < 0].sum()

        if total_loss == 0:
            return float("inf")

        return round(total_profit / abs(total_loss), 2)

#hola