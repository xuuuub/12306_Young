# api/book.py
from flask import Blueprint, request, jsonify, session
from utils import get_db_connection, close_db_connection
import logging

book_bp = Blueprint('book', __name__)

@book_bp.route('/api/book', methods=['POST'])
def book_ticket():
    # 检查用户是否登录
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'msg': '请先登录'}), 401

    data = request.get_json()
    train_id = data.get('train_id')

    if not train_id or not isinstance(train_id, int):
        return jsonify({'success': False, 'msg': '车次ID无效'}), 400

    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # 开启事务
        conn.start_transaction()

        # 1. 查询车次余票（加行锁防止并发超卖）
        cursor.execute("SELECT available_seats FROM trains WHERE id = %s FOR UPDATE", (train_id,))
        train = cursor.fetchone()
        if not train:
            raise Exception("车次不存在")
        
        if train['available_seats'] <= 0:
            raise Exception("余票不足，无法购买")

        # 2. 插入订单
        cursor.execute(
            "INSERT INTO orders (user_id, train_id, status) VALUES (%s, %s, 'paid')",
            (user_id, train_id)
        )

        # 3. 扣减余票
        cursor.execute(
            "UPDATE trains SET available_seats = available_seats - 1 WHERE id = %s",
            (train_id,)
        )

        # 提交事务
        conn.commit()

        return jsonify({'success': True, 'msg': '购票成功！'})

    except Exception as e:
        if conn:
            conn.rollback()
        logging.error(f"购票失败: {e}")
        return jsonify({'success': False, 'msg': str(e) if '余票' in str(e) else '购票失败，请重试'}), 500
    finally:
        if conn:
            close_db_connection(conn)