import sqlite3
from datetime import datetime

def getconn():
    # 连接数据库的函数，请根据实际情况修改
    return sqlite3.connect('./library/library.db')

class User:
    def __init__(self, user_id, name):
        self.user_id = user_id
        self.name = name

    @staticmethod
    def register():
        conn = getconn()
        cur = conn.cursor()
        username = input("请输入注册账号：")
        password = input("请输入注册密码：")
        cur.execute("INSERT INTO Login (username, password) VALUES (?, ?)", (username, password))
        print(f"注册成功！账号：{username},密码：{password}")
        conn.commit()
        cur.close()
        conn.close()

    @staticmethod
    def overtime(username):
        conn = getconn()
        cur = conn.cursor()
        records = cur.execute("SELECT * FROM Bookstate WHERE username=?", (username,)).fetchall()
        if not records:
            return 0
        today = datetime.today()
        overtime_flag = 1
        for record in records:
            if record[4] is not None:
                if today > datetime.strptime(record[4], '%Y-%m-%d') and record[6] == 0:
                    book_info = cur.execute("SELECT number, name FROM Book WHERE number=?", (record[1],)).fetchone()
                    print(f"图书编号:{book_info[0]},图书名字:{book_info[1]},借书时间:{record[3]},归还期限:{record[4]},已超期时间:{(today - datetime.strptime(record[4], '%Y-%m-%d')).days}天")
                    overtime_flag = 0
        cur.close()
        conn.close()
        return overtime_flag

    @staticmethod
    def borrowbook(username):
        conn = getconn()
        cur = conn.cursor()
        overtime_flag = User.overtime(username)
        if overtime_flag == 0:
            print("你有超期图书未归还，请归还后才能借阅")
            return
        row = cur.execute("SELECT COUNT(*) FROM Bookstate WHERE username=?", (username,)).fetchone()
        if row[0] >= 2:
            print("对不起，一个账号一次只能借阅两本书，你已经达到数量上限")
            return
        op = input("输入图书编号或者名字,请选择：")
        if op == '编号':
            number = input("请输入图书编号：")
        else:
            name = input("请输入图书名字：")
            number = cur.execute("SELECT number FROM Book WHERE name=?", (name,)).fetchone()[0]
        records = cur.execute("SELECT * FROM Bookstate WHERE number=?", (number,)).fetchall()
        num = sum(1 for record in records if record[6] == 1)
        if num == 0:
            print("该书已经没有副本可以借阅，请选择其他书籍")
            cur.close()
            conn.close()
            return
        borrowtime = input("请输入借阅时间(yyyy-mm-dd)：")
        returntime = input("请输入归还时间(yyyy-mm-dd)：")
        id_to_borrow = next(record[0] for record in records if record[6] == 1)
        cur.execute("UPDATE Bookstate SET status=?, borrowtime=?, returntime=?, flag=0, username=? WHERE id=? AND number=?", ("不在库", borrowtime, returntime, username, id_to_borrow, number))
        conn.commit()
        cur.close()
        conn.close()

    @staticmethod
    def querymybook(username):
        conn = getconn()
        cur = conn.cursor()
        records = cur.execute("SELECT * FROM Bookstate WHERE username=?", (username,)).fetchall()
        today = datetime.today()
        for record in records:
            if record[4] is not None:
                book_info = cur.execute("SELECT * FROM Book WHERE number=?", (record[1],)).fetchone()
                overdue_days = (today - datetime.strptime(record[4], '%Y-%m-%d')).days if today > datetime.strptime(record[4], '%Y-%m-%d') else 0
                status = f"已超期{overdue_days}天" if overdue_days else "未超期"
                print(f"图书信息：图书编号:{book_info[0]},图书名字:{book_info[1]},作者：{book_info[2]},出版社：{book_info[3]},出版时间：{book_info[4]},价格：{book_info[5]},副本{record[0]},借书时间:{record[3]},归还期限:{record[4]}，{status}")
        if not records:
            print("信息为空，还未借书")
        cur.close()
        conn.close()

    @staticmethod
    def returnbook(username):
        conn = getconn()
        cur = conn.cursor()
        print("你所借图书信息与状态")
        line = "-------------------------------------------"
        print(line)
        User.querymybook(username)
        print(line)
        number = input("请输入所还书籍的编号：")
        cur.execute("UPDATE Bookstate SET status=?, borrowtime=?, returntime=?, flag=1, username=? WHERE number=? AND username=?", ('在库', None, None, None, number, username))
        print("还书成功")
        conn.commit()
        cur.close()
        conn.close()

    @staticmethod
    def queryms():
        conn = getconn()
        cur = conn.cursor()
        op = input("请输入图书编号或名字查询：")
        if op.isdigit():
            record = cur.execute("SELECT * FROM Book WHERE number=?", (op,)).fetchone()
            querycopy(op)
        else:
            record = cur.execute("SELECT * FROM Book WHERE name=?", (op,)).fetchone()
            querycopy(record[0])
        cur.close()
        conn.close()

    @staticmethod
    def log():
        conn = getconn()
        cur = conn.cursor()
        username = input("请输入账号：")
        password = input("请输入密码：")
        user = cur.execute("SELECT * FROM Login WHERE username=? AND password=?", (username, password)).fetchone()
        cur.close()
        conn.close()
        if user:
            print(f"登录成功，欢迎 {username}!")
            return (1, username)
        else:
            print("登录失败，账号或密码错误")
            return (0, None)

    @staticmethod
    def user():
        flag = 1
        op = 2
        ch = 2
        while ch == 2:
            ch = int(input("登录账户：1   注册账户：2   请输入选项："))
            if ch == 1:
                op = User.log()
            elif ch == 2:
                User.register()
        if op[0] == 1:
            while flag == 1:
                line = "--------------------用户界面-----------------------"
                print(line)
                print("退出用户界面：0    借书：1    还书：2 ")
                print("查询图书信息和状态：3     查询自己已借图书信息和状态：4")
                status = int(input("请输入选项:"))
                if status == 0:
                    break
                elif status == 1:
                    User.borrowbook(op[1])
                elif status == 2:
                    User.returnbook(op[1])
                elif status == 3:
                    User.queryms()
                elif status == 4:
                    User.querymybook(op[1])
                else:
                    print("没有该选项")
                flag = int(input("继续操作输入1，退出输入0："))
        else:
            print("欢迎下次光临！")

# 辅助函数
def querybook():
    option = input("请输入图书编号或名字：")
    if option.isdigit():
        return (option, None)
    else:
        return (None, option)

def querycopy(number):
    conn = getconn()
    cur = conn.cursor()
    records = cur.execute("SELECT * FROM Bookstate WHERE number=?", (number,)).fetchall()
    for record in records:
        status = "在库" if record[6] == 1 else "不在库"
        print(f"副本{record[0]} 状态：{status}")
    cur.close()
    conn.close()
