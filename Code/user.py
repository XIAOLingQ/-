import sqlite3
from datetime import datetime, timedelta
import re  # 导入正则表达式模块

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
        records = cur.execute("SELECT * FROM borrowed_books WHERE user_id=?", (user_id,)).fetchall()
        if not records:
            return 0  # 如果没有借阅记录，返回0

        today = datetime.today().date()
        overtime_flag = 1
        for record in records:
            if len(record) >= 7 and record[4] is not None and record[6] == 0:
                due_date = datetime.strptime(record[4], '%Y-%m-%d').date()
                if today > due_date:
                    book_info = cur.execute("SELECT id, title FROM books WHERE id=?", (record[2],)).fetchone()
                    if book_info:
                        print(
                            f"图书编号:{book_info[0]}, 图书名字:{book_info[1]}, 借书时间:{record[3]}, 归还期限:{record[4]}, 状态:{record[5]}")
                    else:
                        print("未找到对应的图书信息")
                    overtime_flag = 2  # 如果有超期书，将标志设置为0

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
        if overtime_flag == 2:
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
            result = cur.execute("SELECT id FROM books WHERE title=?", (name,)).fetchone()
            if result is None:
                print("没有找到该图书")
                cur.close()
                conn.close()
                return
            number = result[0]

        # 查询图书副本数量
        result = cur.execute("SELECT copies FROM books WHERE id=?", (number,)).fetchone()
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
        borrow_date = datetime.strptime(borrowtime, "%Y-%m-%d").date()
        return_date = borrow_date + timedelta(days=30)
        print(f"还书期限是30天，到期时间是：{return_date.strftime('%Y-%m-%d')}")

        # 更新数据库，减少可借阅的副本数量
        cur.execute("UPDATE books SET copies = copies - 1 WHERE id = ?", (number,))

        # 查最大id
        cur.execute("SELECT MAX(id) FROM borrowed_books")
        max_id = cur.fetchone()[0]
        if max_id is None:
            max_id = 0

        # 将借阅信息插入到 borrowed_books 表
        cur.execute(
            "INSERT INTO borrowed_books (id, user_id, book_id, borrow_date, return_date, status) VALUES (?, ?, ?, ?, ?, ?)",
            (max_id + 1, user_id, number, borrow_date.strftime('%Y-%m-%d'), return_date.strftime('%Y-%m-%d'), 0)
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
        conn = getconn()
        cur = conn.cursor()
        records = cur.execute("SELECT * FROM borrowed_books WHERE user_id=?", (user_id,)).fetchall()
        today = datetime.today().date()  # 获取今天的日期（不包括时间部分）

        for record in records:
            if record[4] is not None:
                # 使用正则表达式去除时间部分
                date_part = re.split(r'[ ]', record[4])[0]
                due_date = datetime.strptime(date_part, '%Y-%m-%d').date()

                # 计算是否超期
                if today > due_date:
                    overdue_days = (today - due_date).days
                    status = f"已超期{overdue_days}天"
                else:
                    status = "未超期"

                # 获取图书信息并打印
                book_info = cur.execute("SELECT * FROM books WHERE id=?", (record[2],)).fetchone()
                if book_info:
                    print(f"图书信息：图书编号:{book_info[0]}, 图书名字:{book_info[1]}, 作者：{book_info[2]}, 出版社：{book_info[3]}, 出版时间：{book_info[4]}, 价格：{book_info[5]}, 副本{book_info[0]}, 借书时间:{record[3]}, 归还期限:{record[4]}，{status}")
                else:
                    print("未找到对应的图书信息")

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
        User.querymybook(user_id)  # Assumes this method prints the user's borrowed books
        print(line)

        number = input("请输入所还书籍的编号：")

        # Check if the user has borrowed this book
        cur.execute("SELECT * FROM borrowed_books WHERE user_id = ? AND book_id = ?", (user_id, number))
        record = cur.fetchone()
        if record is None:
            print("你未借过该图书")
        else:
            # Update the books table to increase the number of copies
            cur.execute("UPDATE books SET copies = copies + 1 WHERE id = ?", (number,))

            # Delete the borrowed book record from borrowed_books table
            cur.execute("DELETE FROM borrowed_books WHERE user_id = ? AND book_id = ?", (user_id, number))

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
        try:
            if op.isdigit():
                record = cur.execute("SELECT * FROM books WHERE id=?", (op,)).fetchone()
            else:
                record = cur.execute("SELECT * FROM books WHERE title=?", (op,)).fetchone()

            if record:
                querycopy(record[0])
            else:
                print("未找到对应的图书信息")
        except Exception as e:
            print(f"查询过程中发生错误: {e}")
        finally:
            cur.close()
            conn.close()



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
    records = cur.execute("SELECT * FROM books WHERE id=?", (number,)).fetchall()
    for record in records:
        status = "在库" if record[6] > 0 else "不在库"
        print(f"副本{record[6]}本 状态：{status}")
    cur.close()
    conn.close()

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
    records = cur.execute("SELECT * FROM books WHERE id=?", (number,)).fetchall()
    for record in records:
        status = "在库" if record[6] > 0 else "不在库"
        print(f"副本{record[0]}本 状态：{status}")
    cur.close()
    conn.close()

def usermenu():
    print("**************用户***************")
    print("1.借阅图书   2.归还图书   3.查询图书信息和状态")
    print("4.查询已借图书信息和状态    5.退出")