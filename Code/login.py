import os
import sqlite3

from user import User
from adminer import Adminer

def getconnection():
    dbstring = r"../library/library.db"  # 相对路径
    base_dir = os.path.dirname(os.path.abspath(__file__))  # 获取当前文件所在目录
    db_path = os.path.join(base_dir, dbstring)  # 构建相对路径的绝对路径
    conn = sqlite3.connect(db_path)
    return conn

def loggin():
    while True :
        print("**************登录***************")
        print("1.用户     2.管理员   3.注册    4.退出")
        print("请输入登录身份")
        try:
            a = int(input("请输入一个整数："))
        except ValueError:
            print("输入无效，请输入一个整数。")
            continue
        if a == 1:
            table_name = "user"
        elif a == 2:
            table_name = "adminer"
        elif a == 4:
            return None
        if a==1 or a==2:
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
                if a == 1:
                    return User(user_id, name)
                else:
                    return Adminer(user_id, name)
            else:
                print("用户名或密码错误，请重试。")
                conn.close()
        elif a == 3:
            while True:
                print("1.用户注册  2.管理员注册  3.返回")
                try:
                    reg_option = int(input("请输入一个整数："))
                except ValueError:
                    print("输入无效，请输入一个整数。")
                    continue

                if reg_option == 1:
                    reg_table = "user"
                elif reg_option == 2:
                    reg_table = "adminer"
                elif reg_option == 3:
                    break
                else:
                    print("无效的选项，请重新选择。")
                    continue

                username = input("请输入用户名: ")
                password = input("请输入密码: ")
                name = input("请输入昵称: ")

                if not username or not password or not name:
                    print("用户名和密码不能为空，请重试。")
                    continue

                conn = getconnection()
                cursor = conn.cursor()

                # 检查用户名是否已存在
                check_query = f"SELECT * FROM {reg_table} WHERE username=?"
                cursor.execute(check_query, (username,))
                if cursor.fetchone():
                    print("用户名已存在，请选择其他用户名。")
                    conn.close()
                    continue

                # 获取最大ID并加一
                max_id_query = f"SELECT MAX(id) FROM {reg_table}"
                cursor.execute(max_id_query)
                max_id = cursor.fetchone()[0]
                if max_id is None:
                    new_id = 1
                else:
                    new_id = max_id + 1

                insert_query = f"INSERT INTO {reg_table} (id, username, password,name) VALUES (?, ?, ?, ?)"
                cursor.execute(insert_query, (new_id, username, password,name))
                conn.commit()
                conn.close()
                print("注册成功！")
                break
        else:
            print("无效的选项，请重新选择。")
            continue
