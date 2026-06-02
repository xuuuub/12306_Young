# utils.py
import mysql.connector
from mysql.connector import Error
from config import DB_CONFIG

def get_db_connection():
    """返回数据库连接"""
    return mysql.connector.connect(**DB_CONFIG)

def close_db_connection(conn, cursor=None):
    """安全关闭连接和游标"""
    if cursor:
        cursor.close()
    if conn and conn.is_connected():
        conn.close()