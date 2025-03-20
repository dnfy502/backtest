import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def run_backtest(filename, initial_portfolio=1000, commission=0.15):
    # Loading data
    trade_report = pd.read_csv(filename)   # Trade Log data file
    signal = trade_report['signals']
    close = trade_report['close']
    datetime = trade_report['datetime']
    
    # Some lists to store data for future use
    trade_log = []   # Realised equity curve
    portfolio_curve = [] # Unrealised equity curve
    buy_and_hold_curve = []  # Benchmark curve
    pnl_log = []   # Profit and Loss made on each trade 
    
    # Initialising variables
    portfolio = initial_portfolio
    trade_log.append(float(portfolio))
    position = 0
    longs = 0
    shorts = 0

    # Calculate buy-and-hold once at the start for buy and hold return
    buy_and_hold_quantity = initial_portfolio / close[0]
    
    for i in range(len(trade_report)):
        # Buy and Hold curve
        buy_and_hold_curve.append(buy_and_hold_quantity * close[i])

        if signal[i] in (+1, -1, +2, -2):
            # Opening a long position
            if signal[i] == +1 and position == 0:
                position = 1
                longs += 1
                entry_price = close[i]
                charges = (commission * portfolio) / 100
                qty_bought = portfolio / entry_price
                portfolio_curve.append(round(float(portfolio), 2))

            # Opening a short position
            elif signal[i] == -1 and position == 0:
                position = -1
                shorts += 1
                entry_price = close[i]
                charges = (commission*portfolio)/100           
                qty_sold = portfolio/entry_price
                portfolio_curve.append(round(float(portfolio),2))
            
            # Closing long position
            elif signal[i] == -1 and position == 1:
                position = 0
                exit_price = close[i]
                pnl = (exit_price - entry_price) * qty_bought - charges
                pnl_log.append(pnl)
                portfolio += pnl
                trade_log.append(float(portfolio))
                portfolio_curve.append(round(float(portfolio),2))
            
            # Closing short position
            elif signal[i] == +1 and position == -1:
                position = 0
                exit_price = close[i]
                pnl = (entry_price - exit_price) * qty_sold - charges
                pnl_log.append(pnl)
                portfolio += pnl
                trade_log.append(float(portfolio))
                portfolio_curve.append(round(float(portfolio),2))
            
            # Switch from long to short
            elif signal[i] == -2:
                exit_price = close[i]
                pnl = (exit_price - entry_price) * qty_bought - charges
                pnl_log.append(pnl)
                portfolio += pnl
                trade_log.append(float(portfolio))

                position = -1
                shorts += 1
                entry_price = close[i]
                charges = (commission*portfolio)/100
                qty_sold = portfolio/entry_price
                portfolio_curve.append(round(float(portfolio),2))
            
            # Switch from short to long
            elif signal[i] == +2:
                exit_price = close[i]
                pnl = (entry_price - exit_price) * qty_sold - charges
                pnl_log.append(pnl)
                portfolio += pnl
                trade_log.append(float(portfolio))

                position = +1
                longs += 1
                charges = (commission*portfolio)/100
                entry_price = close[i]
                qty_bought = portfolio/entry_price
                portfolio_curve.append(round(float(portfolio),2))

        elif position == +1 and signal[i] == 0:
            unrealised_pnl = close[i]*qty_bought - portfolio
            portfolio_curve.append(round(float(portfolio+unrealised_pnl),2))

        elif position == -1 and signal[i] == 0:
            unrealised_pnl = -(close[i]*qty_sold - portfolio)
            portfolio_curve.append(round(float(portfolio+unrealised_pnl),2))
        else:
            portfolio_curve.append(round(float(portfolio),2))

    # Calculating metrics
    Initial_Balnce = initial_portfolio
    Final_balance = portfolio
    ROI = ((Final_balance - Initial_Balnce) / Initial_Balnce) * 100
    Benchmark_ROI = ((buy_and_hold_curve[-1] - buy_and_hold_curve[0])/buy_and_hold_curve[0]) * 100
    No_of_win_trades = len([i for i in pnl_log if i > 0])
    No_of_loss_trades = len(pnl_log) - No_of_win_trades
    Win_Rate = (No_of_win_trades / len(pnl_log)) * 100
    No_of_trades = longs + shorts
    No_of_longs = longs
    No_of_shorts = shorts
    Average_Win = np.mean([i for i in pnl_log if i > 0])
    Average_Loss = np.mean([i for i in pnl_log if i < 0])
    Total_Fees = sum((commission * value / 100) for value in trade_log[:-1])
    Max_Win = max(pnl_log)
    Max_Loss = min(pnl_log)
    Win_Rate_of_Longs = (len([pnl for pnl in pnl_log[:longs] if pnl > 0]) / longs) * 100
    Win_Rate_of_Shorts = (len([pnl for pnl in pnl_log[longs:] if pnl > 0]) / shorts) * 100


    # drawdown and ttr
    datetime2 = pd.to_datetime(datetime)
    time_period = (datetime2.iloc[1] - datetime2.iloc[0]).total_seconds() / 3600 / 24
    max_value = portfolio_curve[0]
    max_index = 0
    max_ttr = 0
    ttr_list = []
    max_drawdown_percent = 0
    for i in range(len(portfolio_curve)):
        if portfolio_curve[i] > max_value:
            max_value = portfolio_curve[i]
            max_index = i
        else:
            drawdown_percent = (max_value - portfolio_curve[i]) / max_value * 100
            if drawdown_percent > max_drawdown_percent:
                max_drawdown_percent = drawdown_percent

            current_ttr = i - max_index
            if current_ttr > max_ttr:
                ttr_list.append(current_ttr)
                max_ttr = current_ttr
    max_ttr = max_ttr * time_period
    avg_ttr = np.mean(ttr_list) * time_period

    # sharpe test
    abs_pnl = np.abs(pnl_log)
    mean_abs_pnl = np.mean(abs_pnl)
    average_pnl = np.mean(pnl_log)
    std_pnl = np.std(abs_pnl)
    sharpe = (mean_abs_pnl / std_pnl) 

    
    #Printing Metrics
    print(f'Initial Balance: {Initial_Balnce:.2f}$')
    print(f'Final Balance: {Final_balance:.2f}$')
    print(f'ROI: {ROI:.2f}%')
    print(f'Benchmark ROI: {Benchmark_ROI:.2f}%')
    print(f'Number of Trades: {No_of_trades}')
    print(f'Win Rate: {Win_Rate:.2f}%')
    print(f'Average Win: {Average_Win:.2f}$')
    print(f'Average Loss: {Average_Loss:.2f}$')
    print(f'Total Fees: {Total_Fees:.2f}$')
    print(f'Maximum Win: {Max_Win:.2f}$')
    print(f'Maximum Loss in a single trade: {Max_Loss:.2f}$')
    print(f'Number of Winning Trades: {No_of_win_trades}')
    print(f'Number of Losing Trades: {No_of_loss_trades}')
    print(f'Number of Long Trades: {No_of_longs}')
    print(f'Number of Short Trades: {No_of_shorts}')
    print(f'Win Rate of Long Trades: {Win_Rate_of_Longs:.2f}%')
    print(f'Win Rate of Short Trades: {Win_Rate_of_Shorts:.2f}%')
    print(f'Maximum Time to Recovery: {max_ttr} days')
    print(f'Average Time to Recovery: {avg_ttr:.2f} days')
    print(f'Maximum Drawdown Percent: {max_drawdown_percent:.2f}%')
    print(f'Sharpe Ratio: {sharpe:.2f}')


    # Plotting the curves
    fig = make_subplots(specs=[[{"secondary_y": False}]])

    fig.add_trace(go.Scatter(x=datetime, y=portfolio_curve, name="Portfolio Curve"),secondary_y=False)
    fig.add_trace(go.Scatter(x=datetime, y=buy_and_hold_curve, name="Buy and Hold Curve"),secondary_y=False)

    fig.update_layout(
        title="Backtesting Results",
        xaxis_title="Date",
        yaxis_title="Portfolio Value",
        template="plotly_dark"
    )

    fig.show()

def overfit_result(filename, initial_portfolio=1000, commission=0.15):
    # Loading data
    trade_report = pd.read_csv(filename)   # Trade Log data file
    signal = trade_report['signals']
    close = trade_report['close']
    datetime = trade_report['datetime']
    
    # Some lists to store data for future use
    trade_log = []   # Realised equity curve
    portfolio_curve = [] # Unrealised equity curve
    buy_and_hold_curve = []  # Benchmark curve
    pnl_log = []   # Profit and Loss made on each trade 
    
    # Initialising variables
    portfolio = initial_portfolio
    trade_log.append(float(portfolio))
    position = 0
    longs = 0
    shorts = 0

    # Calculate buy-and-hold once at the start for buy and hold return
    buy_and_hold_quantity = initial_portfolio / close[0]
    
    for i in range(len(trade_report)):
        # Buy and Hold curve
        buy_and_hold_curve.append(buy_and_hold_quantity * close[i])

        if signal[i] in (+1, -1, +2, -2):
            # Opening a long position
            if signal[i] == +1 and position == 0:
                position = 1
                longs += 1
                entry_price = close[i]
                charges = (commission * portfolio) / 100
                qty_bought = portfolio / entry_price
                portfolio_curve.append(round(float(portfolio), 2))

            # Opening a short position
            elif signal[i] == -1 and position == 0:
                position = -1
                shorts += 1
                entry_price = close[i]
                charges = (commission*portfolio)/100           
                qty_sold = portfolio/entry_price
                portfolio_curve.append(round(float(portfolio),2))
            
            # Closing long position
            elif signal[i] == -1 and position == 1:
                position = 0
                exit_price = close[i]
                pnl = (exit_price - entry_price) * qty_bought - charges
                pnl_log.append(pnl)
                portfolio += pnl
                trade_log.append(float(portfolio))
                portfolio_curve.append(round(float(portfolio),2))
            
            # Closing short position
            elif signal[i] == +1 and position == -1:
                position = 0
                exit_price = close[i]
                pnl = (entry_price - exit_price) * qty_sold - charges
                pnl_log.append(pnl)
                portfolio += pnl
                trade_log.append(float(portfolio))
                portfolio_curve.append(round(float(portfolio),2))
            
            # Switch from long to short
            elif signal[i] == -2:
                exit_price = close[i]
                pnl = (exit_price - entry_price) * qty_bought - charges
                pnl_log.append(pnl)
                portfolio += pnl
                trade_log.append(float(portfolio))

                position = -1
                shorts += 1
                entry_price = close[i]
                charges = (commission*portfolio)/100
                qty_sold = portfolio/entry_price
                portfolio_curve.append(round(float(portfolio),2))
            
            # Switch from short to long
            elif signal[i] == +2:
                exit_price = close[i]
                pnl = (entry_price - exit_price) * qty_sold - charges
                pnl_log.append(pnl)
                portfolio += pnl
                trade_log.append(float(portfolio))

                position = +1
                longs += 1
                charges = (commission*portfolio)/100
                entry_price = close[i]
                qty_bought = portfolio/entry_price
                portfolio_curve.append(round(float(portfolio),2))

        elif position == +1 and signal[i] == 0:
            unrealised_pnl = close[i]*qty_bought - portfolio
            portfolio_curve.append(round(float(portfolio+unrealised_pnl),2))

        elif position == -1 and signal[i] == 0:
            unrealised_pnl = -(close[i]*qty_sold - portfolio)
            portfolio_curve.append(round(float(portfolio+unrealised_pnl),2))
        else:
            portfolio_curve.append(round(float(portfolio),2))

    # Calculating metrics
    Initial_Balnce = initial_portfolio
    Final_balance = portfolio
    ROI = ((Final_balance - Initial_Balnce) / Initial_Balnce) * 100
    Benchmark_ROI = ((buy_and_hold_curve[-1] - buy_and_hold_curve[0])/buy_and_hold_curve[0]) * 100
    No_of_win_trades = len([i for i in pnl_log if i > 0])
    No_of_loss_trades = len(pnl_log) - No_of_win_trades
    Win_Rate = (No_of_win_trades / len(pnl_log)) * 100
    No_of_trades = longs + shorts
    No_of_longs = longs
    No_of_shorts = shorts
    Average_Win = np.mean([i for i in pnl_log if i > 0])
    Average_Loss = np.mean([i for i in pnl_log if i < 0])
    Total_Fees = sum((commission * value / 100) for value in trade_log[:-1])
    Max_Win = max(pnl_log)
    Max_Loss = min(pnl_log)
    Win_Rate_of_Longs = (len([pnl for pnl in pnl_log[:longs] if pnl > 0]) / longs) * 100
    Win_Rate_of_Shorts = (len([pnl for pnl in pnl_log[longs:] if pnl > 0]) / shorts) * 100


    # drawdown and ttr
    datetime2 = pd.to_datetime(datetime)
    time_period = (datetime2.iloc[1] - datetime2.iloc[0]).total_seconds() / 3600 / 24
    max_value = portfolio_curve[0]
    max_index = 0
    max_ttr = 0
    ttr_list = []
    max_drawdown_percent = 0
    for i in range(len(portfolio_curve)):
        if portfolio_curve[i] > max_value:
            max_value = portfolio_curve[i]
            max_index = i
        else:
            drawdown_percent = (max_value - portfolio_curve[i]) / max_value * 100
            if drawdown_percent > max_drawdown_percent:
                max_drawdown_percent = drawdown_percent

            current_ttr = i - max_index
            if current_ttr > max_ttr:
                ttr_list.append(current_ttr)
                max_ttr = current_ttr
    max_ttr = max_ttr * time_period
    avg_ttr = np.mean(ttr_list) * time_period

    # sharpe test
    abs_pnl = np.abs(pnl_log)
    mean_abs_pnl = np.mean(abs_pnl)
    average_pnl = np.mean(pnl_log)
    std_pnl = np.std(abs_pnl)
    sharpe = (mean_abs_pnl / std_pnl) 

    
    #Printing Metrics
    # print(f'Initial Balance: {Initial_Balnce:.2f}$')
    # print(f'Final Balance: {Final_balance:.2f}$')
    # print(f'ROI: {ROI:.2f}%')
    # print(f'Benchmark ROI: {Benchmark_ROI:.2f}%')
    # print(f'Number of Trades: {No_of_trades}')
    # print(f'Win Rate: {Win_Rate:.2f}%')
    # print(f'Average Win: {Average_Win:.2f}$')
    # print(f'Average Loss: {Average_Loss:.2f}$')
    # print(f'Total Fees: {Total_Fees:.2f}$')
    # print(f'Maximum Win: {Max_Win:.2f}$')
    # print(f'Maximum Loss in a single trade: {Max_Loss:.2f}$')
    # print(f'Number of Winning Trades: {No_of_win_trades}')
    # print(f'Number of Losing Trades: {No_of_loss_trades}')
    # print(f'Number of Long Trades: {No_of_longs}')
    # print(f'Number of Short Trades: {No_of_shorts}')
    # print(f'Win Rate of Long Trades: {Win_Rate_of_Longs:.2f}%')
    # print(f'Win Rate of Short Trades: {Win_Rate_of_Shorts:.2f}%')
    # print(f'Maximum Time to Recovery: {max_ttr} days')
    # print(f'Average Time to Recovery: {avg_ttr:.2f} days')
    # print(f'Maximum Drawdown Percent: {max_drawdown_percent:.2f}%')
    # print(f'Sharpe Ratio: {sharpe:.2f}')

    return round(float(Final_balance),2), round(Win_Rate,2), round(max_drawdown_percent,2)

if __name__ == '__main__':
    run_backtest('results.csv')