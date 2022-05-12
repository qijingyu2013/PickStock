# 主文件

import pysnowball as ball
from LimitUpAfterFourDayWithDB import fetchLimitUpAfterFourDay
from NineYin import fetchNineDayData
from StockToDB import upgradeStockList, upgradeStockTrade
from utils import currentTime


def main():
    print('###初始化执行任务')
    print('[1] 保存并且更新股票信息')
    print('[2] 保存并且更新股票行情')
    print('[3] 全量更新')
    print('[4] 获取连阴票')
    print('[5] 获取满足5天前涨停后4天不破位的票')
    print('根据编号选择任务:')
    s = int(input())
    ball.set_token('xq_a_token=9d7c75c59c8b3ef763711f682f3bb26163c4aad7;')
    timestamp = currentTime()

    if s == 1:
        upgradeStockList(timestamp)
        print('\r保存并且更新股票信息,已完成！')
    elif s == 2:
        upgradeStockTrade(timestamp)
        print('\r保存并且更新股票行情,已完成！')
    elif s == 3:
        upgradeStockList(timestamp)
        upgradeStockTrade(timestamp)
        print('\r全量更新,已完成！')
    elif s == 4:
        print('输入连阴次数:')
        count = int(input())
        if count <= 4:
            fetchNineDayData(4)
        elif count >= 9:
            fetchNineDayData(9)
        else:
            fetchNineDayData(count)
    elif s == 5:
        fetchLimitUpAfterFourDay()
        print('\r获取满足5天前涨停后4天不破位的票,已完成！')
    else:
        print('输入错误。。。')


main()
