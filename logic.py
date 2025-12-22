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
        
<<<<<<< HEAD
        return round(total_profit / abs(total_loss), 2)
=======
        return round(total_profit / abs(total_loss), 2)













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
>>>>>>> 090e82f (add firts class)
