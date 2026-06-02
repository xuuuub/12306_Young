# api/admin.py
from flask import request, Blueprint, jsonify, session
from utils import get_db_connection, close_db_connection
from datetime import datetime

admin_bp = Blueprint('admin', __name__)

# 管理员查看所有订单（含用户、车次信息）
@admin_bp.route('/api/admin/orders', methods=['GET'])
def get_all_orders():
    """管理员查看所有订单（含用户、车次信息）"""
    # 权限校验
    if session.get('role') != 'admin':
        return jsonify({"success": False, "msg": "权限不足"}), 403

    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        query = """
            SELECT 
                o.id AS order_id,
                u.username AS user_name,
                t.train_number,
                t.departure,
                t.destination,
                t.departure_time,
                o.order_time,
                o.status,
                o.group_id
            FROM orders o
            JOIN users u ON o.user_id = u.id
            JOIN trains t ON o.train_id = t.id
            ORDER BY o.order_time DESC
        """

        cursor.execute(query)
        orders = cursor.fetchall()

        for o in orders:
            o['is_group'] = o['group_id'] is not None

        # 格式化时间
        for order in orders:
            if hasattr(order['departure_time'], 'isoformat'):
                order['departure_time'] = order['departure_time'].isoformat()
            if hasattr(order['order_time'], 'isoformat'):
                order['order_time'] = order['order_time'].isoformat()

        return jsonify({"success": True, "data": orders})

    except Exception as e:
        print("Admin get orders error:", e)
        return jsonify({"success": False, "msg": "查询失败"}), 500
    finally:
        close_db_connection(conn, cursor)


# 添加新列车
@admin_bp.route('/api/admin/add-train', methods=['POST'])
def add_train():
    """管理员添加新列车"""
    if session.get('role') != 'admin':
        return jsonify({"success": False, "msg": "权限不足"}), 403

    data = request.get_json()
    
    #参数校验
    required_fields = ['train_number', 'departure', 'destination', 'departure_time', 'total_seats','price']
    for field in required_fields:
        if not data.get(field):
            return jsonify({"success": False, "msg": f"缺少必要字段: {field}"}), 400

    train_number = data['train_number'].strip()
    departure = data['departure'].strip()
    destination = data['destination'].strip()
    total_seats = data['total_seats']
    #验证票价
    try:
        price = float(data['price'])
        if price < 0:
            return jsonify({"success": False, "msg": "票价不能为负数"}), 400
    except (ValueError, TypeError):
        return jsonify({"success": False, "msg": "票价必须是有效数字"}), 400

    #验证时间格式 "2025-12-20T14:30"
    try:
        departure_time = datetime.fromisoformat(data['departure_time'])
    except ValueError:
        return jsonify({"success": False, "msg": "出发时间格式无效，请使用 YYYY-MM-DDTHH:mm 格式"}), 400

    #余票 = 总座位数
    available_seats = total_seats

    # 验证座位数
    if not isinstance(total_seats, int) or total_seats <= 0:
        return jsonify({"success": False, "msg": "总座位数必须是大于0的整数"}), 400

    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # 检查车次号是否已存在（避免重复）
        cursor.execute("SELECT id FROM trains WHERE train_number = %s", (train_number,))
        if cursor.fetchone():
            return jsonify({"success": False, "msg": "车次号已存在，请使用不同的车次号"}), 409

        #插入
        insert_query = """
            INSERT INTO trains (
                train_number, 
                departure, 
                destination, 
                departure_time, 
                total_seats, 
                available_seats,
                price
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(insert_query, (
            train_number,
            departure,
            destination,
            departure_time,
            total_seats,
            available_seats,
            price
        ))
        conn.commit()

        return jsonify({"success": True, "msg": "新列车添加成功！"})

    except Exception as e:
        print("Add train error:", e)
        conn.rollback()
        return jsonify({"success": False, "msg": "服务器内部错误"}), 500
    finally:
        close_db_connection(conn, cursor)


# 更新车次时间以及票价。
@admin_bp.route('/api/admin/update-train', methods=['POST'])
def update_train():
    if session.get('role') != 'admin':
        return jsonify({'success': False, 'msg': '无权限'}), 403

    data = request.get_json()

    old_train_number = data.get('old_train_number')
    new_train_number = data.get('new_train_number')
    departure_time = data.get('departure_time')
    price = data.get('price')

    if not all([old_train_number, new_train_number, departure_time, price]):
        return jsonify({'success': False, 'msg': '参数不完整'}), 400

    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        conn.start_transaction()

        #查找旧车次
        cursor.execute("""
            SELECT id
            FROM trains
            WHERE train_number = %s
            FOR UPDATE
        """, (old_train_number,))
        train = cursor.fetchone()

        if not train:
            raise Exception('旧车次号不存在')

        train_id = train['id']

        #更新信息
        cursor.execute("""
            UPDATE trains
            SET train_number = %s,
                departure_time = %s,
                price = %s
            WHERE id = %s
        """, (new_train_number, departure_time, price, train_id))

        conn.commit()
        return jsonify({'success': True, 'msg': '车次信息修改成功'})

    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({'success': False, 'msg': str(e)}), 500
    finally:
        close_db_connection(conn, cursor)


#获取所有用户列表
@admin_bp.route('/api/admin/users', methods=['GET'])
def get_all_users():
    if session.get('role') != 'admin':
        return jsonify({"success": False, "msg": "权限不足"}), 403

    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, username, role FROM users ORDER BY id ASC")
        users = cursor.fetchall()
        return jsonify({"success": True, "data": users})
    except Exception as e:
        print("Get users error:", e)
        return jsonify({"success": False, "msg": "查询失败"}), 500
    finally:
        close_db_connection(conn, cursor)


# 修改用户等级
@admin_bp.route('/api/admin/update-user-role', methods=['POST'])
def update_user_role():
    if session.get('role') != 'admin':
        return jsonify({"success": False, "msg": "权限不足"}), 403

    data = request.get_json()
    user_id = data.get('user_id')
    new_role = data.get('role')

    if not user_id or new_role not in ['user', 'admin']:
        return jsonify({"success": False, "msg": "参数无效"}), 400

    # 防止管理员把自己降级
    if user_id == session.get('user_id') and new_role == 'user':
        return jsonify({"success": False, "msg": "不能将自己降级为普通用户"}), 400

    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # 检查用户是否存在
        cursor.execute("SELECT id FROM users WHERE id = %s", (user_id,))
        if not cursor.fetchone():
            return jsonify({"success": False, "msg": "用户不存在"}), 404

        # 更新用户
        cursor.execute("UPDATE users SET role = %s WHERE id = %s", (new_role, user_id))
        conn.commit()

        return jsonify({"success": True, "msg": "用户角色更新成功"})
    except Exception as e:
        print("Update user role error:", e)
        conn.rollback()
        return jsonify({"success": False, "msg": "操作失败"}), 500
    finally:
        close_db_connection(conn, cursor)


# 后台强制退票
@admin_bp.route('/api/admin/cancel-order', methods=['POST'])
def admin_cancel_order():
    #管理员权限校验
    if session.get('role') != 'admin':
        return jsonify({"success": False, "msg": "无管理员权限"}), 403

    data = request.get_json()
    order_id = data.get('order_id')

    if not order_id:
        return jsonify({"success": False, "msg": "缺少订单ID"}), 400

    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        conn.start_transaction()

        #查询订单+是否团体票
        cursor.execute("""
            SELECT 
                o.id AS order_id,
                o.status AS order_status,
                o.group_id,
                o.train_id
            FROM orders o
            WHERE o.id = %s
            FOR UPDATE
        """, (order_id,))
        order = cursor.fetchone()

        if not order:
            raise Exception("订单不存在")

        if order['order_status'] != 'paid':
            raise Exception("该订单已取消或不可操作")

        #情况一：单人票（group_id IS NULL）=====
        if not order['group_id']:
            # 查询车次（锁）
            cursor.execute("""
                SELECT available_seats, total_seats
                FROM trains
                WHERE id = %s
                FOR UPDATE
            """, (order['train_id'],))
            train = cursor.fetchone()

            if not train:
                raise Exception("车次不存在")

            # 更新订单状态
            cursor.execute("""
                UPDATE orders
                SET status = 'cancelled'
                WHERE id = %s
            """, (order_id,))

            # 回退 1 个座位（防止超上限）
            cursor.execute("""
                UPDATE trains
                SET available_seats = LEAST(available_seats + 1, total_seats)
                WHERE id = %s
            """, (order['train_id'],))

            conn.commit()
            return jsonify({
                "success": True,
                "msg": "单人票已强制退票"
            })

        #情况二：团体票（整团退
        group_id = order['group_id']

        # 1 查询团体订单
        cursor.execute("""
            SELECT train_id, total_passengers, status
            FROM group_orders
            WHERE group_id = %s
            FOR UPDATE
        """, (group_id,))
        group = cursor.fetchone()

        if not group:
            raise Exception("团体订单不存在")

        if group['status'] != 'paid':
            raise Exception("团体订单已退或不可操作")

        # 2 取消该团体下的所有订单
        cursor.execute("""
            UPDATE orders
            SET status = 'cancelled'
            WHERE group_id = %s
              AND status = 'paid'
        """, (group_id,))

        # 3 取消团体主订单
        cursor.execute("""
            UPDATE group_orders
            SET status = 'cancelled'
            WHERE group_id = %s
        """, (group_id,))

        # 4 回退座位（按团体人数）
        cursor.execute("""
            UPDATE trains
            SET available_seats = LEAST(
                available_seats + %s,
                total_seats
            )
            WHERE id = %s
        """, (group['total_passengers'], group['train_id']))

        conn.commit()
        return jsonify({
            "success": True,
            "msg": f"团体票已强制退票（共 {group['total_passengers']} 张）"
        })

    except Exception as e:
        if conn:
            conn.rollback()
        print("Admin cancel order error:", e)
        return jsonify({
            "success": False,
            "msg": str(e)
        }), 500

    finally:
        close_db_connection(conn, cursor)
