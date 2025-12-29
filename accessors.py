import pandas as pd
from pandas.api.extensions import register_dataframe_accessor

from logic import * 

@register_dataframe_accessor("bt")
class BotAnalyzer:
    def __init__(self, df:pd.DataFrame):
        self._df = df

    # -------- helpers --------
    def _check_col(self, col: str):
        if col not in self._df.columns:
            raise KeyError(f"Column '{col}' not found")
    
    # -------- properties --------
    @property
    def expectancy_R(self):
        return expectancy_R(self._df)
    

    # -------- metrics functions --------
    def profit_factor(self,col: str)->float:
        return profit_factor(self._df[col])
    
    def expectancy(self,col: str)->float:
        return expectancy(self._df[col])
   
    def max_dd(self,col: str)->float:
        return max_dd(self._df[col])
    
    def win_rate(self,col: str,BE_THRESHOLD:float = 0.0)->dict:
        return win_rate(self._df[col],BE_THRESHOLD)
    
    def payoff_ratio(self,col: str)->float:
        return payoff_ratio(self._df[col])
    
    def avg_DD(self,col: str)->float:
        return avg_DD(self._df[col])
    
    def avg_win(self,col: str)->float:
        return avg_win(self._df[col])
    
    def avg_loss(self,col: str)->float:
        return avg_loss(self._df[col])
    


    #-------- transform functions --------
    def trim_n_percentile(self,col: str,lower_q: float = 0.01,upper_q: float = 0.99)->pd.DataFrame:
        return trim_n_percentile(self._df,col,lower_q,upper_q)
    
    def trim_per_extreme_values(self,col: str,percent: float = 0.01)->pd.DataFrame:
        return trim_per_extreme_values(self._df,col,percent)
    
    def add_R(self)->pd.DataFrame:
        """
        Docstring for add_R
        
        :param self: Description
        :return: Description
        :rtype: DataFrame
        """
        return add_R(self._df)
    
    