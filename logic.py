import re
from unittest import result
from numpy import empty
import pandas as pd

#! Las funciones de métricas NUNCA modifican permanentemente las columnas
#! Las funciones de transformación NUNCA calculan métricas

# @property
# def edge_portfolio(self):
    # return .edge_R(self.df)


# def summary(self):
#     summary_dict = {
#         "Profit Factor ": self.profit_factor(self.df),
#         # "Expectancy ": self.edge_portfolio,
#         "Max Drawdown ": self.maxDD_R(self.df),
#         "Rates (%)": self.win_rate(self.df),
#         "Payoff Ratio ": self.payoff_ratio(self.df)
#     }
#     return summary_dict



#!------- Metrics fuctions---------
def profit_factor(serie: pd.Series,BE_THRESHOLD = 0.0):
    """
    Note: No considered in the calculation a trade as profit if {serie} < BE_THRESHOLD 

    Profit Factor =  sum(profits) / |sum(losses)|
    """
    #Check the argument is pd.serie
    _handle_series(serie)


    #Calculate total positive and total negative

    positive = serie[serie >= BE_THRESHOLD].sum()
    negative = serie[serie < BE_THRESHOLD].sum()

    #Handle division by zero
    if negative == 0:
        return float("inf")


    result = float(round(positive / abs(negative), 2))

    return result

def expectancy(serie)-> float: 
    """
    Expectancy = (%wins * avg wins) - (%losses * avg losses)
    """
    #Check the argument is pd.serie
    _handle_series(serie)
    
    #Get rates in percent
    win_rate_dict = win_rate(serie,BE_THRESHOLD=0.0)
    
    #Get wins and losses
    wins = win_rate_dict["Win"]/100
    losses = win_rate_dict["Loss"]/100
    
    #Calculate expectancy
    expectancy = wins*avg_win(serie) - losses*avg_loss(serie)

    return expectancy

def expectancy_R(df:pd.DataFrame) -> float:
    """
    Expectancy = mean(R_multiple)
    """
    #Check the argument is pd.DataFrame
    _handle_df(df)
    
    #Check if R_multiple column
    if "R_multiple" not in df.columns:
        raise ValueError("Function expect a R_multiple column")
    
    
    result = float(round(df["R_multiple"].mean(),2))

    return result

def max_dd(serie) -> float:
    """
    Max Drawdown all time
    """

    #Check the argument is pd.serie
    _handle_series(serie)

    equity = equity_curve(serie)

    peak = equity.cummax()

    dd = equity - peak

    return float(round(dd.min(),2))

def win_rate(serie:pd.Series,BE_THRESHOLD = 0.0)->dict:
    """
    Rate = n°(wins|loss|BE) / total trades * 100

    Note: A trade is considered BE when profit is less than BE_THRESHOLD
    """
    #Check the argument is pd.serie
    _handle_series(serie)
    
    serie= serie.copy()
    percent = lambda x: round(x*100/total,2)  

    total = serie.count()
    if total==0: return dict({"Total":0})


    base_dict = {}


    if BE_THRESHOLD:
        win = (serie > BE_THRESHOLD).sum()
        breakeven = (
            (serie<= BE_THRESHOLD) & 
            (serie > 0)
        ).sum()

        losses = (serie < 0 ).sum()

        base_dict.update({
                          "Win":float(percent(win)),
                          "Loss":float(percent(losses)),
                          "BE":float(percent(breakeven))
                          })    

    else:
        win = (serie > 0).sum()
        losses = (serie <= 0 ).sum()
        base_dict.update({
                          "Win":float(percent(win)),
                          "Loss":float(percent(losses))
                          })




        

    #Adding total 
    base_dict["Total"] = int(total)


    return base_dict

def payoff_ratio(serie:pd.Series)-> float:
    """
    Payoff Ratio = Mean Profit / Mean Loss
    """
    #check the argument is pd.DataFrame
    _handle_df(serie)

    mean_profit = serie[serie > 0].mean()
    mean_loss = serie[serie <= 0].mean()

    result = float(round(mean_profit / abs(mean_loss),2)) 
    return result

def equity_curve(serie:pd.Series)-> pd.Series:
    """
    Returns a pandas Series representing the balance curve 
    """
    #Check the argument is pd.serie
    _handle_series(serie)

    equity_curve = serie.cumsum().round(2)

    return equity_curve

def avg_DD(serie:pd.Series)-> float:
    """
    Average Drawdown 
    """
    #Check the argument is pd.serie
    _handle_series(serie)

    equity = equity_curve(serie)

    peak = equity.cummax()
    max_dd = equity - peak
    avg_dd = max_dd.mean()

    return float(round(avg_dd,2))

def avg_win(serie:pd.Series)-> float:
    """
    Average Win
    """
    #Check the argument is pd.serie
    _handle_series(serie)
    #handle nan
    if len(serie[serie>0])==0 : return 0
    
    result = float(round(serie[serie>0].mean(),2))

    return result 

def avg_loss(serie:pd.Series)-> float:
    """
    Average Loss in module
    """
    #Check the argument is pd.serie
    _handle_series(serie)
    #handle nan
    if len(serie[serie<0])==0 : return 0

    result = abs(float(round(serie[serie<0].mean(),2)))
    return result




#!----- transform functions---------
def add_R(df:pd.DataFrame):
    """
    Add R_multiple column to dataframe
    Trades without initial stop loss are dropped
    """

    #check the argument is pd.DataFrame
    _handle_df(df)

    # copy dataframe to avoid modifying original
    temp_df = df.copy()
    
    #R_multiple is column already?
    if "R_multiple" in temp_df.columns:
        return df

    #Save trades without sl just in case its required
    without_sl = temp_df[temp_df["S / L"] ==0]
    
    #Drop trades without initial stop loss
    temp_df= temp_df.drop(temp_df[temp_df["S / L"] ==0].index)
    temp_df = temp_df.reset_index(drop=True)


    pv = _point_value(df)

    #* Formula R(usd): |P.Entry-SL|* Volumen* point_value

    r_usd = abs(temp_df["Price Entry"] - temp_df["S / L"]) * temp_df["Volume"] * temp_df["Symbol"].map(pv)
     
    # Create a new column 'R(usd)' in the DataFrame

    temp_df["R(usd)"] = r_usd.round(2)

    #* Formula R_multiple: Profit / R(usd)

    temp_df["R_multiple"] = (temp_df["Profit"]/temp_df["R(usd)"]).round(2)

    # Assign back to self.df for return a BotAnalyzer object 

    

    return temp_df
        

def trim_n_percentile(df:pd.DataFrame,column:str,lower_q=0.01,upper_q=0.99):
    """
    Drop the percentile indicate of trades
    :param lower_q: Lower percentile 
    :param upper_q: Higher percentile permited 
    """
    #check the argument is pd.dataframe
    _handle_df(df)
    temp_df = df.copy()

    temp_col = temp_df[column]

    #lower percentil and upper percentile
    lo, hi = temp_col.quantile([lower_q,upper_q])

    df = df[temp_col.between(lo,hi)].reset_index(drop=True)

    return df

def trim_per_extreme_values(df:pd.DataFrame,column:str,percent:float = 0.01):
    """
    Drop the percentaje indicate of trades from each side distribution
    """

    #check the argument is pd.dataframe
    _handle_df(df)
    
    temp_df = df.copy()

    #Delete n trades
    n = int(round(percent*len(temp_df),0))

    #Get index of max trades
    idx_max = temp_df[column].nlargest(n).index
    #Get index of min trades
    idx_min = temp_df[column].nsmallest(n).index

    idx_total = idx_max.union(idx_min)
    temp_df = temp_df.drop(idx_total).reset_index(drop=True)
   
    return temp_df

def montecarlo(self):
    """
    Shuflle Montecarlo on R_multiples
    """
    pass



#!----- aux functions-----
def _point_value(df:pd.DataFrame):

    #check the argument is pd.DataFrame
    _handle_df(df)

    # copy dataframe to avoid modifying original
    
    temp_df = df.copy()

    #*Fomula point value    =        |Profit|
    # *                          ----------------------------
    #  *                         |P.Entry-P.Exit|*Volume 

    temp_df["point_value"] = temp_df["Profit"].abs()/((temp_df["Price Entry"]-temp_df["Price Exit"]).abs()*temp_df["Volume"])

    #create dictionary with median point value per symbol

    point_value_dict = dict(temp_df.groupby("Symbol")["point_value"].median().round(2))

    return point_value_dict

def _handle_df(df):
    if not isinstance(df,pd.DataFrame):
        raise ValueError(f"Function expect a {pd.DataFrame}")

def _handle_series(serie):
    if not isinstance(serie,pd.Series):
        raise ValueError(f"Function expect a {pd.Series}")


