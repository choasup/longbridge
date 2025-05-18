import os
import pandas as pd
import numpy as np
from decimal import Decimal
from typing import List, Dict

from account import *

from longport.openapi import Config, QuoteContext, TradeContext
from longport.openapi import OrderType, OrderSide, TimeInForceType
from longport.openapi import Period, AdjustType

def calculate_bollinger_bands(df, window=15, num_std=2):
    """计算布林带"""
    # 将Decimal转换为float进行计算
    df['price_float'] = df['price'].apply(float)
    df['MA'] = df['price_float'].rolling(window=window).mean()
    df['STD'] = df['price_float'].rolling(window=window).std()
    df['Upper'] = df['MA'] + (df['STD'] * num_std)
    df['Lower'] = df['MA'] - (df['STD'] * num_std)
    return df

def main(quote_ctx, trade_ctx, symbol):
    # 获取3分钟K线数据
    resp = quote_ctx.intraday(symbol)
    #print("Resp structure:", resp)  # 打印resp结构
        
    # 转换为DataFrame
    df = pd.DataFrame({
        'timestamp': [candle.timestamp for candle in resp],
        'price': [candle.price for candle in resp],
        'volume': [candle.volume for candle in resp]
    })
    
    df['time'] = pd.to_datetime(df['timestamp'], unit='s')
    df.set_index('time', inplace=True)    
    # 计算BOLL线
    df = calculate_bollinger_bands(df)

    #from IPython import embed; embed()
    # 初始化持仓管理器
    position_manager = PositionManager()

    # 遍历每个时间点
    for i in range(1, len(df)):
        current_price = df['price'].iloc[i]
        upper_band = Decimal(str(df['Upper'].iloc[i]))
        lower_band = Decimal(str(df['Lower'].iloc[i]))
        
        # 更新最新价格
        position_manager.update_price(current_price)
        
        # 检查是否有NaN值
        if pd.isna(lower_band) or pd.isna(upper_band):
            continue
        
        # 交易信号
        if current_price < lower_band:  # 价格低于下轨，买入信号
            position_manager.buy(
                time=df.index[i],
                price=current_price,
                quantity=10,
                reason='价格低于BOLL下轨'
            )
                
        if current_price > upper_band and position_manager.position > 0:  # 价格高于上轨，卖出信号
            position_manager.sell(
                time=df.index[i],
                price=current_price,
                quantity=position_manager.position,
                reason='价格高于BOLL上轨'
            )

    # 打印账户摘要
    position_manager.print_summary()

if __name__ == "__main__":
    # Load configuration from environment variables
    # 模拟账户
    config = Config.from_env()

    quote_ctx = QuoteContext(config)
    trade_ctx = TradeContext(config)

    symbol = "BABA.US"
    main(quote_ctx, trade_ctx, symbol)