# 假设这些函数已经实现了所需的数据库操作
from datetime import datetime, timedelta
import re

from db import get_connection
def has_overdue_books(user_id):
    """
        检查用户是否有超期未归还的图书
    """
    conn = get_connection()
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


def count_borrowed_books(user_id):
    conn = get_connection()
    cur = conn.cursor()
    row = cur.execute("SELECT COUNT(*) FROM borrowed_books WHERE user_id=?", (user_id,)).fetchone()
    if row[0] >= 2:
        return  True
    else:
        return False

def book_exists_by_name(book_name):
    conn = get_connection()
    cur = conn.cursor()
    result = cur.execute("SELECT title FROM books WHERE title=?", (book_name,)).fetchone()
    if result is None:
        print("没有找到该图书")
        cur.close()
        conn.close()
        return True
    else:
        return False

def book_exists_by_id(book_id):
    conn = get_connection()
    cur = conn.cursor()
    result = cur.execute("SELECT id FROM books WHERE id=?", (book_id,)).fetchone()
    if result is None:
        print("没有找到该图书")
        cur.close()
        conn.close()
        return True
    else:
        return False


def borrow_book_by_name(user_id, book_name):
    conn = get_connection()
    cur = conn.cursor()

    # 检查是否存在该图书名
    result = cur.execute("SELECT id, copies FROM books WHERE title=?", (book_name,)).fetchone()
    if result is None:
        print("没有找到该图书名")
        cur.close()
        conn.close()
        return False

    book_id, available_copies = result
    if available_copies <= 0:
        print("该书已经没有副本可以借阅，请选择其他书籍")
        cur.close()
        conn.close()
        return False

    borrow_date = datetime.now().date()
    return_date = borrow_date + timedelta(days=30)
    print(f"还书期限是30天，到期时间是：{return_date.strftime('%Y-%m-%d')}")

    # 更新数据库，减少可借阅的副本数量
    cur.execute("UPDATE books SET copies = copies - 1 WHERE id = ?", (book_id,))

    # 查找 borrowed_books 表中的最大 ID
    cur.execute("SELECT MAX(id) FROM borrowed_books")
    max_id = cur.fetchone()[0]
    if max_id is None:
        max_id = 0

    # 将借阅信息插入到 borrowed_books 表
    cur.execute(
        "INSERT INTO borrowed_books (id, user_id, book_id, borrow_date, return_date, status) VALUES (?, ?, ?, ?, ?, ?)",
        (max_id + 1, user_id, book_id, borrow_date.strftime('%Y-%m-%d'), return_date.strftime('%Y-%m-%d'), "未超期")
    )

    conn.commit()
    cur.close()
    conn.close()
    return True


def borrow_book_by_id(user_id, book_id):
    print(user_id)
    conn = get_connection()
    cur = conn.cursor()

    # 检查是否存在该图书名
    result = cur.execute("SELECT id, copies FROM books WHERE id=?", (book_id,)).fetchone()
    if result is None:
        print("没有找到该图书编号")
        cur.close()
        conn.close()
        return False

    book_id, available_copies = result
    if available_copies <= 0:
        print("该书已经没有副本可以借阅，请选择其他书籍")
        cur.close()
        conn.close()
        return False

    borrow_date = datetime.now().date()
    return_date = borrow_date + timedelta(days=30)
    print(f"还书期限是30天，到期时间是：{return_date.strftime('%Y-%m-%d')}")

    # 更新数据库，减少可借阅的副本数量
    cur.execute("UPDATE books SET copies = copies - 1 WHERE id = ?", (book_id,))

    # 查找 borrowed_books 表中的最大 ID
    cur.execute("SELECT MAX(id) FROM borrowed_books")
    max_id = cur.fetchone()[0]
    if max_id is None:
        max_id = 0

    # 将借阅信息插入到 borrowed_books 表
    cur.execute(
        "INSERT INTO borrowed_books (id, user_id, book_id, borrow_date, return_date, status) VALUES (?, ?, ?, ?, ?, ?)",
        (max_id + 1, user_id, book_id, borrow_date.strftime('%Y-%m-%d'), return_date.strftime('%Y-%m-%d'), "未超期")
    )

    conn.commit()
    cur.close()
    conn.close()
    return True

def querycopy(book_id):
    conn = get_connection()
    cur = conn.cursor()
    copies = cur.execute("SELECT copies FROM books WHERE id=?", (book_id,)).fetchall()
    cur.close()
    conn.close()
    return copies


def querymybook(user_id):
    """
    查询用户已借图书信息和状态
    """
    conn = get_connection()
    cur = conn.cursor()
    records = cur.execute("SELECT * FROM borrowed_books WHERE user_id=?", (user_id,)).fetchall()
    today = datetime.today().date()  # 获取今天的日期（不包括时间部分）

    book_list = []

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

            # 获取图书信息并存入列表
            book_info = cur.execute("SELECT * FROM books WHERE id=?", (record[2],)).fetchone()
            if book_info:
                book_list.append({
                    'book_id': book_info[0],
                    'book_name': book_info[1],
                    'author': book_info[2],
                    'publisher': book_info[3],
                    'publish_date': book_info[4],
                    'price': book_info[5],
                    'copy_id': book_info[0],
                    'borrow_date': record[3],
                    'due_date': record[4],
                    'status': status
                })
            else:
                book_list.append({
                    'book_id': None,
                    'book_name': '未找到对应的图书信息',
                    'author': '',
                    'publisher': '',
                    'publish_date': '',
                    'price': '',
                    'copy_id': '',
                    'borrow_date': '',
                    'due_date': '',
                    'status': ''
                })

    cur.close()
    conn.close()

    return book_list