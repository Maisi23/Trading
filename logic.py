import pandas as pd

#! Las funciones de métricas NUNCA crean columnas
#! Las funciones de transformación NUNCA calculan métricas

class BotAnalyzer:
    def __init__(self,trades:pd.DataFrame,initial_balance=5000,risk=0.01):
        
        self.df = trades.copy()

      
        if not isinstance(self.df,pd.DataFrame):
            raise TypeError("Input must be a pandas DataFrame")

        required = {"Profit"}

        if not required.issubset(self.df.columns):
            raise KeyError("Columns 'Profit' and are required")

    @staticmethod
    def win_rate(df:pd.DataFrame,BE = False):
        """
        Rate = n°(wins|loss|BE) / total trades * 100
        Note: A trade is considered BE when profit is less than 0.05 R-multiple
        """
        BE_THRESHOLD = 0.05
        temp_df= df.copy()
        percent = lambda x: round(x*100/total,2)  

        total = temp_df["Profit"].count()
        if total==0: return 0

    
        base_dict = {}
        
        if BE:
            win = (temp_df["R-multiple"] > BE_THRESHOLD).sum()
            breakeven = (
                (temp_df["R-multiple"] <= BE_THRESHOLD) & 
                (temp_df["R-multiple"] > 0)
            ).sum()

            losses = (temp_df["Profit"] < 0 ).sum()

            base_dict.update({
                              "Win":[f"{percent(win)}%",win],
                              "Loss":[f"{percent(losses)}%",losses],
                              "BE":[f"{percent(breakeven)}%",breakeven]
                              })    

        else:
            win = (temp_df["R-multiple"] > 0).sum()
            losses = (temp_df["R-multiple"] <= 0 ).sum()
            base_dict.update({
                              "Win":[f"{percent(win)}%",win],
                              "Loss":[f"{percent(losses)}%",losses]
                              })

        
        #Adding total 
        base_dict["Total"] = ["100%", total]


        return pd.DataFrame(base_dict,index=["Percent","n"])

    @staticmethod
    def profit_factor(df:pd.DataFrame):
        """
        Note: No considered in the calculation a trade as profit if R-multiple < 0.05 (BE)
        #* Profit Factor =  sum(R+) 
        #*                  --------------------------
        #*                  | sum(R-) |
        
        """
        BE_THRESHOLD = 0.05

        #Check if R-multiple column exists
     
        if "R-multiple" not in df.columns:
            raise KeyError("Column 'R-multiple' is required")
        

        #Select R-multiple column
        r = df["R-multiple"]
        

        #Calculate total R+ and R-

        r_positive = r[r >= BE_THRESHOLD].sum()
        r_negative = r[r < BE_THRESHOLD].sum()

        #Handle division by zero
        if r_negative == 0:
            return float("inf")
        

        result = round(r_positive / abs(r_negative), 5)

        return result

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
        
        #R-multiple is column already?
        if "R-multiple" in temp_df.columns:
            return self

        #Drop trades without initial stop loss
        
        temp_df= temp_df.drop(temp_df[temp_df["S / L"] ==0].index)
        temp_df = temp_df.reset_index(drop=True)
    

        pv = self._point_value()

        #* Formula R(usd): |P.Entry-SL|* Volumen* point_value
        
        r_usd = abs(temp_df["Price Entry"] - temp_df["S / L"]) * temp_df["Volume"] * temp_df["Symbol"].map(pv)
         
        # Create a new column 'R(usd)' in the DataFrame

        temp_df["R(usd)"] = r_usd.round(2)
        
        #* Formula R-multiple: Profit / R(usd)

        temp_df["R-multiple"] = (temp_df["Profit"]/temp_df["R(usd)"]).round(2)
        
        # Assign back to self.df for return a BotAnalyzer object 

        self.df = temp_df

        return self
            
    @staticmethod
    def expectancy_R(df:pd.DataFrame) -> float:
        """
        Expectancy in R = mean(R)
        """
        if "R-multiple" not in df.columns:
            raise KeyError("Column 'R-multiple' is required")
        

        result = round(df["R-multiple"].mean(),2)
        
        return result
    
    @staticmethod
    def maxDD_R(df:pd.DataFrame) -> float:
        """
        Max Drawdown in R-multiple
        """

        if "R-multiple" not in df.columns:
            raise KeyError("Column 'R-multiple' is required")
       
        r = df["R-multiple"]

        balance_n = r.cumsum() 
        peak = balance_n.cummax()
        dd_in_R = balance_n - peak
        return round(dd_in_R.min(),2)
     
    








# def get_bots_by_comment():
#     return df["Comment"].unique()

# def handle_errors_not_string_and_not_in_df(x):
#      #Verificicar que sea none para no entrar en el if y que sea una string 
#     if x is not None:
#         if  not isinstance(x,str) :
#             raise TypeError(f"{x} no es una string")
    
#         #Conseguir los bots por comentario del df y verificar si bot se encuentra
#         if x not in get_bots_by_comment():
#             raise KeyError(f"{x} no está en el dataframe")    
        

"""

def profit_factor_v2(data,by_bot=True):
    
    #Profit factor por bot
    if by_bot:
        x = data.groupby("Comment")        

        return x.apply(profit_factor_v2,by_bot=False,include_groups=False) #type: ignore


    total_profit = data[data["Profit"]>=0]["Profit"].sum()
    total_loss = data[data["Profit"]< 0]["Profit"].sum()

    #Division por 0
    if total_loss==0:
        return float('inf')
    

    return round(abs(total_profit/total_loss),2)


def win_rate(data:pd.DataFrame,by_bot = False,BE = True):
    
    Calcula los ratios para los bots o para el total de la cuenta
    Se puede desactivar el calculo con BE y hacerlo normal

    Nota: Se considera BE cuando el profit fue menor que el 0.15% del balance actual
    

    #data es un dataframe?
    if not isinstance(data,pd.DataFrame):
        raise TypeError("data is not a Dataframe")
    
    #Profit y balance son columnas necesarias para el calculo, están?
    if "Profit" not in data.columns or "Balance" not in data.columns:
        raise KeyError("Columns 'Profit' or 'Balance' is not in your dataframe")

  

    #Calculo
    total = data["Profit"].count()

    percent = lambda x: round(x*100/total,2)  

    win = ((data["Profit"] > 0) & (data["Profit"] > data["Balance"]*0.0015)).sum() 
    win_percent = percent(win)

    losses = (data["Profit"] < 0 ).sum()
    losses_percent = percent(losses)
    
    #Diccionario base
    dicc =  {"Win":[f"{win_percent}%",win],
            "Loss":[f"{losses_percent}%",losses]}

    #Queres los breakeven?
    if BE:
        breakeven =  ((data["Profit"] < data["Balance"]*0.0015) & (data["Profit"] > 0)).sum()
        breakeven_percent = percent(breakeven)

        dicc["BE"] = [f"{breakeven_percent}%",breakeven]
    
    #Añado el total
    
    dicc["Total"] = ["100%", total]


    #Para cada bot
    if by_bot:
        x = data.groupby("Comment")[["Profit","Balance"]]
        return x.apply(win_rate,BE=BE)
    

    return pd.DataFrame(dicc,index=["Percent","n"])

def point_value(data_for_point_value:pd.DataFrame):

    temp_df = data_for_point_value.copy()
    
    #*Calculo valor del punto =        |Profit|
    # *                          ----------------------------
    #  *                         |P.Entry-P.Exit|*Volume 
    
    temp_df["point_value"] = temp_df["Profit"].abs()/((temp_df["Price Entry"]-temp_df["Price Exit"]).abs()*temp_df["Volume"])
    
    df_return = dict(temp_df.groupby("Symbol")["point_value"].median().round(2))
   
    return df_return


def add_R(data_R:pd.DataFrame):
    if "R" in data_R.columns:
        return None
    
    for i in point_value(data_R):
        
        #* Calculo R(usd): |P.Entry-SL|*Volumen*point_value

        #Operaciones sin stop inicial deben ser tratadas con otro criterio 
     
        func = abs(data_R["Price Entry"] - data_R.loc[data_R["S / L"]>0,"S / L"])*data_R["Volume"]*point_value(data_R)[i]
        
        data_R.loc[data_R["Symbol"]==i,"R(usd)"] = func.round(2)
    
    data_R["R"] = (data_R["Profit"]/data_R["R(usd)"]).round(2)

    #Se rellenan con inf las operaciones sin stops iniciales
    data_R.fillna(0.0,inplace=True)
        
    return data_R 

def balance_in_R(data:pd.DataFrame,RISK:float = 0.01,grafic:bool = False):
    
    # * Formula: Balance_n = Balance_0 * PRODUCTORIO(1 + R_n* RISK) 

    #Interior del Productorio
    data["growth"] = 1+ data["R"]*RISK
    
    #Toda la Formula
    data["Equity"] = (INITIAL_BALANCE *data["growth"].cumprod()).round(2)
    
    # if grafic:
    #     graf = data["Balance"].plot(kind="line",xlabel="n Operaciones",ylabel="Balance")
    #     return graf
    
    return data[data.columns[-6:]]


def max_drawdown_in_R(data:pd.DataFrame):
    if "R" not in data.columns: 
        add_R(data)
        print("Columna R añadida")
    
    data["R"]= data["R"].fillna(0)

    balance_n = data["R"].cumsum() 
    peak = balance_n.cummax()
    dd_in_R = balance_n - peak
    return dd_in_R.min() 
"""

