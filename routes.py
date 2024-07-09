import json
import re  # 导入正则表达式模块
import sqlite3
from functools import wraps

from flask import request, redirect, render_template, url_for, flash, jsonify, session, make_response
from service import *




def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def init_routes(app):
    @app.before_request
    def before_request():
        allowed_routes = ['index', 'login']
        if request.endpoint not in allowed_routes and 'user_id' not in session:
            # flash('请先登录', 'danger')
            return redirect(url_for('login'))

    @app.route('/', methods=['GET', 'POST'])
    def index():
        return render_template('login.html')

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'GET':
            return render_template('login.html')
        username = request.form.get('user')
        password = request.form.get('pwd')
        role = request.form.get('role')
        conn = get_connection()
        cursor = conn.cursor()
        if role == 'adminer':
            table_name = 'adminer'
        else:
            table_name = 'user'

        query = f"SELECT * FROM {table_name} WHERE username=? AND password=?"
        cursor.execute(query, (username, password))
        result = cursor.fetchone()
        conn.close()
        if result:
            session['user_id'] = result[0]
            if table_name == "user":
                return redirect(url_for('user'))
            else:
                return redirect(url_for('adminer'))
        else:
            return render_template('login.html', msg='用户名、密码或身份输入错误')

    @app.route('/user', methods=['GET', 'POST'])
    @login_required
    def user():
        return render_template('user.html')

    @app.route('/adminer', methods=['GET', 'POST'])
    @login_required
    def adminer():
        return render_template('adminer.html')

    @app.route('/borrow', methods=['GET', 'POST'])
    @login_required
    def borrow_book():
        if request.method == 'GET':
            return render_template('borrow_book.html')
        user_id = session.get('user_id')
        if request.is_json:
            data = request.get_json()
        else:
            try:
                data = json.loads(request.data)
            except ValueError:
                return jsonify({"error": "Invalid JSON format"}), 400

        if not data:
            return jsonify({'message': '请求数据不完整'}), 400

        book_name = data.get('book_name')
        book_id = data.get('book_id')
        if has_overdue_books(user_id) == 2:
            return jsonify({'message': '您有超期未还的书籍，不能继续借阅'}), 403

        if count_borrowed_books(user_id):
            return jsonify({'message': '您已借出两本书籍，不能继续借阅'}), 409

        if book_name:
            if not book_exists_by_name(book_name):
                return jsonify({'message': '未找到相关图书'}), 404
            borrow_book_by_name(user_id, book_name)
        elif book_id:
            if not book_exists_by_id(book_id):
                return jsonify({'message': '未找到相关图书'}), 404
            borrow_book_by_id(user_id, book_id)
        else:
            return jsonify({'message': '请求数据不完整'}), 400

        flash(f"图书 {book_id} 已借阅", "success")
        return jsonify({'message': '借阅成功'}), 200

    @app.route('/myborrowbooks', methods=['GET'])
    @login_required
    def myborrowbooks():
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({"message": "用户未登录"}), 401

        conn = get_connection()
        cur = conn.cursor()
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

    @app.route('/return', methods=['GET', 'POST'])
    @login_required
    def return_book():
        if request.method == 'GET':
            return render_template('return_book.html')
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({"message": "用户未登录"}), 401

        book_ids = request.form.getlist('book_ids')
        if not book_ids:
            return jsonify({"message": "未选择书籍"}), 400

        conn = get_connection()
        cur = conn.cursor()
        try:
            for book_id in book_ids:
                cur.execute("UPDATE books SET copies = copies + 1 WHERE id = ?", (book_id,))
                cur.execute("DELETE FROM borrowed_books WHERE user_id = ? AND book_id = ?", (user_id, book_id))
            conn.commit()
        except Exception as e:
            conn.rollback()
            return jsonify({"message": str(e)}), 500
        finally:
            cur.close()
            conn.close()
        return jsonify({"message": "还书成功"}), 200

    @app.route('/query_book', methods=['GET', 'POST'])
    @login_required
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
            return jsonify({"error": "An error occurred"}), 500

    @app.route('/query_borrowed_books', methods=['GET', 'POST'])
    @login_required
    def query_borrowed_books():
        user_id = session.get('user_id')
        if not user_id:
            return "User not logged in", 401

        borrowed_books = querymybook(user_id)
        return render_template('query_borrowed_books.html', borrowed_books=borrowed_books)

    @app.route('/bookInput', methods=['POST', 'GET'])
    @login_required
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

    @app.route('/bookModify', methods=['POST', 'GET'])
    @login_required
    def bookModify():
        if request.method == 'POST':
            book_name = request.form['book_name']
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM books WHERE title = ?", (book_name,))
            if cur.fetchone()[0] == 0:
                flash(f"图书'{book_name}' 不存在", 'danger')
                conn.close()
                return render_template('modify_book.html')

            id = request.form['id']
            author = request.form['author']
            publisher = request.form['publisher']
            pub_date = request.form['pub_date']
            price = request.form['price']
            copies = request.form['copies']

            try:
                sqlstring = """
                        UPDATE books 
                        SET book_id = ?, author = ?, publisher = ?, pub_date = ?, price = ?, copies = ?
                        WHERE title = ?
                    """
                cur.execute(sqlstring, (id, author, publisher, pub_date, price, copies, book_name))
                conn.commit()
                flash(f"图书'{book_name}' 信息修改成功!", 'success')
            except sqlite3.Error as e:
                flash(f"An error occurred: {e}", 'danger')
            finally:
                conn.close()
        return render_template('bookModify.html')

    @app.route('/bookDel', methods=['POST', 'GET'])
    @login_required
    def bookDel():
        if request.method == 'POST':
            delete_method = request.form['delete_method']
            if delete_method == 'id':
                book_id = request.form['book_id']
                try:
                    conn = get_connection()
                    cur = conn.cursor()
                    cur.execute("SELECT COUNT(*) FROM books WHERE id = ?", (book_id,))
                    if cur.fetchone()[0] == 0:
                        flash(f"编号为{book_id}的图书不存在，无需删除", 'danger')
                    else:
                        cur.execute("DELETE FROM books WHERE id = ?", (book_id,))
                        conn.commit()
                        flash(f"编号为{book_id}的图书已成功删除！", 'success')
                    conn.close()
                except sqlite3.Error as e:
                    flash(f"发生错误: {e}", 'danger')
            elif delete_method == 'title':
                book_title = request.form['book_title']
                try:
                    conn = get_connection()
                    cur = conn.cursor()
                    cur.execute("SELECT COUNT(*) FROM books WHERE title = ?", (book_title,))
                    if cur.fetchone()[0] == 0:
                        flash(f"图书《{book_title}》不存在，无需删除", 'danger')
                    else:
                        cur.execute("DELETE FROM books WHERE title = ?", (book_title,))
                        conn.commit()
                        flash(f"图书《{book_title}》已成功删除！", 'success')
                    conn.close()
                except sqlite3.Error as e:
                    flash(f"发生错误: {e}", 'danger')
            return redirect(url_for('bookDel'))
        return render_template('bookDel.html')

    @app.route('/bookSearch', methods=['POST', 'GET'])
    @login_required
    def bookSearch():
        books = []
        if request.method == 'POST':
            search_type = request.form['search_type']
            if search_type == 'id':
                book_id = request.form['book_id']
                try:
                    conn = get_connection()
                    cur = conn.cursor()
                    cur.execute("SELECT * FROM books WHERE id = ?", (book_id,))
                    books = cur.fetchall()
                    if not books:
                        flash(f"编号为{book_id}的图书不存在", 'danger')
                    conn.close()
                except sqlite3.Error as e:
                    flash(f"发生错误: {e}", 'danger')
            elif search_type == 'title':
                book_title = request.form['book_title']
                try:
                    conn = get_connection()
                    cur = conn.cursor()
                    cur.execute("SELECT * FROM books WHERE title = ?", (book_title,))
                    books = cur.fetchall()
                    if not books:
                        flash(f"图书《{book_title}》不存在", 'danger')
                    conn.close()
                except sqlite3.Error as e:
                    flash(f"发生错误: {e}", 'danger')
            elif search_type == 'all':
                try:
                    conn = get_connection()
                    cur = conn.cursor()
                    cur.execute("SELECT * FROM books")
                    books = cur.fetchall()
                    conn.close()
                except sqlite3.Error as e:
                    flash(f"发生错误: {e}", 'danger')
        return render_template('bookSearch.html', books=books)


    @app.route('/bookSearch_user', methods=['POST', 'GET'])
    @login_required
    def bookSearch_user():
        books = []
        if request.method == 'POST':
            search_type = request.form['search_type']
            if search_type == 'id':
                book_id = request.form['book_id']
                try:
                    conn = get_connection()
                    cur = conn.cursor()
                    cur.execute("SELECT * FROM books WHERE id = ?", (book_id,))
                    books = cur.fetchall()
                    if not books:
                        flash(f"编号为{book_id}的图书不存在", 'danger')
                    conn.close()
                except sqlite3.Error as e:
                    flash(f"发生错误: {e}", 'danger')
            elif search_type == 'title':
                book_title = request.form['book_title']
                try:
                    conn = get_connection()
                    cur = conn.cursor()
                    cur.execute("SELECT * FROM books WHERE title = ?", (book_title,))
                    books = cur.fetchall()
                    if not books:
                        flash(f"图书《{book_title}》不存在", 'danger')
                    conn.close()
                except sqlite3.Error as e:
                    flash(f"发生错误: {e}", 'danger')
            elif search_type == 'all':
                try:
                    conn = get_connection()
                    cur = conn.cursor()
                    cur.execute("SELECT * FROM books")
                    books = cur.fetchall()
                    conn.close()
                except sqlite3.Error as e:
                    flash(f"发生错误: {e}", 'danger')
        return render_template('bookSearch_user.html', books=books)

    @app.route('/userSearch', methods=['POST', 'GET'])
    @login_required
    def userSearch():
        borrowed_books = []
        if request.method == 'POST':
            user_id = request.form['user_id']
            try:
                conn = get_connection()
                cur = conn.cursor()
                records = cur.execute("SELECT * FROM borrowed_books WHERE user_id=?", (user_id,)).fetchall()
                today = datetime.today().date()

                for record in records:
                    if record[4] is not None:
                        date_part = re.split(r'[ ]', record[4])[0]
                        due_date = datetime.strptime(date_part, '%Y-%m-%d').date()

                        if today > due_date:
                            overdue_days = (today - due_date).days
                            status = f"已超期{overdue_days}天"
                        else:
                            status = "未超期"

                        book_info = cur.execute("SELECT * FROM books WHERE id=?", (record[2],)).fetchone()
                        if book_info:
                            borrowed_books.append({
                                'book_id': book_info[0],
                                'title': book_info[1],
                                'author': book_info[2],
                                'publisher': book_info[3],
                                'pub_date': book_info[4],
                                'price': book_info[5],
                                'copies': book_info[6],
                                'borrow_date': record[3],
                                'due_date': record[4],
                                'status': status
                            })
                conn.close()
                if not borrowed_books:
                    flash("信息为空，还未借书", 'info')
            except sqlite3.Error as e:
                flash(f"发生错误: {e}", 'danger')
        return render_template('userSearch.html', borrowed_books=borrowed_books)

    @app.route('/logout')
    def logout():
        session.clear()
        return redirect(url_for('login'))