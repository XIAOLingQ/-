import sqlite3
from datetime import datetime

def getconn():
    # 连接数据库的函数，请根据实际情况修改
    return sqlite3.connect('../library/library.db')

class User:
    def __init__(self, user_id, name):
        self.user_id = user_id
        self.name = name

    @staticmethod
    def overtime(user_id):
        """
        检查用户是否有超期未归还的图书
        """
        conn = getconn()
        cur = conn.cursor()
        records = cur.execute("SELECT * FROM borrowed_books WHERE user_id=?", (user_id,)).fetchall()  # 获取用户所有借阅记录
        if not records:
            return 0  # 如果没有借阅记录，返回0

        today = datetime.today()
        overtime_flag = 1
        for record in records:
            if record[4] is not None:
                if today > datetime.strptime(record[4], '%Y-%m-%d') and record[6] == 0:
                    book_info = cur.execute("SELECT id, title FROM books WHERE id=?", (record[2],)).fetchone()
                    print(f"图书编号:{book_info[0]}, 图书名字:{book_info[1]}, 借书时间:{record[3]}, 归还期限:{record[4]}, 状态:{record[5]}, 已超期时间:{(today - datetime.strptime(record[4], '%Y-%m-%d')).days}天")
                    overtime_flag = 0  # 如果有超期书，将标志设置为0
        cur.close()
        conn.close()
        return overtime_flag  # 返回超期状态

    @staticmethod
    def borrowbook(user_id):
        """
        用户借阅图书的函数
        """
        conn = getconn()
        cur = conn.cursor()

        # 判断是否有超期书
        overtime_flag = User.overtime(user_id)
        if overtime_flag == 0:
            print("你有超期图书未归还，请归还后才能借阅")
            return

        # 判断已借图书数量是否超过限制
        row = cur.execute("SELECT COUNT(*) FROM borrowed_books WHERE user_id=?", (user_id,)).fetchone()
        if row[0] >= 2:
            print("对不起，一个账号一次只能借阅两本书，你已经达到数量上限")
            return

        # 输入图书编号或名字
        op = input("输入图书编号或者名字,请选择：")
        if op == '编号':
            number = input("请输入图书编号：")
        else:
            name = input("请输入图书名字：")
            result = cur.execute("SELECT number FROM books WHERE title=?", (name,)).fetchone()
            if result is None:
                print("没有找到该图书")
                cur.close()
                conn.close()
                return
            number = result[0]

        # 查询图书副本数量
        result = cur.execute("SELECT copies FROM books WHERE number=?", (number,)).fetchone()
        if result is None:
            print("没有找到该图书")
            cur.close()
            conn.close()
            return

        available_copies = result[0]
        if available_copies <= 0:
            print("该书已经没有副本可以借阅，请选择其他书籍")
            cur.close()
            conn.close()
            return

        borrowtime = input("请输入借阅时间(yyyy-mm-dd)：")
        returntime = input("请输入归还时间(yyyy-mm-dd)：")

        # 更新数据库，减少可借阅的副本数量
        cur.execute(
            "UPDATE books SET copies = copies - 1 WHERE number = ?", (number,)
        )

        # 将借阅信息插入到 borrowed_books 表
        cur.execute(
            "INSERT INTO borrowed_books (user_id, book_number, borrow_time, return_time) VALUES (?, ?, ?, ?)",
            (user_id, number, borrowtime, returntime)
        )

        conn.commit()
        cur.close()
        conn.close()
        print("借书成功")

    @staticmethod
    def querymybook(user_id):
        """
        查询用户已借图书信息和状态
        """
        conn = getconn()#连接
        cur = conn.cursor()
        records = cur.execute("SELECT * FROM borrowed_books WHERE user_id=?", (user_id,)).fetchall()
        today = datetime.today()
        for record in records:
            if record[4] is not None:
                book_info = cur.execute("SELECT * FROM books WHERE book_id=?", (record[2],)).fetchone()
                overdue_days = (today - datetime.strptime(record[4], '%Y-%m-%d')).days if today > datetime.strptime(record[4], '%Y-%m-%d') else 0
                status = f"已超期{overdue_days}天" if overdue_days else "未超期"
                print(f"图书信息：图书编号:{book_info[0]}, 图书名字:{book_info[1]}, 作者：{book_info[2]}, 出版社：{book_info[3]}, 出版时间：{book_info[4]}, 价格：{book_info[5]}, 副本{book_info[0]}, 借书时间:{record[3]}, 归还期限:{record[4]}，{status}")
        if not records:
            print("信息为空，还未借书")
        cur.close()
        conn.close()

    @staticmethod
    def returnbook(user_id):
        """
        用户还书的函数
        """
        conn = getconn()
        cur = conn.cursor()
        print("你所借图书信息与状态")
        line = "-------------------------------------------"
        print(line)
        User.querymybook(user_id)
        print(line)
        number = input("请输入所还书籍的编号：")
        cur.execute("UPDATE books SET copies = copies + 1 WHERE number = ?", (number,))
        print("还书成功")
        conn.commit()
        cur.close()
        conn.close()

    @staticmethod
    def queryms():
        """
        查询图书信息和状态
        """
        conn = getconn()
        cur = conn.cursor()
        op = input("请输入图书编号或名字查询：")
        if op.isdigit():
            record = cur.execute("SELECT * FROM books WHERE number=?", (op,)).fetchone()
            querycopy(op)
        else:
            record = cur.execute("SELECT * FROM books WHERE name=?", (op,)).fetchone()
            querycopy(record[0])
        cur.close()
        conn.close()

    @staticmethod
    def user():
        """
        用户登录或注册，并进行借书还书等操作
        """
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
    """
    查询图书编号或名字
    """
    option = input("请输入图书编号或名字：")
    if option.isdigit():
        return (option, None)
    else:
        return (None, option)

def querycopy(number):
    """
    查询图书副本状态
    """
    conn = getconn()
    cur = conn.cursor()
    records = cur.execute("SELECT * FROM Bookstate WHERE number=?", (number,)).fetchall()
    for record in records:
        status = "在库" if record[6] == 1 else "不在库"
        print(f"副本{record[0]} 状态：{status}")
    cur.close()
    conn.close()
