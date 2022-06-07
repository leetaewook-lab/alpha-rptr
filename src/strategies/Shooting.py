# coding: UTF-8
import os
import random

import math
import re
import time

import numpy
from hyperopt import hp

from src import logger, notify
from src.indicators import highest, lowest, med_price, avg_price, typ_price, atr, MAX, sma, bbands, macd, adx, sar, cci, rsi, crossover, crossunder, \
    last, rci, double_ema, ema, triple_ema, wma, ssma, hull, supertrend, rsx, donchian
from src.exchange.bitmex.bitmex import BitMex
from src.exchange.binance_futures.binance_futures import BinanceFutures
from src.exchange.bitmex.bitmex_stub import BitMexStub
from src.exchange.binance_futures.binance_futures_stub import BinanceFuturesStub
from src.bot import Bot
from src.gmail_sub import GmailSub

# 1m, 9, 3, -60 => 승률 좋은데?
TIME_UNIT = '1m'
EMA_RANGE = 9
PERCENTAGE = 3
BEFORE_PRICE_INDEX = -60

class Shooting(Bot):
    def __init__(self): 
        # set time frame here       
        Bot.__init__(self, [TIME_UNIT])
        # initiate variables
        self.isLongEntry = []
        self.isShortEntry = []
        
    def options(self):
        return {}

    def strategy(self, action, open, close, high, low, volume):    
        # 프로덕션에 올리기 전에 레버리지 크기 확인할 것
        lot = round(self.exchange.get_lot(), 3)

        # 상승장인지 하락장인지 판별하기 위해 이중지수이동평균을 사용한다.
        my_ema = double_ema(close, EMA_RANGE)[-1]
        is_bull = my_ema[-1] < close[-1]

        # 상승장에 급격한 하락이 나오면 롱을 친다.
        # 하락장에 급격한 상승이 나오면 숏을 친다.
        long_entry_condition = (close[-1] <= close[BEFORE_PRICE_INDEX] * (1 - (PERCENTAGE / 100))) and is_bull
        short_entry_condition = (close[-1] >= close[BEFORE_PRICE_INDEX] * (1 + (PERCENTAGE / 100))) and not is_bull

        self.exchange.sltp(profit_long=PERCENTAGE*2, profit_short=PERCENTAGE*2, stop_long=PERCENTAGE*2, stop_short=PERCENTAGE*2, round_decimals=0)

        def entry_callback(avg_price=close[-1]):
            long = True if self.exchange.get_position_size() > 0 else False
            logger.info(f"{'Long' if long else 'Short'} Entry Order Successful")

        if long_entry_condition:
            self.exchange.entry("Long", True, lot, callback=entry_callback)
            
        if short_entry_condition:
            self.exchange.entry("Short", False, lot, callback=entry_callback)
        
        self.isLongEntry.append(long_entry_condition)
        self.isShortEntry.append(short_entry_condition)
