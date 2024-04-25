import pandas as pd
import pandas_ta as ta
from tqdm import tqdm
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
from backtesting import Strategy
from backtesting import Backtest
import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
import yfinance as yf

tqdm.pandas()


def download_data(symbol, period, interval):
    tickerData = yf.Ticker(symbol)
    tickerDf = tickerData.history(
        period=period,
        interval=interval,
    )
    tickerDf = tickerDf[tickerDf.High != tickerDf.Low]
    tickerDf.to_csv(f"../data/{symbol.lower()}-{period}-{interval}.csv")
    return tickerDf


def read_data(symbol, period, interval):
    data = pd.read_csv(f'../data/{symbol}-{period}-{interval}.csv')
    data.Datetime = pd.to_datetime(data.Datetime, utc=True)
    data.set_index('Datetime', inplace=False)
    data.drop(['Dividends', 'Stock Splits', 'Volume'], axis=1, inplace=True)
    return data


def set_ema(data, ema_length):
    data['EMA'] = ta.ema(data.Close, length=ema_length)
    return data


def set_macd(data):
    macd = ta.macd(data.Close)
    data['MACD'] = macd.loc[:, 'MACD_12_26_9']
    data['MACD_signal'] = macd.loc[:, 'MACDs_12_26_9']
    data['MACD_histogram'] = macd.loc[:, 'MACDh_12_26_9']
    return data


def set_atr(data):
    data['ATR'] = ta.atr(data.High, data.Low, data.Close, length=7)
    return data


def set_rsi(data, rsi_length):
    data['RSI'] = ta.rsi(data.Close, length=rsi_length)
    return data


def set_adx(data, length):
    adx = ta.adx(data['High'], data['Low'], data['Close'], length=length)
    data['ADX'] = adx.ADX_14
    data['ADX_pos'] = adx.DMP_14
    data['ADX_neg'] = adx.DMN_14
    return data


def ema_trade_signal(data, current, back_candles):
    start = max(0, current - back_candles)
    rows = data.loc[start:current]

    if all(rows.High < rows.EMA):
        return -1
    elif all(rows.Low > rows.EMA):
        return 1
    else:
        return 0


def set_ema_trade_signal(data):
    data['EMA_trade_signal'] = data.progress_apply(
        lambda r: ema_trade_signal(data, r.name, 5), axis='columns'
    )
    return data


def macd_trade_signal(data, current):
    if (
        all(data.loc[current - 3:current - 2, 'MACD'] <
            data.loc[current - 3:current - 2, 'MACD_signal']) and
        all(data.loc[current - 1:current, 'MACD'] >
            data.loc[current - 1:current, 'MACD_signal'])
    ):
        return 1
    if (
        all(data.loc[current - 3:current - 2, 'MACD'] >
            data.loc[current - 3:current - 2, 'MACD_signal']) and
        all(data.loc[current - 1:current, 'MACD'] <
            data.loc[current - 1:current, 'MACD_signal'])
    ):
        return -1
    return 0


def set_macd_trade_signal(data):
    data['MACD_trade_signal'] = data.progress_apply(
        lambda r: macd_trade_signal(data, r.name),
        axis='columns'
    )
    return data


def set_rsi_trade_signal(data):
    data['RSI_trade_signal'] = data.progress_apply(
        lambda r: 1 if r.RSI > 70 else -1 if r.RSI < 30 else 0,
        axis='columns'
    )
    return data


def set_adx_trade_signal(data):
    data['ADX_trade_signal'] = data.progress_apply(
        lambda r: 1 if r.ADX > 30 else 0,
        axis='columns'
    )
    return data


def set_total_trade_signal(data, total_trade_signal):
    data['Total_trade_signal'] = data.progress_apply(
        lambda r: total_trade_signal(r),
        axis='columns'
    )
    return data


class MacdStrategy(Strategy):
    mysize = 3
    slcoef = 1.1
    TPSLRatio = 1.5
    # rsi_length = 16

    def init(self):
        super().init()
        self.signal1 = self.I(lambda: self.data.Total_trade_signal)
        # df['RSI']=ta.rsi(df.Close, length=self.rsi_length)

    def next(self):
        super().next()
        slatr = self.slcoef * self.data.ATR[-1]
        TPSLRatio = self.TPSLRatio

        # if len(self.trades)>0:
        #     if self.trades[-1].is_long and self.data.RSI[-1]>=90:
        #         self.trades[-1].close()
        #     elif self.trades[-1].is_short and self.data.RSI[-1]<=10:
        #         self.trades[-1].close()

        if self.signal1 == 1 and len(self.trades) == 0:
            sl1 = self.data.Close[-1] - slatr
            tp1 = self.data.Close[-1] + slatr * TPSLRatio
            self.buy(sl=sl1, tp=tp1, size=self.mysize)

        elif self.signal1 == -1 and len(self.trades) == 0:
            sl1 = self.data.Close[-1] + slatr
            tp1 = self.data.Close[-1] - slatr*TPSLRatio
            self.sell(sl=sl1, tp=tp1, size=self.mysize)


def set_indicators(data, ema_length):
    set_ema(data, ema_length)
    set_macd(data)
    set_atr(data)
    set_rsi(data, 14)
    set_adx(data, 14)


def set_trade_signals(data, total_trade_signal):
    set_ema_trade_signal(data)
    set_macd_trade_signal(data)
    set_rsi_trade_signal(data)
    set_adx_trade_signal(data)

    set_total_trade_signal(data, total_trade_signal)
    print(f'number of trades: {data[data.Total_trade_signal != 0].shape[0]}')


def show_heatmap(heatmap):
    # Convert multiindex series to dataframe
    heatmap_dataFrame = heatmap.unstack()
    plt.figure(figsize=(10, 8))
    sns.heatmap(heatmap_dataFrame, annot=True, cmap='viridis', fmt='.0f')
    plt.show()


def backtest_trading(data, cash):
    backtest = Backtest(data, MacdStrategy, cash=cash,
                        margin=1/30, commission=0.00)
    stats, heatmap = backtest.optimize(slcoef=[i/10 for i in range(10, 26)],
                                       TPSLRatio=[i/10 for i in range(10, 26)],
                                       maximize='Return [%]', max_tries=300,
                                       random_state=0,
                                       return_heatmap=True)

    return backtest, stats, heatmap
