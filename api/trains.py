# api/trains.py
from flask import Blueprint, request, jsonify
from utils import get_db_connection, close_db_connection
from datetime import datetime

trains_bp = Blueprint('trains', __name__)

@trains_bp.route('/api/trains', methods=['GET'])
def search_trains():
    # 获取查询参数（允许为空）
    departure = request.args.get('departure', '').strip()
    destination = request.args.get('destination', '').strip()
    date_str = request.args.get('date', '').strip()  # 格式：YYYY-MM-DD

    # 构建 SQL 查询
    query = """
    SELECT id,
        train_number,
        departure,
        destination,
        departure_time,
        available_seats,
        price,
        is_pre_sal
    FROM trains
    WHERE 1=1
    """
    
    query += " AND is_pre_sal IN ('0','1')"
    params = []

    if departure:
        query += " AND departure = %s"
        params.append(departure)
    if destination:
        query += " AND destination = %s"
        params.append(destination)
    if date_str:
        try:
            # 验证日期格式
            datetime.strptime(date_str, '%Y-%m-%d')
            # 匹配当天的所有车次（忽略时分秒）
            query += " AND DATE(departure_time) = %s"
            params.append(date_str)
        except ValueError:
            return jsonify({'success': False, 'msg': '日期格式错误，应为 YYYY-MM-DD'}), 400

    # 按发车时间排序
    query += " ORDER BY departure_time ASC"

    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, params)
        trains = cursor.fetchall()
        return jsonify({'success': True, 'data': trains})
    except Exception as e:
        print(f"数据库查询错误: {e}")
        return jsonify({'success': False, 'msg': '服务器内部错误'}), 500
    finally:
        if conn:
            close_db_connection(conn)