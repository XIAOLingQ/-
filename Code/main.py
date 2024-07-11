from user import *
from login import *
from adminer import *

def updatastatus():
    # 获取当前日期
    current_date = datetime.now().date()
    conn = getconnection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE borrowed_books
        SET status = CASE
            WHEN return_date < ?
            THEN '已超期'
            ELSE '未超期'
        END
    ''', (current_date,))
    conn.commit()
    conn.close()

while True:
    updatastatus()
    using = loggin()
    if using is None:
        print("程序已退出")
        break
    elif isinstance(using, User):
        print(f"欢迎, 用户 {using.name} (用户ID: {using.user_id})")
        # 用户
        while True:
            usermenu()
            try:
                flag = int(input("请输入一个整数："))
            except ValueError:
                print("输入无效，请输入一个整数。")
                continue
            if flag == 1:
                using.borrowbook(using.user_id)
            elif flag == 2:
                using.returnbook(using.user_id)
            elif flag == 3:
                using.queryms()
            elif flag == 4:
                using.querymybook(using.user_id)
            elif flag == 5:
                break
            else:
                print("输入错误，请重新输入：")

    elif isinstance(using, Adminer):
        print(f"欢迎, 管理员 {using.name} (管理员ID: {using.user_id})")
        while True:
            menuadminer()
            try:
                flag = int(input("请输入一个整数："))
            except ValueError:
                print("输入无效，请输入一个整数。")
                continue
            if flag == 1:
                using.bookInput()
            elif flag == 2:
                using.bookModify()
            elif flag == 3:
                using.bookDel()
            elif flag == 4:
                using.bookSearch()
            elif flag == 5:
                using.userSearch()
            elif flag == 6:
                using.chech_borrowed_users()
            elif flag ==7:
                using.chech_users()
            elif flag == 8:
                break
            else:
                print("输入错误，请重新输入：")
        # 在这里添加管理员的操作
