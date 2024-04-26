def total_macd_adx_trade_signal(row):
    if (row.ADX_trade_signal == 0):
        return 0

    if (row.MACD_trade_signal == 1):
        return 1
    elif (row.MACD_trade_signal == -1):
        return -1
    else:
        return 0

def total_macd_ema_trade_signal(row):
    if ((row.EMA_trade_signal == 1) & (row.MACD_trade_signal == 1)):
        return 1
    elif ((row.EMA_trade_signal == -1) & (row.MACD_trade_signal == -1)):
        return -1
    else:
        return 0
