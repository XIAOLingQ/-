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
        overtime_flag = 1
        for record in records:
            if record[5] == '已超期':
                overtime_flag = 2
        return overtime_flag

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
        op = input("输入(编号) 或 (名字),请选择：")
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

        borrow_date = datetime.now().date()
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
            (max_id + 1, user_id, number, borrow_date.strftime('%Y-%m-%d'), return_date.strftime('%Y-%m-%d'), '未超期')
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
            return -1

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
        a = User.querymybook(user_id)  # Assumes this method prints the user's borrowed books
        print(line)
        if a == -1:
            return
        number = input("请输入所还书籍的编号：")

        cur.execute("UPDATE books SET copies = copies + 1 WHERE id = ?", (number,))

        cur.execute("DELETE FROM borrowed_books WHERE user_id = ? AND book_id = ?", (user_id, number))

        print("还书成功")

        conn.commit()
        cur.close()
        conn.close()

    @staticmethod
    def queryms():
        conn = getconn()
        cur = conn.cursor()
        print("\n")
        print("*************查询图书信息*************")
        order = -1
        while order == -1:
            print("1.查询某本图书")
            print("2.总览图书管所有图书")
            print("3.退出")
            order = int(input("请选择查询操作："))
            if order == 1:
                flag = -1
                while flag == -1:
                    print("1.按图书编号进行查询")
                    print("2.按图书名称进行查询")
                    print("3.退出")
                    flag = int(input("请选择查询方式："))
                    if flag == 1:
                        id = int(input("请输入图书编号："))
                        cur.execute("SELECT COUNT(*) FROM books WHERE id = ?", (id,))
                        if cur.fetchone()[0] == 0:
                            print(f"编号为{id}的图书不存在")
                        else:
                            cur.execute("select * from books where id =?", (id,))
                            conn.commit()
                            print(f"编号为{id}的图书信息如下：")
                            for row in cur:
                                print(
                                    f"编号：{row[0]},书名：{row[1]},作者： {row[2]},出版社： {row[3]},出版日期：{row[4]},价格：{row[5]},副本数量：{row[6]}")
                            cur.close()
                            conn.close()
                    elif flag == 2:
                        title = input("请输入图书名称：")
                        cur.execute("SELECT COUNT(*) FROM books WHERE title = ?", (title,))
                        if cur.fetchone()[0] == 0:
                            print(f"图书<<{title}>>不存在")
                        else:
                            cur.execute("select * from books where title =?", (title,))
                            conn.commit()
                            print(f"图书<<{title}>>的信息如下：")
                            for row in cur:
                                print(
                                    f"编号：{row[0]},书名：{row[1]},作者： {row[2]},出版社： {row[3]},出版日期：{row[4]},价格：{row[5]},副本数量：{row[6]}")
                            cur.close()
                            conn.close()

                    elif flag == 3:
                        return
                    else:
                        flag = -1
                        print("错误的输入，请重新选择！！！")
            elif order == 2:
                print("所有图书信息如下：")
                cur.execute("select * from books ")
                records = cur.fetchall()
                for line in records:
                    print(f"图书编号: {line[0]}, 书名: {line[1]}, 作者: {line[2]}, 出版社: {line[3]}, 出版日期: {line[4]},价格: {line[5]}, 副本数量: {line[6]}")
                cur.close()
                conn.close()
            elif order == 3:
                return
            else:
                order = -1
                print("错误的输入，请重新选择！！！")



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