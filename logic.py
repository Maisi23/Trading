import pandas as pd

#! Las funciones de métricas NUNCA crean columnas
#! Las funciones de transformación NUNCA calculan métricas

class BotAnalyzer:
    def __init__(self,trades:pd.DataFrame):
        
        self.df = trades.copy()

      
        if not isinstance(self.df,pd.DataFrame):
            raise TypeError("Input must be a pandas DataFrame")

        required = {"Profit"}

        if not required.issubset(self.df.columns):
            raise KeyError("Column 'Profit' and are required")

    @property
    def edge_portfolio_R(self):
        return self.edge_R(self.df)
    
    @property
    def summary(self):
        summary_dict = {
            "Profit Factor (R)": self.profit_factor(self.df),
            "Expectancy (R)": self.edge_portfolio_R,
            "Max Drawdown (R)": self.maxDD_R(self.df),
            "Rates (%)": self.win_rate(self.df),
            "Payoff Ratio (R)": self.payoff_ratio(self.df)
        }
        return summary_dict


    @staticmethod
    def profit_factor(df:pd.DataFrame):
        """
        Note: No considered in the calculation a trade as profit if R_multiple < 0.05 (BE)
        #* Profit Factor =  sum(R+) 
        #*                  --------------------------
        #*                  | sum(R-) |
        
        """
        BE_THRESHOLD = 0.05

        #Check if R_multiple column exists
     
        if "R_multiple" not in df.columns:
            raise KeyError("Column 'R_multiple' is required")
        

        #Select R_multiple column
        r = df["R_multiple"]
        

        #Calculate total R+ and R-

        r_positive = r[r >= BE_THRESHOLD].sum()
        r_negative = r[r < BE_THRESHOLD].sum()

        #Handle division by zero
        if r_negative == 0:
            return float("inf")
        

        result = float(round(r_positive / abs(r_negative), 2))

        return result

    @staticmethod
    def edge_R(df:pd.DataFrame) -> float:
        """
        Expectancy in R = mean(R)
        """
        if "R_multiple" not in df.columns:
            raise KeyError("Column 'R_multiple' is required")
        

        result = float(round(df["R_multiple"].mean(),2))
        
        return result
    
    @staticmethod
    def maxDD_R(df:pd.DataFrame) -> float:
        """
        Max Drawdown in R_multiple
        """

        assert "R_multiple" in df.columns, "Column 'R_multiple' is required"       
        
        r = df["R_multiple"]

        equity = BotAnalyzer.equity_R_curve(df)

        peak = equity.cummax()
        
        dd_in_R = equity - peak
        
        return float(round(dd_in_R.min(),2))
     
    @staticmethod
    def win_rate(df:pd.DataFrame,BE = False):
        """
        Rate = n°(wins|loss|BE) / total trades * 100
        Note: A trade is considered BE when profit is less than 0.05 R_multiple
        """
        if "R_multiple" not in df.columns:
            raise KeyError("Column 'R_multiple' is required")
        BE_THRESHOLD = 0.05
        temp_df= df.copy()
        percent = lambda x: round(x*100/total,2)  

        total = temp_df["Profit"].count()
        if total==0: return 0

    
        base_dict = {}
        
        if BE:
            win = (temp_df["R_multiple"] > BE_THRESHOLD).sum()
            breakeven = (
                (temp_df["R_multiple"] <= BE_THRESHOLD) & 
                (temp_df["R_multiple"] > 0)
            ).sum()

            losses = (temp_df["Profit"] < 0 ).sum()

            base_dict.update({
                              "Win":float(percent(win)),
                              "Loss":float(percent(losses)),
                              "BE":float(percent(breakeven))
                              })    

        else:
            win = (temp_df["R_multiple"] > 0).sum()
            losses = (temp_df["R_multiple"] <= 0 ).sum()
            base_dict.update({
                              "Win":float(percent(win)),
                              "Loss":float(percent(losses))
                              })

        
        #Adding total 
        base_dict["Total"] = int(total)


        return base_dict

    @staticmethod
    def payoff_ratio(df:pd.DataFrame):
        """
        Payoff Ratio = Mean Profit / Mean Loss
        """
        if "R_multiple" not in df.columns:
            raise KeyError("Column 'R_multiple' is required")
        r = df["R_multiple"]
        mean_profit = r[r > 0].mean()
        mean_loss = r[r <= 0].mean()
        result = float(round(mean_profit / abs(mean_loss),2)) 
        return result


    @staticmethod
    def equity_R_curve(df):
        """
        Returns a pandas Series representing the equity curve in R_multiple
        """
        assert "R_multiple" in df.columns, "Column 'R_multiple' is required"
        
        r = df["R_multiple"]
        equity_curve = r.cumsum().round(2)
        return equity_curve
    
    @staticmethod
    def avg_DD_R(df):
        """
        Average Drawdown in R_multiple
        """
        equity = BotAnalyzer.equity_R_curve(df)
        peak = equity.cummax()
        max_dd_in_R = equity - peak
        avg_dd = max_dd_in_R.mean()
        
        return float(round(avg_dd,2))
    


    def _point_value(self):

        # copy dataframe to avoid modifying original

        temp_df = self.df.copy()
        
        #*Fomula point value    =        |Profit|
        # *                          ----------------------------
        #  *                         |P.Entry-P.Exit|*Volume 
        
        temp_df["point_value"] = temp_df["Profit"].abs()/((temp_df["Price Entry"]-temp_df["Price Exit"]).abs()*temp_df["Volume"])
        
        #create dictionary with median point value per symbol

        point_value_dict = dict(temp_df.groupby("Symbol")["point_value"].median().round(2))
       
        return point_value_dict
    
    
    
    def add_R(self):
        
        # copy dataframe to avoid modifying original
        temp_df = self.df.copy()
        
        #R_multiple is column already?
        if "R_multiple" in temp_df.columns:
            return self

        #Drop trades without initial stop loss
        
        temp_df= temp_df.drop(temp_df[temp_df["S / L"] ==0].index)
        temp_df = temp_df.reset_index(drop=True)
    

        pv = self._point_value()

        #* Formula R(usd): |P.Entry-SL|* Volumen* point_value
        
        r_usd = abs(temp_df["Price Entry"] - temp_df["S / L"]) * temp_df["Volume"] * temp_df["Symbol"].map(pv)
         
        # Create a new column 'R(usd)' in the DataFrame

        temp_df["R(usd)"] = r_usd.round(2)
        
        #* Formula R_multiple: Profit / R(usd)

        temp_df["R_multiple"] = (temp_df["Profit"]/temp_df["R(usd)"]).round(2)
        
        # Assign back to self.df for return a BotAnalyzer object 

        self.df = temp_df

        return self
            
    def montecarlo(self):
        """
        Shuflle Montecarlo on R_multiples
        """
        pass
    
    def trim_n_percentile(self,lower_q=0.01,upper_q=0.99):
        """
        Warning: If the min of R is -1 then no lossing trade will be trim 

        :param lower_q: Lower percentile 
        :param upper_q: Higher percentile permited 
        """
        df = self.df.copy()
        
        assert "R_multiple" in df.columns, "Column R_multiple is required"


        r = df["R_multiple"]
        #lower percentil and upper percentile
        lo, hi = r.quantile([lower_q,upper_q])
        
        df = df[r.between(lo,hi)].reset_index(drop=True)
       
        self.df = df

        return self







    
    def trim_per_extreme_values(self,percent:float = 0.01):
        """
        Drop the percentaje indicate of trades from each side distribution
        """
        df = self.df.copy()
        
        assert "R_multiple" in df.columns, "R_multiple is required"

        #Delete n trades
        n = int(round(percent*len(df),0))
        
        #Get index of max trades
        idx_max = df.R_multiple.nlargest(n).index
        #Get index of min trades
        idx_min = df.R_multiple.nsmallest(n).index

        idx_total = idx_max.union(idx_min)
        df = df.drop(idx_total).reset_index(drop=True)

        self.df = df
        
        return self

        

















"""def balance_in_R(data:pd.DataFrame,RISK:float = 0.01,grafic:bool = False):
    
    # * Formula: Balance_n = Balance_0 * PRODUCTORIO(1 + R_n* RISK) 

    #Interior del Productorio
    data["growth"] = 1+ data["R"]*RISK
    
    #Toda la Formula
    data["Equity"] = (INITIAL_BALANCE *data["growth"].cumprod()).round(2)
    
    # if grafic:
    #     graf = data["Balance"].plot(kind="line",xlabel="n Operaciones",ylabel="Balance")
    #     return graf
    
    return data[data.columns[-6:]]

"""