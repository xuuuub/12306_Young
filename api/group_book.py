from flask import Blueprint, request, jsonify, session
from utils import get_db_connection, close_db_connection
from datetime import datetime

group_book_bp = Blueprint('group_book', __name__)

@group_book_bp.route('/api/group-book', methods=['POST'])
def group_book():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'msg': '未登录'}), 401

    data = request.get_json()
    train_id = data.get('train_id')
    passengers = data.get('passengers')

    #基本参数校验
    if not train_id or not isinstance(passengers, list) or len(passengers) <= 1:
        return jsonify({'success': False, 'msg': '参数错误'}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        conn.start_transaction()

        #查询车次并锁行
        cursor.execute("""
            SELECT price, available_seats
            FROM trains
            WHERE id = %s
            FOR UPDATE
        """, (train_id,))
        train = cursor.fetchone()

        if not train:
            raise Exception("车次不存在")

        total_passengers = len(passengers)

        if train['available_seats'] < total_passengers:
            raise Exception("余票不足")

        #防止同一身份证重复买同一趟车
        seen_idcards = set()
        for p in passengers:
            real_name = p.get('real_name')
            idcard = p.get('idcard')

            if not real_name or not idcard or len(idcard) != 18:
                raise Exception("乘客信息不合法")

            if idcard in seen_idcards:
                raise Exception("同一身份证不能重复添加")
            seen_idcards.add(idcard)

            cursor.execute("""
                SELECT 1
                FROM orders o
                JOIN users u ON o.user_id = u.id
                WHERE u.idcard = %s
                  AND o.train_id = %s
                  AND o.status = 'paid'
                LIMIT 1
            """, (idcard, train_id))

            if cursor.fetchone():
                raise Exception(f"身份证 {idcard} 已购买该车次，不能重复购票")

        #生成 group_id
        group_id = (
            f"G{datetime.now().strftime('%Y%m%d%H%M%S')}"
            f"_T{train_id}_U{user_id}_P{total_passengers}"
        )

        total_amount = train['price'] * total_passengers

        #插入group_orders
        cursor.execute("""
            INSERT INTO group_orders
            (group_id, applicant_user_id, train_id, total_passengers, total_amount, status)
            VALUES (%s,%s,%s,%s,%s,'paid')
        """, (group_id, user_id, train_id, total_passengers, total_amount))

        #处理每一个乘客
        for p in passengers:
            real_name = p['real_name']
            idcard = p['idcard']

            # 查是否有账号
            cursor.execute(
                "SELECT id FROM users WHERE idcard = %s",
                (idcard,)
            )
            u = cursor.fetchone()
            if not u:
                raise Exception(f"身份证 {idcard} 尚未注册，请先注册账号")

            passenger_user_id = u['id']

            # 插 group_passengers
            cursor.execute("""
                INSERT INTO group_passengers
                (group_id, user_id, real_name, idcard)
                VALUES (%s,%s,%s,%s)
            """, (group_id, passenger_user_id, real_name, idcard))

            # 插 orders（让对应账号能看到票）
            cursor.execute("""
                INSERT INTO orders
                (user_id, train_id, status, group_id)
                VALUES (%s,%s,'paid',%s)
            """, (passenger_user_id, train_id, group_id))

        #扣减余票
        cursor.execute("""
            UPDATE trains
            SET available_seats = available_seats - %s
            WHERE id = %s
        """, (total_passengers, train_id))

        conn.commit()
        return jsonify({
            'success': True,
            'group_id': group_id
        })

    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'msg': str(e)}), 500
    finally:
        close_db_connection(conn, cursor)
