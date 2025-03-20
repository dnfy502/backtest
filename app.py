import os
import pandas as pd
import numpy as np
import plotly.graph_objs as go
import plotly
import json
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file and file.filename.endswith('.csv'):
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)
        
        # Run backtesting on the uploaded file
        results, chart_json = run_backtest(filepath)
        return jsonify({'results': results, 'chart': chart_json})
    
    return jsonify({'error': 'Invalid file format. Please upload a CSV file.'}), 400

def run_backtest(filename, initial_portfolio=1000, commission=0.15):
    # Load data
    trade_report = pd.read_csv(filename)
    
    signal = trade_report['signals']
    open_p = trade_report['open']
    high = trade_report['high']
    low = trade_report['low']
    close = trade_report['close']
    datetime = trade_report['datetime']
    
    trade_log = []   # Realised equity curve
    pnl_log = []     
    portfolio_curve = [] # Unrealised equity curve
    buy_and_hold_curve = []  # Benchmark curve
    
    # Backtest logic
    portfolio = initial_portfolio
    trade_log.append(int(portfolio))
    position = 0
    longs = 0
    shorts = 0

    # Calculate buy-and-hold once at the start
    holding_qty = initial_portfolio / close[0]
    
    for i in range(len(trade_report)):
        # Update buy-and-hold value
        buy_and_hold_curve.append(holding_qty * close[i])

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
                trade_log.append(int(portfolio))
                portfolio_curve.append(round(float(portfolio),2))
            
            # Closing short position
            elif signal[i] == +1 and position == -1:
                position = 0
                exit_price = close[i]
                pnl = (entry_price - exit_price) * qty_sold - charges
                pnl_log.append(pnl)
                portfolio += pnl
                trade_log.append(int(portfolio))
                portfolio_curve.append(round(float(portfolio),2))
            
            # Switch from long to short
            elif signal[i] == -2:
                exit_price = close[i]
                pnl = (exit_price - entry_price) * qty_bought - charges
                pnl_log.append(pnl)
                portfolio += pnl
                trade_log.append(int(portfolio))

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
                trade_log.append(int(portfolio))

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
    
    # Calculate metrics
    Final_Balance = portfolio
    No_of_trades = len(trade_log)-1
    Min_Balance = min(trade_log)
    Max_Balance = max(trade_log)
    ROI = ((portfolio - initial_portfolio)/initial_portfolio)*100
    Total_fees = sum((commission * value / 100) for value in trade_log[:-1])
    
    if pnl_log:  # Check if there are any trades
        Maximum_PNL = max(pnl_log)
        Minimum_PNL = min(pnl_log)
        Winning_Trades = sum(1 for pnl in pnl_log if pnl > 0)
        
        if Winning_Trades > 0:
            Average_win = sum(pnl for pnl in pnl_log if pnl > 0) / Winning_Trades
        else:
            Average_win = 0
            
        Losing_Trades = len(pnl_log) - Winning_Trades
        
        if Losing_Trades > 0:
            Average_loss = sum(pnl for pnl in pnl_log if pnl < 0) / Losing_Trades
        else:
            Average_loss = 0
            
        Win_Rate = (Winning_Trades/len(pnl_log))*100
    else:
        Maximum_PNL = Minimum_PNL = Average_win = Average_loss = Win_Rate = 0
        Winning_Trades = Losing_Trades = 0
    
    Benchmark_Return = ((close[len(close)-1] - close[0]) / close[0]) * 100
    Benchmark_Balance = initial_portfolio + (Benchmark_Return * initial_portfolio)/100
    
    if No_of_trades > 0:
        Average_Return = (Final_Balance-initial_portfolio)/No_of_trades
    else:
        Average_Return = 0

    # Create results dictionary
    results = {
        'Initial_Balance': initial_portfolio,
        'Final_Balance': round(Final_Balance, 2),
        'Benchmark_Portfolio': round(Benchmark_Balance, 2),
        'Net_Profit': round(ROI, 2),
        'Benchmark_Return': round(Benchmark_Return, 2),
        'No_of_Trades': No_of_trades,
        'Average_Return': round(Average_Return, 2),
        'Winning_Trades': Winning_Trades,
        'Losing_Trades': Losing_Trades,
        'Win_Rate': round(Win_Rate, 2),
        'Max_Balance': round(Max_Balance, 2),
        'Min_Balance': round(Min_Balance, 2),
        'Max_Win': round(Maximum_PNL, 2),
        'Max_Loss': round(Minimum_PNL, 2),
        'Average_Win': round(Average_win, 2),
        'Average_Loss': round(Average_loss, 2),
        'Total_Fees': round(Total_fees, 2),
        'Long_Trades': longs,
        'Short_Trades': shorts
    }
    
    # Create aligned realized PNL array for plotting
    time_axis = list(datetime)
    realised_pnl = [trade_log[0]] * len(time_axis)
    tl_idx = 1
    
    for i in range(1, len(time_axis)):
        if tl_idx < len(trade_log) and signal[i] in (+1, -1, +2, -2):
            realised_pnl[i] = trade_log[tl_idx]
            tl_idx += 1
        else:
            realised_pnl[i] = realised_pnl[i-1]

    # Create Plotly figure
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=time_axis, y=buy_and_hold_curve, mode='lines', name='Buy & Hold'))
    fig.add_trace(go.Scatter(x=time_axis, y=portfolio_curve, mode='lines', name='Unrealised PNL'))
    fig.add_trace(go.Scatter(x=time_axis, y=realised_pnl, mode='lines', name='Realised PNL'))
    
    fig.update_layout(
        title='Backtest Results',
        xaxis_title='Datetime',
        yaxis_title='Value',
        hovermode='x unified'
    )
    
    # Convert the plot to JSON for web display
    chart_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    
    return results, chart_json

if __name__ == '__main__':
    app.run(debug=True)