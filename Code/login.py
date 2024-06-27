import sqlite3

def getConnection():
    dbstring="E:\Code\Python\专业综合训练Ⅱ\library\library.db"
    conn=sqlite3.connect(dbstring)
    return conn
def login(username, password):

    # 连接数据库
    conn = getConnection()
    cursor = conn.cursor()

    # 查询表log
    cursor.execute("SELECT identity FROM log WHERE username = ? AND password = ?", (username, password))
    result = cursor.fetchone()

    # 关闭数据库连接
    conn.close()

    # 根据查询结果返回相应的值
    if result:
        identity = result[0]
        if identity == 'amdiner':
            return 1
        elif identity == 'user':
            return 0
    return -1  # 如果用户名或密码不正确，返回-1



def getidentity():
    while(1):
        print("1.登录")
        print("2.退出")
        a = input("请选择：")
        if a == "1" :
            username = input("请输入用户名:")
            password = input("请输入密码:")
            login_result = login(username, password)
            if login_result == 1:
                print("登录成功，身份是管理员。")
                return 1
            elif login_result == 0:
                print("登录成功，身份是用户。")
                return 0
            else:
                print("用户名或密码不正确。")
        elif a=="2" :
            return -1