# api/orders.py
from flask import Blueprint, jsonify, session, request
from utils import get_db_connection, close_db_connection
from mysql.connector import Error

orders_bp = Blueprint('orders', __name__)

# 这是为了查询我的订单
@orders_bp.route('/api/my-orders', methods=['GET'])
def get_my_orders():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"success": False, "msg": "未登录"}), 401

    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # 联查订单 + 车次信息（包含 price）
        query = """
            SELECT
                o.id AS order_id,
                o.status,
                o.group_id,
                t.train_number,
                t.departure,
                t.destination,
                t.departure_time,
                t.price,
                g.applicant_user_id,
                g.status AS group_status,
                g.total_passengers
            FROM orders o
            JOIN trains t ON o.train_id = t.id
            LEFT JOIN group_orders g ON o.group_id = g.group_id
            WHERE o.user_id = %s
            ORDER BY t.departure_time DESC
        """
        cursor.execute(query, (user_id,))
        orders = cursor.fetchall()

        for o in orders:
            o['is_group'] = o['group_id'] is not None
            o['is_applicant'] = (
                o['is_group'] and o['applicant_user_id'] == user_id)
            
        # 格式化时间
        for order in orders:
            if hasattr(order['departure_time'], 'isoformat'):
                order['departure_time'] = order['departure_time'].isoformat()

        return jsonify({"success": True, "data": orders})
    except Error as e:
        print("Get orders error:", e)
        return jsonify({"success": False, "msg": "查询失败"}), 500
    finally:
        close_db_connection(conn, cursor)

# 退票接口
@orders_bp.route('/api/cancel-order', methods=['POST'])
def cancel_order():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"success": False, "msg": "未登录"}), 401

    data = request.get_json()
    order_id = data.get('order_id')
    if not order_id or not isinstance(order_id, int):
        return jsonify({"success": False, "msg": "订单ID无效"}), 400

    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        conn.start_transaction()

        # 1. 查询订单
        cursor.execute("""
            SELECT o.train_id, o.status,o.group_id
            FROM orders o
            WHERE o.id = %s AND o.user_id = %s
        """, (order_id, user_id))
        order = cursor.fetchone()

        if not order:
            raise Exception("订单不存在或无权限操作")
        if order['group_id'] is not None:
            raise Exception("团体票不能单独退票")
        if order['status'] != 'paid':
            raise Exception("只能退还未取消的已支付订单")

        train_id = order['train_id']

        # 2. 更新订单状态
        cursor.execute("UPDATE orders SET status = 'cancelled' WHERE id = %s", (order_id,))

        # 3. 回加余票
        cursor.execute("UPDATE trains SET available_seats = available_seats + 1 WHERE id = %s", (train_id,))

        conn.commit()
        return jsonify({"success": True, "msg": "退票成功！"})
    except Exception as e:
        if conn:
            conn.rollback()
        print("Cancel order error:", e)
        return jsonify({"success": False, "msg": str(e)}), 500
    finally:
        if conn:
            close_db_connection(conn)

#团体退票
@orders_bp.route('/api/cancel-group', methods=['POST'])
def cancel_group():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"success": False, "msg": "未登录"}), 401

    data = request.get_json()
    group_id = data.get('group_id')
    if not group_id:
        return jsonify({"success": False, "msg": "参数错误"}), 400

    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        conn.start_transaction()

        #查询团体订单
        cursor.execute("""
            SELECT train_id, total_passengers, status
            FROM group_orders
            WHERE group_id = %s AND applicant_user_id = %s
        """, (group_id, user_id))
        group = cursor.fetchone()

        if not group:
            raise Exception("无权限操作该团体订单")

        #防止重复退票
        if group['status'] != 'paid':
            raise Exception("该团体订单已退票或不可操作")

        #更新团体订单状态
        cursor.execute("""
            UPDATE group_orders
            SET status = 'cancelled'
            WHERE group_id = %s AND status = 'paid'
        """, (group_id,))

        #更新所有子订单
        cursor.execute("""
            UPDATE orders
            SET status = 'cancelled'
            WHERE group_id = %s
        """, (group_id,))

        #回退余票
        cursor.execute("""
            UPDATE trains
            SET available_seats = available_seats + %s
            WHERE id = %s
        """, (group['total_passengers'], group['train_id']))

        conn.commit()
        return jsonify({"success": True, "msg": "团体退票成功"})

    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({"success": False, "msg": str(e)}), 500
    finally:
        close_db_connection(conn)
