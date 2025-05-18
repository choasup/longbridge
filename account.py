from datetime import datetime, date
from dataclasses import dataclass
from decimal import Decimal
from typing import List, Dict

@dataclass
class Trade:
    time: datetime
    action: str
    price: float
    quantity: int
    reason: str
    profit: float = 0.0

@dataclass
class TradeLog:
    time: datetime
    action: str
    price: float
    quantity: int
    reason: str
    profit: float = 0.0
    position: int = 0  # 交易后的持仓
    cost_price: float = 0.0  # 每股成本价格
    market_value: float = 0.0  # 交易后的市值
    available_capital: float = 0.0  # 可用资金
    account_value: float = 0.0  # 账户总值
    total_profit: float = 0.0  # 总收益

class PositionManager:
    def __init__(self, initial_capital: Decimal = Decimal('10000')):
        self.position = 0  # 当前持仓数量
        self.total_cost = Decimal('0')  # 总成本
        self.avg_cost_price = Decimal('0')  # 平均成本价格
        self.trades: List[Trade] = []  # 交易记录
        self.holdings: List[Dict] = []  # 持仓记录
        self.trade_logs: List[TradeLog] = []  # 详细交易日志
        self.last_price = Decimal('0')  # 最新价格
        
        # 资金管理
        self.initial_capital = initial_capital  # 初始资金
        self.available_capital = initial_capital  # 可用资金
    
    def _log_trade(self, time: datetime, action: str, price: Decimal, quantity: int, 
                  reason: str, profit: float = 0.0) -> None:
        """记录交易日志"""
        self.trade_logs.append(TradeLog(
            time=time,
            action=action,
            price=float(price),
            quantity=quantity,
            reason=reason,
            profit=profit,
            position=self.position,
            cost_price=float(self.get_average_cost_price()),
            market_value=float(price * self.position),
            available_capital=float(self.available_capital),
            account_value=float(self.get_account_value()),
            total_profit=float(self.get_total_profit())
        ))
    
    def get_average_cost_price(self) -> Decimal:
        """获取平均成本价格"""
        return self.avg_cost_price
    
    def get_market_value(self) -> Decimal:
        """获取当前市值"""
        return self.last_price * self.position
    
    def get_available_capital(self) -> Decimal:
        """获取可用资金"""
        return self.available_capital
    
    def get_account_value(self) -> Decimal:
        """获取账户总值（股票市值 + 可用资金）"""
        return self.get_market_value() + self.available_capital
    
    def get_total_profit(self) -> Decimal:
        """获取总收益（账户总值 - 初始资金）"""
        return self.get_account_value() - self.initial_capital
        
    def update_price(self, price: Decimal) -> None:
        """更新最新价格"""
        self.last_price = price
    
    def buy(self, time: datetime, price: Decimal, quantity: int = 1, reason: str = "") -> None:
        """买入操作"""
        cost = price * quantity
        if cost > self.available_capital:
            return
            raise ValueError(f"可用资金不足，需要: {cost}, 可用: {self.available_capital}")
            
        
        self.total_cost += cost
        self.position += quantity
        self.last_price = price  # 更新最新价格
        self.available_capital -= cost  # 减少可用资金
        
        # 更新总成本和平均成本价格
        self.avg_cost_price = self.total_cost / self.position
        
        self.holdings.append({
            'time': time,
            'price': price,
            'quantity': quantity
        })
        
        trade = Trade(
            time=time,
            action='买入',
            price=float(price),
            quantity=quantity,
            reason=reason,
        )
        self.trades.append(trade)
        self._log_trade(time, '买入', price, quantity, reason)
    
    def sell(self, time: datetime, price: Decimal, quantity: int = 1, reason: str = "") -> float:
        """卖出操作，返回本次交易的收益"""
        if self.position < quantity:
            return 0
            raise ValueError(f"持仓不足，当前持仓: {self.position}, 需要卖出: {quantity}")
            
        self.total_cost = self.total_cost - price * quantity
        self.position = self.position - quantity
        # 更新总成本和平均成本价格
        self.last_price = price  # 更新最新价格
        self.available_capital += price * quantity  # 增加可用资金

        # 计算卖出收益（基于平均成本价格）
        profit = (price - self.avg_cost_price) * quantity

        if self.position != 0:
            self.avg_cost_price = self.total_cost / self.position
        else:
            self.avg_cost_price = price
        
        self._update_holdings(quantity)
        
        trade = Trade(
            time=time,
            action='卖出',
            price=float(price),
            quantity=quantity,
            reason=reason,
        )
        self.trades.append(trade)
        self._log_trade(time, '卖出', price, quantity, reason, profit)
        
        return 0 #profit
    
    def _update_holdings(self, quantity: int) -> None:
        """更新持仓记录"""
        remaining = quantity
        new_holdings = []
        
        for holding in self.holdings:
            if remaining <= 0:
                new_holdings.append(holding)
                continue
                
            if holding['quantity'] <= remaining:
                remaining -= holding['quantity']
            else:
                new_holdings.append({
                    'time': holding['time'],
                    'price': holding['price'],
                    'quantity': holding['quantity'] - remaining
                })
                remaining = 0
        
        self.holdings = new_holdings
    
    def print_trade_logs(self) -> None:
        """打印详细的交易日志"""
        print("\n交易日志:")
        # 定义列宽
        col_widths = {
            'time': 9,
            'action': 6,
            'price': 8,
            'quantity': 6,
            'position': 6,
            'cost_price': 8,
            'market_value': 10,
            'available_capital': 10,
            'account_value': 10,
            'total_profit': 10
        }
        
        # 打印表头
        header = (
            f"{'时间':<{col_widths['time']}} "
            f"{'动作':<{col_widths['action']}} "
            f"{'价格':>{col_widths['price']}} "
            f"{'数量':>{col_widths['quantity']}} "
            f"{'持仓':>{col_widths['position']}} "
            f"{'成本价':>{col_widths['cost_price']}} "
            f"{'持仓市值':>{col_widths['market_value']}} "
            f"{'可用资金':>{col_widths['available_capital']}} "
            f"{'账户总值':>{col_widths['account_value']}} "
            f"{'总收益':>{col_widths['total_profit']}}"
        )
        print(header)
        print("-" * len(header))
        
        # 打印数据行
        for log in self.trade_logs:
            row = (
                f"{log.time.strftime('%H:%M:%S'):<{col_widths['time']}} "
                f"{log.action:<{col_widths['action']}} "
                f"{log.price:>{col_widths['price']}.2f} "
                f"{log.quantity:>{col_widths['quantity']}} "
                f"{log.position:>{col_widths['position']}} "
                f"{log.cost_price:>{col_widths['cost_price']}.2f} "
                f"{log.market_value:>{col_widths['market_value']}.2f} "
                f"{log.available_capital:>{col_widths['available_capital']}.2f} "
                f"{log.account_value:>{col_widths['account_value']}.2f} "
                f"{log.total_profit:>{col_widths['total_profit']}.2f}"
            )
            print(row)
    
    def print_summary(self) -> None:
        """打印账户摘要"""
        print("\n账户摘要:")
        # 定义列宽
        col_width = 15
        
        # 打印数据行
        print(f"{'初始资金:':<{col_width}} {float(self.initial_capital):>10.2f}")
        print(f"{'可用资金:':<{col_width}} {float(self.available_capital):>10.2f}")
        print(f"{'持仓数量:':<{col_width}} {self.position:>10}")
        print(f"{'最新价格:':<{col_width}} {float(self.last_price):>10.2f}")
        print(f"{'平均成本:':<{col_width}} {float(self.get_average_cost_price()):>10.2f}")
        print(f"{'持仓市值:':<{col_width}} {float(self.get_market_value()):>10.2f}")
        print(f"{'账户总值:':<{col_width}} {float(self.get_account_value()):>10.2f}")
        print(f"{'总收益:':<{col_width}} {float(self.get_total_profit()):>10.2f}")
        
        # 打印详细交易日志
        self.print_trade_logs()
