import matplotlib.pyplot as plt
import requests
import re
from datetime import datetime

from ta.trend import VortexIndicator

import numpy as np

eth_ammount = 0.03434581
plt.style.use('fivethirtyeight')


def cbpGetHistoricRates(market='BTC-GBP', granularity=86400, iso8601start='', iso8601end=''):
    if not isinstance(market, str):
        raise Exception('Market string input expected')

    if not isinstance(granularity, int):
        raise Exception('Granularity integer input expected')

    granularity_options = [60, 300, 900, 3600, 21600, 86400]
    if not granularity in granularity_options:
        raise Exception(
            'Invalid granularity: 60, 300, 900, 3600, 21600, 86400')

    if not isinstance(iso8601start, str):
        raise Exception('ISO8601 date string input expected')

    if not isinstance(iso8601end, str):
        raise Exception('ISO8601 date string input expected')

    # iso8601 regex
    regex = r'^(-?(?:[1-9][0-9]*)?[0-9]{4})-(1[0-2]|0[1-9])-(3[01]|0[1-9]|[12][0-9])T(2[0-3]|[01][0-9]):([0-5][0-9]):([0-5][0-9])(\.[0-9]+)?(Z|[+-](?:2[0-3]|[01][0-9]):[0-5][0-9])?$'

    if len(iso8601start) < 0:
        match_iso8601 = re.compile(regex).match
        if match_iso8601(iso8601start) is None:
            raise Exception('iso8601 start date is invalid')

    if len(iso8601end) < 0:
        match_iso8601 = re.compile(regex).match
        if match_iso8601(iso8601end) is None:
            raise Exception('iso8601 end date is invalid')

    api = 'https://api.pro.coinbase.com/products/' + market + '/candles?granularity=' + \
          str(granularity) + '&start=' + iso8601start + '&end=' + iso8601end
    resp = requests.get(api)
    if resp.status_code != 200:
        raise Exception('GET ' + api + ' {}'.format(resp.status_code))
    data = []
    for price in reversed(resp.json()):
        # time, low, high, open, close, volume
        # datetime.datetime.strptime(date_string, '%Y%m%d%H%M%S%f')
        iso8601 = datetime.utcfromtimestamp(price[0])

        timestamp = datetime.strftime(iso8601, "%Y%m%d%H%M%S")
        a = []
        a.append(iso8601)
        a.append(price[1])
        a.append(price[2])
        a.append(price[3])
        a.append(price[4])
        a.append(price[5])
        data.append(a)

    return data


def HA(df):
    df['HA_Close'] = ''
    df['HA_Open'] = ''
    df['HA_High'] = ''
    df['HA_Low'] = ''
    df['HA_Close'] = (df['Open'] + df['High'] + df['Low'] + df['Close']) / 4

    for i in range(0, len(df)):
        if i == 0:
            a = df['Open'][i]
            b = df['Close'][i]

            df.at[i, 'HA_Open'] = (a + b) / 2
        else:
            a = df['HA_Open'][i - 1]
            b = df['HA_Close'][i - 1]

            df.at[i, 'HA_Open'] = (a + b) / 2

    df['HA_High'] = df[['HA_Open', 'HA_Close', 'High']].max(axis=1)
    df['HA_Low'] = df[['HA_Open', 'HA_Close', 'Low']].min(axis=1)
    # print(df)
    return df


def TEMA(data, time_period, column):
    EMA = data[column].ewm(span=time_period, adjust=False).mean()
    EMA2 = EMA.ewm(span=time_period, adjust=False).mean()
    TEMA = 3 * EMA - 3 * EMA2 + EMA2.ewm(span=time_period, adjust=False).mean()
    return TEMA


def DEMA(data, time_period, column):
    EMA = data[column].ewm(span=time_period, adjust=False).mean()
    DEMA = 2 * EMA - EMA.ewm(span=time_period, adjust=False).mean()
    return DEMA


def TEMA_strategy(data):
    buy_list = []
    sell_list = []
    wallet_value = []
    flag = False
    for i in range(0, len(data)):

        if data['TEMA_short'][i] > data['TEMA_long'][i] and flag == False:
            buy_list.append(data['Close'][i])
            sell_list.append(np.nan)
            flag = True
        elif data['TEMA_short'][i] < data['TEMA_long'][i] and flag == True:
            buy_list.append(np.nan)
            sell_list.append(data['Close'][i])
            flag = False
        else:
            buy_list.append(np.nan)
            sell_list.append(np.nan)
    data['Buy'] = buy_list
    data['Sell'] = sell_list
    data['W_value'] = wallet_value


def DEMA_strategy(data):
    buy_list = []
    sell_list = []
    wallet_value = []
    flag = False
    for i in range(0, len(data)):
        wallet_value.append(data['Close'][i] * eth_ammount)
        if data['DEMA_short'][i] > data['DEMA_long'][i] and flag == False:
            buy_list.append(data['Close'][i])
            sell_list.append(np.nan)
            flag = True
        elif data['DEMA_short'][i] < data['DEMA_long'][i] and flag == True:
            buy_list.append(np.nan)
            sell_list.append(data['Close'][i])
            flag = False
        else:
            buy_list.append(np.nan)
            sell_list.append(np.nan)
    data['Buy'] = buy_list
    data['Sell'] = sell_list


def MACD_SIGNAL_strategy(signal):
    buy_list = []
    sell_list = []

    flag = False
    for i in range(0, len(signal)):

        if signal['MACD'][i] > signal['Signal line'][i]:
            sell_list.append(np.nan)
            if flag != 1:
                buy_list.append(signal['Close'][i])
                flag = 1
            else:
                buy_list.append(np.nan)

        elif signal['MACD'][i] < signal['Signal line'][i]:
            buy_list.append(np.nan)
            if flag != 0:
                sell_list.append(signal['Close'][i])
                flag = 0
            else:
                sell_list.append(np.nan)
        else:
            sell_list.append(np.nan)
            buy_list.append(np.nan)

    return (buy_list, sell_list)


def Plot_data(df):
    plt.figure(figsize=(12.2, 4.5))
    plt.scatter(df.index, df['Buy'], color='green', label='Buy signal', marker='^', alpha=1)
    plt.scatter(df.index, df['Sell'], color='red', label='Sell signal', marker='v', alpha=1)

    plt.plot(df.index, df['Close'], label='Close price', alpha=0.35)
    plt.plot(df.index, df['TEMA_short'], label='TEMA_short', alpha=0.35)
    plt.plot(df.index, df['TEMA_long'], label='TEMA_long', alpha=0.35)
    plt.plot(df.index, df['W_value'], color='black', label='W_value', alpha=0.35)
    plt.xticks(rotation=45)
    plt.title('Close Price Buy and Sell signals')
    plt.xlabel('Date', fontsize=18)
    plt.ylabel('Close price Eur', fontsize=18)
    plt.legend(loc='upper left')
    plt.show()


def Plot_signal_MACD_data(df, macd, signal):
    plt.figure(figsize=(12.2, 4.5))

    plt.plot(df.index, macd, label='MACD')
    plt.plot(df.index, signal, label='SIGNAL')
    plt.legend(loc='upper left')
    plt.show()


def Plot_MACD_data(df, macd, signal):
    fig, ax = plt.subplots(constrained_layout=True)
    ax.figure(figsize=(12.2, 4.5))
    ax.scatter(df.index, df['Buy_signal_price'], color='green', label='Buy signal', marker='^', alpha=1, linewidth=1)
    ax.scatter(df.index, df['Sell_signal_price'], color='red', label='Sell signal', marker='v', alpha=1, linewidth=1)

    ax.plot(df.index, df['Close'], label='Close price', alpha=0.35, linewidth=1)

    plt.plot(df.index, macd, label='MACD', linewidth=1)
    plt.plot(df.index, signal, label='SIGNAL', linewidth=1)

    plt.title('Close Price Buy and Sell signals')
    plt.xlabel('Date', fontsize=18)
    plt.ylabel('Close price Eur', fontsize=18)
    plt.legend(loc='upper left')
    plt.show()


def Plot__with_volume(df, ema):
    fig, ax = plt.subplots(constrained_layout=True)
    ax.figure(figsize=(12.2, 4.5))

    ax.plot(df.index, df['Close'], label='Close price', alpha=0.35, linewidth=1)

    plt.plot(df.index, ema, label='ema', linewidth=1)
    plt.plot(df.index, df['Volume'], label='SIGNAL', linewidth=1)

    plt.title('Close Price Buy and Sell signals')
    plt.xlabel('Date', fontsize=18)
    plt.ylabel('Close price Eur', fontsize=18)
    plt.legend(loc='upper left')
    plt.show()


def ema(df, time_period):
    df['EMA_200'] = ''
    df['EMA_200'] = df['Close'].ewm(span=time_period, adjust=False).mean()


def macd(short_ema, long_ema):
    macd = short_ema - long_ema
    return macd


def signal(macd):
    signal = macd.ewm(span=9, adjust=False).mean()
    return signal


def plot_rsi(df):
    df['rsi'] = ''
    diff = df.Close.diff().values
    gains = diff
    losses = -diff
    with np.errstate(invalid='ignore'):
        gains[(gains < 0) | np.isnan(gains)] = 0.0
        losses[(losses <= 0) | np.isnan(losses)] = 1e-10  # we don't want divide by zero/NaN
    n = 14
    m = (n - 1) / n
    ni = 1 / n
    g = gains[n] = np.nanmean(gains[:n])
    l = losses[n] = np.nanmean(losses[:n])
    gains[:n] = losses[:n] = np.nan
    for i, v in enumerate(gains[n:], n):
        g = gains[i] = ni * v + m * g
    for i, v in enumerate(losses[n:], n):
        l = losses[i] = ni * v + m * l
    rs = gains / losses
    df['rsi'] = 100 - (100 / (1 + rs))

    return df


def vortex(df):
    df['vortex_indicator_neg'] = ''
    df['vortex_indicator_pos'] = ''

    vorteksas = VortexIndicator(df['High'], df['Low'], df['Close'], window=14, fillna=False)

    df['vortex_indicator_neg'] = vorteksas.vortex_indicator_neg()
    df['vortex_indicator_pos'] = vorteksas.vortex_indicator_pos()
    return df


def get_currrency_list():
    valiutos = []

    url = "https://api.exchange.coinbase.com/products"
    headers = {"Accept": "application/json"}
    response = requests.get(url).json()
    for i in range(len(response)):
        dic = response[i]
        valiutos.append(dic['id'])
    surusiuotas = sorted(valiutos)
    return (surusiuotas)