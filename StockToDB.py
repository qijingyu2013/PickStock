# 底层逻辑 第一天涨停成功,后面4天不破涨停的阳线(不跌破涨停的开盘价)

# 1. 每天定时自动拉取前一天股票数据
# 1.1 抓取股票信息
# 1.2 抓取指定日期的股票行情
# 2. 第一天涨停成功,后面4天不破涨停的阳线(不跌破涨停的开盘价)
# 2.1 找出4天前涨停成功的票
# 2.2 筛选出4天后不跌破涨停开盘价的票

import datetime
import time
from enum import Enum

from sqlalchemy import and_

import models
import pysnowball as ball


# 抓取股票列表
def fetchStockList(timestamp):
    lists = ball.list(5000)
    # print(list)
    return lists


# 保存并且更新股票信息
def saveStockList(data):
    lists = data['data']['list']
    for item in lists:
        try:
            result = models.session.query(
                models.StockList.id
            ).filter(
                and_(
                    models.StockList.name == item['name'],
                    models.StockList.code == item['symbol'][-6:]
                )
            ).all()
            if len(result) < 1:
                stock_list_instance = models.StockList(
                    name=item['name'],  # 股票名称
                    code=item['symbol'][-6:],  # 股票代码
                    flag=item['symbol'][0:2],  # 沪深标识位
                )
                models.session.add(stock_list_instance)
            # 提交
            models.session.commit()
        except IndexError as e:
            print("this is a IndexError:", e)
        except KeyError as e:
            print("this is a KeyError:", e)
    return ''


# 更新股票信息
def upgradeStockList(timestamp):
    lists = fetchStockList(timestamp)
    saveStockList(lists)


class StockType(Enum):
    HuShenChuang = 1
    HuShen = 2
    Hu = 3
    Shen = 4
    Chuang = 5
    Ke = 6


# 从数据库里拿出股票列表
def fetchStockListFromDB(type=StockType.HuShen, st=True):
    try:
        # 深
        sz = models.session.query(
            models.StockList.id,
            models.StockList.flag,
            models.StockList.code,
            models.StockList.name
        ).filter(
            and_(
                models.StockList.code < 200000,
                models.StockList.status.in_((0, 1 if st else 0))
            )
        ).all()
        # 创业板
        cy = models.session.query(
            models.StockList.id,
            models.StockList.flag,
            models.StockList.code,
            models.StockList.name
        ).filter(
            and_(
                models.StockList.code >= 300000,
                models.StockList.code < 310000,
                models.StockList.status.in_((0, 1 if st else 0))
            )
        ).all()
        # 沪
        sh = models.session.query(
            models.StockList.id,
            models.StockList.flag,
            models.StockList.code,
            models.StockList.name
        ).filter(
            and_(
                models.StockList.code >= 600000,
                models.StockList.code < 688000,
                models.StockList.status.in_((0, 1 if st else 0))
            )
        ).all()

        if type == StockType.HuShenChuang:
            result = sz + cy + sh
        elif type == StockType.HuShen:
            result = sz + sh
        elif type == StockType.Hu:
            result = sh
        elif type == StockType.Shen:
            result = sz
        else:
            result = sz + cy + sh

        print("股票池数量:", len(result))
    except IndexError as e:
        print("this is a IndexError:", e)
    except KeyError as e:
        print("this is a KeyError:", e)
    return result


def updateResult(result, item):
    result.volume = item[1]
    result.open = item[2],  # 开盘价
    result.high = item[3],  # 最高价
    result.low = item[4],  # 最低价
    result.close = item[5],  # 收盘价
    result.chg = item[6],  # 涨跌幅
    result.percent = item[7],  # 涨跌幅%
    result.turn_over_rate = item[8],  # 换手率%
    result.amount = item[9],  # 成交额
    return result


# 保存行情信息
def saveStockTradeDaily(stock_id, stock_code, stock_name, data_daily):
    for item in data_daily:
        try:
            result = models.session.query(
                models.StockTrade
            ).filter(
                and_(
                    models.StockTrade.sid == stock_id,
                    models.StockTrade.timestamp == item[0]
                )
            ).one_or_none()
            if result is not None:
                updateResult(result, item)
            else:
                # 涨停价&跌停价
                if stock_code[0:1] == '3':
                    limit_up_price = round((item[5] - item[6]) * 1.2, 2)
                    limit_down_price = round((item[5] - item[6]) * 0.8, 2)
                else:
                    limit_up_price = round((item[5] - item[6]) * 1.1, 2)
                    limit_down_price = round((item[5] - item[6]) * 0.9, 2)
                stock_trade_instance = models.StockTrade(
                    sid=stock_id,  # stock_list的主键
                    code=stock_code,  # 股票代码
                    name=stock_name,  # 股票名称
                    timestamp=item[0],  # 交易日时间戳
                    volume=item[1],  # 成交量(手)
                    open=item[2],  # 开盘价
                    high=item[3],  # 最高价
                    low=item[4],  # 最低价
                    close=item[5],  # 收盘价
                    chg=item[6],  # 涨跌幅
                    percent=item[7],  # 涨跌幅%
                    turn_over_rate=item[8],  # 换手率%
                    amount=item[9],  # 成交额
                    limit_up=limit_up_price,  # 涨停价
                    limit_down=limit_down_price,  # 跌停价
                )
                models.session.add(stock_trade_instance)
            # 提交
            models.session.commit()
        except IndexError as e:
            print("this is a IndexError:", e)
        except KeyError as e:
            print("this is a KeyError:", e)
    return


# 保存行情信息
def saveStockTradeWeekly(stock_id, stock_code, stock_name, data_weekly):
    for item in data_weekly:
        try:
            result = models.session.query(
                models.StockTradeWeekly
            ).filter(
                and_(
                    models.StockTradeWeekly.sid == stock_id,
                    models.StockTradeWeekly.timestamp == item[0]
                )
            ).one_or_none()
            if result is not None:
                updateResult(result, item)
            else:
                stock_trade_instance = models.StockTradeWeekly(
                    sid=stock_id,  # stock_list的主键
                    code=stock_code,  # 股票代码
                    name=stock_name,  # 股票名称
                    timestamp=item[0],  # 交易日时间戳
                    volume=item[1],  # 成交量(手)
                    open=item[2],  # 开盘价
                    high=item[3],  # 最高价
                    low=item[4],  # 最低价
                    close=item[5],  # 收盘价
                    chg=item[6],  # 涨跌幅
                    percent=item[7],  # 涨跌幅%
                    turn_over_rate=item[8],  # 换手率%
                    amount=item[9],  # 成交额
                )
                models.session.add(stock_trade_instance)
            # 提交
            models.session.commit()
        except IndexError as e:
            print("this is a IndexError:", e)
        except KeyError as e:
            print("this is a KeyError:", e)
    return


# 保存行情信息
def saveStockTradeMonthly(stock_id, stock_code, stock_name, data_monthly):
    for item in data_monthly:
        try:
            result = models.session.query(
                models.StockTradeMonthly
            ).filter(
                and_(
                    models.StockTradeMonthly.sid == stock_id,
                    models.StockTradeMonthly.timestamp == item[0]
                )
            ).one_or_none()
            if result is not None:
                updateResult(result, item)
            else:
                stock_trade_instance = models.StockTradeMonthly(
                    sid=stock_id,  # stock_list的主键
                    code=stock_code,  # 股票代码
                    name=stock_name,  # 股票名称
                    timestamp=item[0],  # 交易日时间戳
                    volume=item[1],  # 成交量(手)
                    open=item[2],  # 开盘价
                    high=item[3],  # 最高价
                    low=item[4],  # 最低价
                    close=item[5],  # 收盘价
                    chg=item[6],  # 涨跌幅
                    percent=item[7],  # 涨跌幅%
                    turn_over_rate=item[8],  # 换手率%
                    amount=item[9],  # 成交额
                )
                models.session.add(stock_trade_instance)
            # 提交
            models.session.commit()
        except IndexError as e:
            print("this is a IndexError:", e)
        except KeyError as e:
            print("this is a KeyError:", e)
    return


# 更新股票行情
def upgradeStockTrade(timestamp, period='all'):
    lists = fetchStockListFromDB(StockType.HuShenChuang)
    length_total = len(lists)
    handle = 0
    # 保存行情信息
    for item in lists:
        try:
            if period == 'daily':
                # 抓取日行情
                data_daily = ball.daily(item[1] + item[2], timestamp, -1)['data']['item']
                saveStockTradeDaily(item[0], item[2], item[3], data_daily)
            elif period == 'weekly':
                # 抓取周行情
                data_weekly = ball.weekly(item[1] + item[2], timestamp, -2)['data']['item']
                # 剔除本周数据
                data_weekly.pop()
                # 保存行情信息
                saveStockTradeWeekly(item[0], item[2], item[3], data_weekly)
            elif period == 'monthly':
                # 抓取月行情
                data_monthly = ball.monthly(item[1] + item[2], timestamp, -2)['data']['item']
                # 剔除本月数据
                data_monthly.pop()
                # 保存行情信息
                saveStockTradeMonthly(item[0], item[2], item[3], data_monthly)
            else:
                data_daily = ball.daily(item[1] + item[2], timestamp, -1)['data']['item']
                saveStockTradeDaily(item[0], item[2], item[3], data_daily)
                # 抓取周行情
                data_weekly = ball.weekly(item[1] + item[2], timestamp, -2)['data']['item']
                # 剔除本周数据
                data_weekly.pop()
                # 保存行情信息
                saveStockTradeWeekly(item[0], item[2], item[3], data_weekly)
                # 抓取月行情
                data_monthly = ball.monthly(item[1] + item[2], timestamp, -2)['data']['item']
                # 剔除本月数据
                data_monthly.pop()
                # 保存行情信息
                saveStockTradeMonthly(item[0], item[2], item[3], data_monthly)
        except KeyError as e:
            print("\rthis is a KeyError:", e)
            print(item[0], item[2], item[3])
        time.sleep(0.5)
        handle += 1
        percent = handle / length_total
        surplus = round((length_total - handle) * 0.75, 1)
        print('\r完成度为: {:.2%}, 还剩余: {}秒'.format(percent, surplus), end='', flush=True)

    return


# 抓取股票信息
def fetchStockInfo(ulist, data, timestamp):
    print("Loading", end="")
    lists = data['data']['list']
    length_total = len(lists)
    handle = 0
    for item in lists:
        # # 沪深标识位
        # item['symbol'][0:2]
        # # 股票代码
        # item['symbol'][-6:]
        # # 股票名称
        # item['name']
        # # 当天价格
        # item['current']
        try:
            # 5天行情
            data_five = ball.daily(item['symbol'], timestamp, -5)['data']
            # 数据长度
            length = len(data_five['item'])
            # 第一天开盘价
            opening_price_first = data_five['item'][0][2]
            # 第一天收盘价
            closing_price_first = data_five['item'][0][5]

            # 第一天涨停价
            if item['symbol'][0:3] == 'SZ3':
                limit_up_price_first = round(data_five['item'][0][2] * 1.2, 2)
            else:
                limit_up_price_first = round(data_five['item'][0][2] * 1.1, 2)
            # print(opening_price_first, closing_price_first, limit_up_price_first)

            # 第一天涨停价 = 第一天收盘价
            if closing_price_first == limit_up_price_first:
                times_flag = 0
                for i in range(length, -1, -1):
                    # 当前开盘价
                    opening_price_current = data_five['item'][i - 1][2]
                    # 当前收盘价
                    closing_price_current = data_five['item'][i - 1][5]
                    # 找出当天收盘价高于第一天开盘价
                    if closing_price_current > opening_price_first:
                        times_flag += 1
                if times_flag == 5:
                    ulist.append([item['name'], item['symbol']])
        # 当需要分开捕获多个异常可以使用多条except语句，try与except之间语句触发任意一个异常捕获后就跳到对应except执行其下面的语句，其余except不在继续执行
        except IndexError as e:
            print("this is a IndexError:", e)
        except KeyError as e:
            print("this is a KeyError:", e)

        # time.sleep(0.1)
        handle += 1
        percent = handle / length_total
        surplus = round((length_total - handle) * 0.05, 1)
        print('\r完成度为: {:.2%}, 还剩余: {}秒'.format(percent, surplus), end='', flush=True)
        # print("\r 完成度为%f%, 还剩余%f秒。" %percent %surplus, end='', flush=True)
    return ulist


# 保存执行任务
def saveStockMission(timestamp, type, ulist):
    stock_mission_instance = models.StockMission(
        timestamp=timestamp,  # 时间戳
        type=type,  # 任务类型 1=9阴 2=涨停后4天不破位
        content=ulist,  # 执行结果
    )
    models.session.add(stock_mission_instance)
    # 提交
    models.session.commit()
    return


def currentTime():
    current = datetime.datetime.now()
    # 打印当前时间
    print("当前时间 :", current)

    year = datetime.datetime.now().year
    month = datetime.datetime.now().month
    day = datetime.datetime.now().day
    # 雪球网请求是需要把日往后延一天
    dt = str(year) + '-' + str(month) + '-' + str(day + 1) + ' 17:00:00'
    timeArray = time.strptime(dt, "%Y-%m-%d %H:%M:%S")
    timestamp = time.mktime(timeArray)
    # print(round(timestamp*1000))
    return round(timestamp * 1000)


def main():
    ball.set_token('xq_a_token=9d7c75c59c8b3ef763711f682f3bb26163c4aad7;')
    timestamp = currentTime()
    upgradeStockTrade(timestamp)
#     print('###初始化执行任务')
#     print('[1] 保存并且更新股票信息')
#     print('[2] 保存并且更新股票行情')
#     print('[3] 全量更新')
#     print('根据编号选择任务:')
#     s = int(input())
#     ball.set_token('xq_a_token=9d7c75c59c8b3ef763711f682f3bb26163c4aad7;')
#     timestamp = currentTime()
#
#     if s == 1:
#         upgradeStockList(timestamp)
#         print('\r保存并且更新股票信息,已完成！')
#     elif s == 2:
#         upgradeStockTrade(timestamp)
#         print('\r保存并且更新股票行情,已完成！')
#     elif s == 3:
#         upgradeStockList(timestamp)
#         upgradeStockTrade(timestamp)
#         print('\r全量更新,已完成！')
#     else:
#         print('输入错误。。。')
#
#
# main()
