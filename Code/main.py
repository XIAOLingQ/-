import sqlite3
from login import getidentity,getConnection

a=getidentity()
if a == -1:
    print("退出程序")
elif a == 1:
    print("进入用户系统")

else :
    print("进入管理员系统")
