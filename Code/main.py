import sqlite3
from user import *
from login import *
from adminer import *

using = loggin()
if using is None:
    print("程序已退出")
elif isinstance(using, User):
    print(f"欢迎, 用户 {using.name} (用户ID: {using.user_id})")
    #
elif isinstance(using, Adminer):
    print(f"欢迎, 管理员 {using.name} (管理员ID: {using.user_id})")
    # 在这里添加管理员的操作

