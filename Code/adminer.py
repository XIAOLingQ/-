import sqlite3


class Adminer:
    def __init__(self, user_id, name):
        self.user_id = user_id
        self.name = name

    # 在类里面实现功能
    # 连接数据库
    def getConnection(self):
        dbstring = "../library/library.db"
        con = sqlite3.connect(dbstring)
        cur = con.cursor()
        return con

    # 录入图书信息
    def bookInput(self):
        conn = self.getConnection()
        cur = conn.cursor()
        print("\n")
        print("*************图书录入*************")
        amount = 0
        while amount <= 0:
            try:
                amount = int(input("请输入录入图书的数量: "))
            except ValueError:
                print("请输入一个有效的数字")
                amount = 0
        for i in range(amount):
            cur.execute("SELECT MAX(id) FROM books")
            max_id = cur.fetchone()[0]
            if max_id is None:
                new_id = 1
            else:
                new_id = max_id + 1
            print(f"第{i + 1}本书的信息:")
            title = input("请输入图书名称:")
            author = input("请输入作者:")
            publisher = input("请输入出版商:")
            pub_date = input("请输入出版日期:")
            price = input("请输入图书价格:")
            copies = input("请输入图书副本量:")
            try:
                cur.execute("insert into books(id,title,author,publisher,pub_date,price,copies)"
                            "values(?,?,?,?,?,?,?)", (new_id, title, author, publisher, pub_date, price, copies))
            except sqlite3.Error as e:
                print("An error occurred:", e)

        conn.commit()
        conn.close()
        print("***************新增图书成功！！！***************")

    # 修改图书信息
    def bookModify(self):
        conn = self.getConnection()
        cur = conn.cursor()
        print("\n")
        print("*************图书信息修改*************")
        book_name = input("请输入你要修改信息的图书的名字:")

        # 检查图书是否存在
        cur.execute("SELECT COUNT(*) FROM books WHERE title = ?", (book_name,))
        if cur.fetchone()[0] == 0:
            print(f"图书 {book_name} 不存在，无法修改。")
            conn.close()
            return

            # 显示修改选项
        print("请选择要修改的字段：")
        print("1. 作者")
        print("2. 出版商")
        print("3. 出版日期")
        print("4. 价格")
        print("5. 副本数量")
        print("输入多项请用逗号分隔（例如：1,2,3）：")
        choices = input("请输入选择：").split(',')

        updates = []
        params = []

        for choice in choices:
            choice = choice.strip()
            if choice == '1':
                author = input("请输入修改后的作者：")
                updates.append("author = ?")
                params.append(author)
            elif choice == '2':
                publisher = input("请输入修改后的出版商：")
                updates.append("publisher = ?")
                params.append(publisher)
            elif choice == '3':
                pub_date = input("请输入修改后的出版日期：")
                updates.append("pub_date = ?")
                params.append(pub_date)
            elif choice == '4':
                price = float(input("请输入修改后的价格："))
                updates.append("price = ?")
                params.append(price)
            elif choice == '5':
                copies = int(input("请输入修改后的副本数量："))
                updates.append("copies = ?")
                params.append(copies)

            if not updates:
                print("没有选择任何字段进行修改。")
                conn.close()
                return
        # 构建 SQL 更新语句
        sqlstring = f"UPDATE books SET {', '.join(updates)} WHERE title = ?"
        params.append(book_name)

        try:
            cur.execute(sqlstring, params)
            conn.commit()
            print(f"****************图书<<{book_name}>>的信息修改成功！！！************")
        except sqlite3.Error as e:
            print("An error occurred:", e)
        finally:
            conn.close()

    # 删除图书信息
    def bookDel(self):
        conn = self.getConnection()
        cur = conn.cursor()
        print("\n")
        print("*************图书删除*************")
        flag = -1
        while flag == -1:
            print("1.按图书编号进行删除")
            print("2.按图书名称进行删除")
            print("3.退出")
            flag = int(input("请选择删除方式："))
            if flag == 1:
                id = int(input("请输入图书编号："))
                cur.execute("SELECT COUNT(*) FROM books WHERE id = ?", (id,))
                if cur.fetchone()[0] == 0:
                    print(f"编号为{id}的图书不存在，无需删除")
                else:
                    cur.execute("delete from books where id =?", (id,))
                    print(f"*************编号为{id}的图书已成功删除！！！*************")
                    conn.commit()
                    conn.close()
            elif flag == 2:
                title = int(input("请输入图书名称："))
                cur.execute("SELECT COUNT(*) FROM books WHERE title = ?", (title,))
                if cur.fetchone()[0] == 0:
                    print(f"图书<<{title}>>不存在，无需删除")
                else:
                    cur.execute("delete from books where title =?", (title,))
                    print(f"*************图书<<{title}>>已成功删除！！！*************")
                    conn.commit()
                    conn.close()
            elif flag == 3:
                return
            else:
                flag = -1
                print("错误的输入，请重新选择！！！")

    # 查询图书信息
    def bookSearch(self):
        conn = self.getConnection()
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

    # 查询任意用户借书状态
    def userSearch(self):
        conn = self.getConnection()
        cur = conn.cursor()
        print("*************查询任意用户借书状态*************")
        id = int(input("请输入所要查询的用户id："))
        # 检查用户是否存在
        cur.execute("SELECT COUNT(*) FROM user WHERE id = ?", (id,))
        if cur.fetchone()[0] == 0:
            print(f"id为 {id}的用户不存在")
            conn.close()
            return
        else:
            cur.execute("SELECT COUNT(*) FROM borrowed_books WHERE user_id = ?", (id,))
            if cur.fetchone()[0] == 0:
                print(f"id为 {id}的用户借书记录为空")
                conn.close()
            else:
                cur.execute("SELECT * FROM borrowed_books WHERE user_id = ?", (id,))
                records = cur.fetchall()
                for line in records:
                    cur.execute("SELECT title FROM books WHERE id = ?", (line[2],))
                    title = cur.fetchall()
                    print(f"图书编号：{line[2]} 书名《{title[0][0]}》 借书时间：{line[3]} 还书期限：{line[4]} {line[5]}")
                cur.close()
                conn.close()

    def chech_borrowed_users(self):
        conn = self.getConnection()
        cur = conn.cursor()
        cur.execute("SELECT bb.*,aa.name,cc.title FROM borrowed_books bb,user aa,books cc where bb.user_id = aa.id and bb.book_id =cc.id")
        records = cur.fetchall()
        for record in records:
            print(
                f"借书编号: {record[0]}, 姓名: {record[6]}, 书名: {record[7]}, 借书日期: {record[3]}, 还书日期: {record[4]},状态: {record[5]}")
        cur.close()
        conn.close()



def menuadminer():
    print("**************管理员***************")
    print("1.录入图书信息     2.修改图书信息    3.删除图书信息")
    print("4.查询图书信息     5.查询任意用户借书状态 6.查询所有用户的借书状态")
    print("7.退出")

