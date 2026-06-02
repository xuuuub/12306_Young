# app.py
from flask import Flask, send_from_directory
from api.auth import auth_bp
from api.trains import trains_bp
from api.book import book_bp
from api.orders import orders_bp
from api.admin import admin_bp
from api.group_book import group_book_bp

app = Flask(__name__, static_folder='static')
app.secret_key = 'your-secret-key-change-in-production'

# 注册蓝图
app.register_blueprint(auth_bp)
app.register_blueprint(trains_bp)
app.register_blueprint(book_bp)
app.register_blueprint(orders_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(group_book_bp)

# 页面路由
@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/admin')
def admin_page():
    return send_from_directory(app.static_folder, 'admin.html')

@app.route('/main')
def main_page():
    return send_from_directory(app.static_folder, 'main.html')

@app.route('/admin_orders.html')
def admin_orders_page():
    return send_from_directory(app.static_folder, 'admin_orders.html')

@app.route('/admin_trains.html')
def admin_trains_page():
    return send_from_directory(app.static_folder, 'admin_trains.html')

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)