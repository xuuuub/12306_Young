# api/auth.py
from flask import Blueprint, request, jsonify, session
from utils import get_db_connection, close_db_connection
from mysql.connector import Error

auth_bp = Blueprint('auth', __name__)

# 用户注册
@auth_bp.route('/api/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    real_name = data.get('real_name')
    idcard = data.get('idcard')

    if not username or not password:
        return jsonify({"success": False, "msg": "用户名和密码不能为空"}), 400
    if len(idcard) != 18:
        return jsonify({"success": False, "msg": "身份证号格式错误"}), 400
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # 检查用户名是否已存在
        cursor.execute("SELECT id FROM users WHERE username = %s OR idcard = %s", 
                        (username,idcard))
        if cursor.fetchone():   
            return jsonify({"success": False, "msg": "用户名或身份证已存在"}), 409

        # 插入新用户
        cursor.execute(
            "INSERT INTO users (username, password,real_name,idcard) VALUES (%s, %s,%s,%s)",
            (username, password,real_name,idcard)
        )
        conn.commit()
        return jsonify({"success": True, "msg": "注册成功！"})
    
    except Error as e:
        print("Register DB error:", e)
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        close_db_connection(conn, cursor)

# 用户登录
@auth_bp.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"success": False, "msg": "用户名或密码为空"}), 400

    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT id,role FROM users WHERE username = %s AND password = %s",
            (username, password)
        )
        user = cursor.fetchone()
        if user:
            session['user_id'] = user['id']
            session['role'] = user['role']
            redirect_page = '/admin' if user['role'] == 'admin' else '/main'
            return jsonify({"success": True, "redirect": redirect_page})
        else:
            return jsonify({"success": False, "msg": "用户名或密码错误"}), 401
    except Error as e:
        print("Login DB error:", e)
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        close_db_connection(conn, cursor)

# 修改密码
@auth_bp.route('/api/change_password', methods=['POST'])
def change_password():
    data = request.json
    username = data.get('username')
    idcard = data.get('idcard')
    new_password = data.get('new_password')

    if not username or not idcard or not new_password:
        return jsonify({"success": False, "msg": "参数不完整"}), 400

    if len(idcard) != 18:
        return jsonify({"success": False, "msg": "身份证号格式错误"}), 400

    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            "SELECT id FROM users WHERE username = %s AND idcard = %s",
            (username, idcard)
        )
        user = cursor.fetchone()

        if not user:
            return jsonify({"success": False, "msg": "用户名或身份证不匹配"}), 401

        cursor.execute(
            "UPDATE users SET password = %s WHERE username = %s",
            (new_password, username)
        )
        conn.commit()

        return jsonify({"success": True, "msg": "密码修改成功"})

    except Error as e:
        print("Change password DB error:", e)
        return jsonify({"success": False, "msg": "服务器错误"}), 500
    finally:
        close_db_connection(conn, cursor)



# 用户退出登录
@auth_bp.route('/api/logout', methods=['POST'])
def logout():
    session.pop('user_id', None)  # 清除用户ID
    return jsonify({"success": True, "msg": "已退出登录"})

    