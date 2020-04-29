# Import libraries
import datetime
import pandas as pd
from pandas_datareader import data as pdr
import matplotlib.pyplot as plt
import numpy as np


# Class implementation
class TradingStrategy:
        # Constructor
    def __init__(self, stock, start_date, end_date):
        self.__stock = stock
        self.__start_date = start_date
        self.__end_date = end_date
        self.__stock_data = pd.DataFrame()
        self.__bollinger_data = pd.DataFrame()
        self.__oscillator_data = pd.DataFrame()
        self.__returns_data = pd.DataFrame(columns=['Start', 'End',
                                                    'Operation', 'Return'])
        self.__cum_returns = list()
        self.__sma10 = None
        self.__sma60 = None

        self.__download_data()

    def __download_data(self):
        df = pdr.get_data_yahoo(self.__stock, self.__start_date,
                                self.__end_date)

        self.__stock_data = pd.DataFrame(df['Adj Close'])

    # Getters
    def get_stock_data(self):
        return self.__stock_data

    def get_oscillator_data(self):
        return self.__oscillator_data

    def get_Bollinger_Bands(self):
        return self.__bollinger_data

    def get_returns(self):
        return self.__returns_data

    # Calculations
    def __calculate_SMAs(self):
        self.__stock_data['SMA10'] = self.__stock_data['Adj Close'].rolling(
                window=10, center=False).mean()
        self.__stock_data['SMA60'] = self.__stock_data['Adj Close'].rolling(
                window=60, center=False).mean()

    def __calculate_ma_oscillator(self):

        ema_short = self.__stock_data['Adj Close'].ewm(
                ignore_na=False, span=12, adjust=False).mean()

        ema_long = self.__stock_data['Adj Close'].ewm(
                ignore_na=False, span=26, adjust=False).mean()

        # Oscillator
        self.__oscillator_data['macd'] = ema_short - ema_long
        # Signal line (MA)
        self.__oscillator_data['signal line'] =\
            self.__oscillator_data['macd'].ewm(
            ignore_na=False, span=9, adjust=False).mean()
        # OsMA
        self.__oscillator_data['OsMA'] = \
            self.__oscillator_data['macd'] -\
            self.__oscillator_data['signal line']

    def __calculate_Bollinger_Bands(self):
        self.__bollinger_data['MA10'] = self.__stock_data['Adj Close'].rolling(
                window=10, center=False).mean()
        std = self.__stock_data['Adj Close'].rolling(
                window=10, center=False).std()
        self.__bollinger_data['Upper'] = self.__bollinger_data['MA10'] + \
            std * 1.5
        self.__bollinger_data['Lower'] = self.__bollinger_data['MA10'] - \
            std * 1.5
        self.__bollinger_data['Price'] = self.__stock_data['Adj Close']

        # Drop first rows with NAs
        self.__bollinger_data = self.__bollinger_data.iloc[9:]

    def __add_return(self, start_date, end_date, operation,
                     operation_return):

        k = len(self.__returns_data)

        self.__returns_data.loc[k] = [start_date, end_date,
                                      operation, operation_return]

    def __calculate_return(self, start, end, operation):

        start_price = self.__stock_data['Adj Close'][
                self.__stock_data.index == start].values[0]
        end_price = self.__stock_data['Adj Close'][
                self.__stock_data.index == end].values[0]

        if (operation == 'short'):
            # index 1 sell, index 2 buy
            operation_return = (start_price - end_price) / end_price

        if (operation == 'long'):
            # index 1 buy, index 2 sell
            operation_return = (end_price - start_price) / start_price

        return operation_return

    def __calculate_cum_returns(self):
        cum_return = (self.__returns_data['Return'] + 1).prod() - 1
        return cum_return

    def __calculate_cum_returns1(self):
        self.__cum_returns.append(1)
        cum_sum = 1
        for i in range(len(self.__returns_data)):
            cum_sum = cum_sum*(1+self.__returns_data['Return'][i])
            self.__cum_returns.append(cum_sum)

    def __test_strategy(self):

        open_position = False
        operation = None
        start_position_date = None

        for i in range(1, len(self.__bollinger_data)):

            if i == len(self.__bollinger_data):

                # last day: Close the position
                end_position_date = self.__stock_data.index[i]
                # Close a position
                open_position = False

                operation_return = self.__calculate_return(start_position_date,
                                                           end_position_date,
                                                           operation)

                self.__add_return(start_position_date, end_position_date,
                                  operation, operation_return)

            if ((self.__bollinger_data['Price'][i] >
                 self.__bollinger_data['Lower'][i]) and
                    (self.__bollinger_data['Lower'][i-1] <
                     self.__bollinger_data['Lower'][i-1])):

                # Open long position
                if (open_position):
                    # Close position
                    end_position_date = self.__bollinger_data.index[i]
                    open_position = False
                    operation_return = self.__calculate_return(
                                            start_position_date,
                                            end_position_date,
                                            operation)

                    self.__add_return(start_position_date, end_position_date,
                                      operation, operation_return)

                start_position_date = self.__bollinger_data.index[i]
                open_position = True
                operation = 'long'

            if ((self.__bollinger_data['Price'][i] <
                 self.__bollinger_data['Upper'][i]) and
                    (self.__bollinger_data['Price'][i-1] >
                     self.__bollinger_data['Upper'][i-1])):

                # Open short position
                if (open_position):

                    end_position_date = self.__bollinger_data.index[i]
                    open_position = False

                    operation_return = self.__calculate_return(
                            start_position_date,
                            end_position_date,
                            operation)

                    self.__add_return(start_position_date, end_position_date,
                                      operation, operation_return)

                # Open new position
                start_position_date = self.__bollinger_data.index[i]
                open_position = True
                operation = "short"

    # Visualization
    def __plot_price_and_SMAs(self):
        self.__stock_data.plot(title="Price and SMAs")

    def __plot_periods(self):
        self.__stock_data[['Adj Close', 'SMA60']][np.logical_and(
            self.__stock_data.index > '2004-05-01',
            self.__stock_data.index < '2004-10-01')].plot(
            title="Price and SMA60: from 2004-05-01 to 2004-10-01")

        self.__stock_data[['Adj Close', 'SMA60']][np.logical_and(
            self.__stock_data.index > '2004-10-01',
            self.__stock_data.index < '2005-05-01')].plot(
            title="Price and SMA60: from 2004-10-01 to 2005-05-01")

        self.__stock_data[['Adj Close', 'SMA60']][np.logical_and(
            self.__stock_data.index > '2005-05-01',
            self.__stock_data.index < '2005-07-01')].plot(
            title="Price and SMA60: from 2005-05-01 to 2005-07-01")

    def __plot_oscillator(self):
        # Plot oscillator
        fig, ax = plt.subplots(nrows=2)

        plt.suptitle('OsMA')
        plt.subplot(211)
        self.__stock_data['Adj Close'].plot()

        plt.subplot(212)
        self.__oscillator_data['OsMA'].plot(kind='bar', color='red')

        # show every Nth label
        locs, labels = plt.xticks()
        N = 50
        plt.xticks(locs[::N], self.__oscillator_data.index.year[::N])
        # autorotate the xlabels
        fig.autofmt_xdate()
        plt.show()

    def __plot_Bollinger_Bands(self):
        self.__bollinger_data.plot(title='Bollinger Bands')

    def __plot_returns(self):

        # Plot cumulative returns
        plt.figure(figsize=(10, 7))
        plt.plot(self.__cum_returns)
        plt.title("Cumulative returns of the strategy")
        plt.show()

    def main(self):
        self.__calculate_SMAs()
        self.__plot_price_and_SMAs()
        self.__plot_periods()
        self.__calculate_ma_oscillator()
        self.__plot_oscillator()
        self.__calculate_Bollinger_Bands()
        self.__plot_Bollinger_Bands()
        self.__test_strategy()
        self.__calculate_cum_returns1()
        print(self.__calculate_cum_returns())
        self.__plot_returns()


stock = 'MCD'
start_date = datetime.date(2004, 01, 01)
end_date = datetime.date(2005, 07, 01)

strategy = TradingStrategy(stock, start_date, end_date)
strategy.main()
