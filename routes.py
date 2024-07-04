import json
import re  # 导入正则表达式模块
import sqlite3

from flask import request, redirect, render_template, url_for, flash, jsonify, session, make_response
from service import *

def init_routes(app):

    @app.route('/', methods=['GET', 'POST'])
    def index():
        return render_template('login.html')

    # 用户菜单页面
    @app.route('/user', methods=['GET', 'POST'])
    def user():
        return render_template('user.html')

    # 管理员菜单页面
    @app.route('/adminer', methods=['GET', 'POST'])
    def adminer():
        return render_template('adminer.html')

    # 登录页面
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'GET':
            return render_template('login.html')
        username = request.form.get('user')
        password = request.form.get('pwd')
        role = request.form.get('role')
        conn = get_connection()
        cursor = conn.cursor()
        # 构建查询字符串
        if role == 'adminer':
            table_name = 'adminer'
        else:
            table_name = 'user'

        query = f"SELECT * FROM {table_name} WHERE username=? AND password=?"
        cursor.execute(query, (username, password))
        result = cursor.fetchone()
        conn.close()
        if result:
            print("登录成功!")
            session['user_id'] = result[0]
            print(session['user_id'])
            if table_name == "user":
                return redirect(url_for('user'))
            else:
                return redirect(url_for('adminer'))
        else:
            return render_template('login.html', msg='用户名、密码或身份输入错误')

    @app.route('/borrow', methods=['GET', 'POST'])
    def borrow_book():
        if request.method == 'GET':
            return render_template('borrow_book.html')

        user_id = session.get('user_id')
        print(session.get('user_id'))
        if request.is_json:
            data = request.get_json()
        else:
            try:
                data = json.loads(request.data)
            except ValueError:
                return jsonify({"error": "Invalid JSON format"}), 400

        if not data:
            response = make_response(json.dumps({'message': '请求数据不完整'}))
            response.mimetype = 'application/json'
            return response, 400

        book_name = data.get('book_name')
        book_id = data.get('book_id')
        if has_overdue_books(user_id) == 2:
            response = make_response(json.dumps({'message': '您有超期未还的书籍，不能继续借阅'}))
            response.mimetype = 'application/json'
            return response, 403

        if count_borrowed_books(user_id):
            response = make_response(json.dumps({'message': '您已借出两本书籍，不能继续借阅'}))
            response.mimetype = 'application/json'
            return response, 409

        if book_name:
            if book_exists_by_name(book_name):
                response = make_response(json.dumps({'message': '未找到相关图书'}))
                response.mimetype = 'application/json'
                return response, 404
            borrow_book_by_name(user_id, book_name)
        elif book_id:
            if book_exists_by_id(book_id):
                response = make_response(json.dumps({'message': '未找到相关图书'}))
                response.mimetype = 'application/json'
                return response, 404
            borrow_book_by_id(user_id, book_id)
        else:
            response = make_response(json.dumps({'message': '请求数据不完整'}))
            response.mimetype = 'application/json'
            return response, 400


        flash(f"图书 {book_id} 已借阅", "success")
        return jsonify({'message': '借阅成功'}), 200


    @app.route('/borrow_logout', methods=['POST','GET'])
    def borrow_logout():
        return redirect(url_for('user'))

    @app.route('/myborrowbooks', methods=['GET'])
    def myborrowbooks():
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({"message": "用户未登录"}), 401

        conn = get_connection()
        cur = conn.cursor()

        # 查询用户的所有借阅记录
        cur.execute("SELECT * FROM borrowed_books WHERE user_id=?", (user_id,))
        records = cur.fetchall()

        books = []
        today = datetime.today().date()

        for record in records:
            cur.execute("SELECT * FROM books WHERE id=?", (record[2],))
            book_info = cur.fetchone()

            if not book_info:
                continue

            if record[4] is not None:
                date_part = re.split(r'[ ]', record[4])[0]
                due_date = datetime.strptime(date_part, '%Y-%m-%d').date()

                if today > due_date:
                    overdue_days = (today - due_date).days
                    status = f"已超期{overdue_days}天"
                else:
                    status = "未超期"
            else:
                status = "无到期日"

            book_details = {
                "borrow_id": record[0],
                "book_id": book_info[0],
                "title": book_info[1],
                "author": book_info[2],
                "publisher": book_info[3],
                "publish_date": book_info[4],
                "price": book_info[5],
                "copies": book_info[6],
                "status": status
            }

            books.append(book_details)

        cur.close()
        conn.close()

        return jsonify(books), 200

    @app.route('/return_logout', methods=['POST', 'GET'])
    def return_logout():
        return redirect(url_for('user'))

    @app.route('/return', methods=['GET','POST'])
    def return_book():
        if request.method == 'GET':
            return render_template('return_book.html')
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({"message": "用户未登录"}), 401

        book_ids = request.form.getlist('book_ids')  # 获取所有选中的 book_ids

        if not book_ids:
            return jsonify({"message": "未选择书籍"}), 400

        conn = get_connection()
        cur = conn.cursor()

        try:
            for book_id in book_ids:
                # 更新书籍数量
                cur.execute("UPDATE books SET copies = copies + 1 WHERE id = ?", (book_id,))
                # 删除借阅记录
                cur.execute("DELETE FROM borrowed_books WHERE user_id = ? AND book_id = ?", (user_id, book_id))

            conn.commit()
        except Exception as e:
            conn.rollback()
            return jsonify({"message": str(e)}), 500
        finally:
            cur.close()
            conn.close()

        return jsonify({"message": "还书成功"}), 200

    @app.route('/query_book', methods=['GET','POST'])
    def query_book():
        if request.method == 'GET':
            return render_template('query_book.html')


        data = request.get_json()
        op = data.get('op')
        if not op:
            return jsonify({"error": "Missing query parameter"}), 400

        conn = get_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500

        try:
            cur = conn.cursor()

            if op.isdigit():
                record = cur.execute("SELECT * FROM books WHERE id=?", (op,)).fetchone()
            else:
                record = cur.execute("SELECT * FROM books WHERE title=?", (op,)).fetchone()

            if record:
                book_id = record[0]
                copies = querycopy(book_id)
                cur.close()
                conn.close()
                return jsonify({
                    "book": {
                        "id": record[0],
                        "title": record[1],
                        "author": record[2],
                        "publisher": record[3]
                    },
                    "copies": copies
                })
            else:
                cur.close()
                conn.close()
                return jsonify({"error": "Book not found"}), 404
        except Exception as e:
            print(f"Error querying book: {e}")
            return jsonify({"error": "An error occurred"}), 500

    @app.route('/query_book_logout', methods=['POST', 'GET'])
    def query_book_logout():
            return redirect(url_for('adminer'))

    @app.route('/query_borrowed_books', methods=['GET', 'POST'])
    def query_borrowed_books():
        user_id = session.get('user_id')
        if not user_id:
            return "User not logged in", 401

        borrowed_books = querymybook(user_id)
        return render_template('query_borrowed_books.html', borrowed_books=borrowed_books)

    @app.route('/query_borrowed_books_logout', methods=['POST', 'GET'])
    def query_borrowed_books_logout():
        return redirect(url_for('user'))

    @app.route('/bookInput', methods=['POST', 'GET'])
    def bookInput():
        if request.method == 'POST':
            title = request.form['book_name']
            author = request.form['book_author']
            publisher = request.form['book_publisher']
            pub_date = request.form['pub_date']
            price = request.form['book_price']
            copies = request.form['copies']

            try:
                conn = get_connection()
                cur = conn.cursor()
                # 获取最大book_id并加1
                cur.execute("SELECT MAX(id) FROM books")
                max_id = cur.fetchone()[0]
                if max_id is None:
                    new_id = 1
                else:
                    new_id = max_id + 1

                cur.execute(
                    "INSERT INTO books (id, title, author, publisher, pub_date, price, copies) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (new_id, title, author, publisher, pub_date, price, copies))
                conn.commit()
                conn.close()
                flash('添加图书成功!', 'success')
            except sqlite3.Error as e:
                flash(f"An error occurred: {e}", 'danger')

        return render_template('bookInput.html')

    @app.route('/bookInput_logout', methods=['POST', 'GET'])
    def bookInput_logout():
        return redirect(url_for('adminer'))

    @app.route('/bookModify', methods=['POST', 'GET'])
    def bookModify():
        return render_template('bookModify.html')

    @app.route('/bookDel', methods=['POST', 'GET'])
    def bookDel():
        return render_template('bookDel.html')

    @app.route('/bookSearch', methods=['POST', 'GET'])
    def bookSearch():
        return render_template('bookSearch.html')

    @app.route('/userSearch', methods=['POST', 'GET'])
    def userSearch():
        return render_template('userSearch.html')

    @app.route('/logout')
    def logout():
        # 在这里处理退出逻辑
        flash("已退出登录", "success")
        return redirect(url_for('login'))
