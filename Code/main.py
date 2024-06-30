import sqlite3
from user import *
from login import *
from adminer import *

using = loggin()
if using is None:
    print("程序已退出")
elif isinstance(using, User):
    print(f"欢迎, 用户 {using.name} (用户ID: {using.user_id})")
    # 用户
elif isinstance(using, Adminer):
    print(f"欢迎, 管理员 {using.name} (管理员ID: {using.user_id})")
    while True :
        menuadminer()
        flag = int(input("请输入："))
        if flag== 1 :
            using.bookInput()
        elif flag == 2 :
            using.bookModify()
        elif flag == 3 :
            using.bookDel()
        elif flag == 4 :
            using.bookSearch()
        elif flag == 5 :
            break
        else :
            print("输入错误，请重新输入：")
    # 在这里添加管理员的操作

