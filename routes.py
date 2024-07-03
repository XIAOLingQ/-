import json
import re  # 导入正则表达式模块
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

    @app.route('/query', methods=['GET', 'POST'])
    def query_book():
        if request.method == 'GET':
            return render_template('query_book.html')
        book_id = request.form.get('book_id')
        # 在这里处理查询图书信息和状态的逻辑
        flash(f"查询图书 {book_id} 信息", "success")
        return redirect(url_for('user'))

    @app.route('/query_borrowed', methods=['GET', 'POST'])
    def query_borrowed_books():
        if request.method == 'GET':
            return render_template('query_borrowed_books.html')
        user_id = request.form.get('user_id')
        # 在这里处理查询已借图书信息和状态的逻辑
        flash(f"查询用户 {user_id} 已借图书信息", "success")
        return redirect(url_for('user'))

    @app.route('/logout')
    def logout():
        # 在这里处理退出逻辑
        flash("已退出登录", "success")
        return redirect(url_for('login'))


