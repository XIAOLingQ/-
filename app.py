from flask import Flask
from routes import init_routes

import os
app = Flask(__name__)

app.secret_key = os.urandom(24)

# 初始化路由
init_routes(app)

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)