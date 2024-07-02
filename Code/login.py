import sqlite3

from user import User
from adminer import Adminer

def getconnection():
    dbstring="E:\Code\Python\专业综合训练Ⅱ\library\library.db"
    conn=sqlite3.connect(dbstring)
    return conn

def loggin():
    while True :

        print("1.用户     2.管理员     3.退出")
        print("请输入登录身份")
        a=int(input())
        if a == 1:
            table_name = "user"
        elif a == 2:
            table_name = "adminer"
        elif a == 3:
            print("退出登录")
            return None
        else:
            print("无效的选项，请重新选择。")
            continue

        username = input("请输入用户名: ")
        password = input("请输入密码: ")

        conn = getconnection()
        cursor = conn.cursor()

        query = f"SELECT * FROM {table_name} WHERE username=? AND password=?"
        cursor.execute(query, (username, password))
        result = cursor.fetchone()

        if result:
            user_id, name = result[0], result[1]
            print("登录成功!")
            conn.close()
            if a==1 :
                return User(user_id,name)
            else :
                return Adminer(user_id,name)
        else:
            print("用户名或密码错误，请重试。")
            conn.close()
