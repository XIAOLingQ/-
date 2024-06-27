import sqlite3
from login import getidentity
#连接数据库
def getConnection():
    dbstring="E:\Code\Python\专业综合训练Ⅱ\library\library.db"
    conn=sqlite3.connect(dbstring)
    return conn

a=getidentity()
if a == -1:
    print("退出程序")
elif a == 1:
    print("进入用户系统")

else :
    print("进入管理员系统")
