import mysql.connector
from mysql.connector import Error
import sys
from datetime import datetime # 用于添加时间戳

def connect_to_database():
    """连接到 MySQL 数据库"""
    connection = None
    try:
        # --- 配置数据库连接信息 ---
        # 请务必根据你的实际环境修改以下信息
        connection = mysql.connector.connect(
            host='localhost', 
            database='train_ticket', 
            user='train_user',    
            password='train123456'
        )
        if connection.is_connected():
            print("成功连接到 MySQL 数据库 (train_ticket)")
            return connection
    except Error as e:
        print(f"连接 MySQL 时发生错误: {e}")
        return None

def export_table_info_and_data(connection, output_file_path):
    """获取表结构和数据并写入文件"""
    try:
        cursor = connection.cursor()

        tables_to_export = ['group_orders', 'group_passengers', 'orders', 'users', 'trains']

        with open(output_file_path, 'w', encoding='utf-8') as f:
            f.write("--- MySQL Database Export Report ---\n")
            f.write(f"Export Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n") # 添加时间戳
            f.write("------------------------------------\n\n")

            for table_name in tables_to_export:
                print(f"正在处理表: {table_name} ...")
                f.write(f"--- Structure of table: {table_name} ---\n")
                # 执行 DESCRIBE 查询
                cursor.execute(f"DESCRIBE {table_name}")
                columns = cursor.fetchall()
                # 获取列名 (cursor.description 包含列信息)
                col_names = [desc[0] for desc in cursor.description]
                f.write("\t".join(col_names) + "\n")
                for row in columns:
                    f.write("\t".join(str(cell) for cell in row) + "\n")
                f.write("\n")

                f.write(f"--- Content of table: {table_name} ---\n")
                # 执行 SELECT * 查询
                cursor.execute(f"SELECT * FROM {table_name}") 
                rows = cursor.fetchall()
                # 写入列名
                if rows: # 如果表不为空
                    f.write("\t".join(str(desc[0]) for desc in cursor.description) + "\n")
                    # 写入数据行
                    for row in rows:
                        f.write("\t".join(str(cell) if cell is not None else 'NULL' for cell in row) + "\n")
                else:
                    f.write("(Table is empty)\n")
                f.write("\n--- End of table: {table_name} ---\n\n")

        print(f"所有表的结构和数据已成功导出到: {output_file_path}")

    except Error as e:
        print(f"执行查询或写入文件时发生错误: {e}")
    finally:
        if cursor:
            cursor.close()


def export_procedures(connection, output_file_path):
    """获取所有存储过程的定义并追加写入文件"""
    try:
        cursor = connection.cursor()

        # 查询当前数据库的所有存储过程
        query = """
        SELECT routine_name, routine_definition
        FROM information_schema.routines
        WHERE routine_type = 'PROCEDURE' AND routine_schema = %s
        ORDER BY routine_name;
        """
        cursor.execute(query, (connection.database,)) # 使用连接对象的database属性
        procedures = cursor.fetchall()

        with open(output_file_path, 'a', encoding='utf-8') as f: 
            f.write("\n--- Stored Procedures in Database: train_ticket ---\n")
            if procedures:
                for proc_name, proc_definition in procedures:
                    print(f"正在导出存储过程: {proc_name} ...")
                    f.write(f"\n--- Procedure: {proc_name} ---\n")
                    f.write(f"{proc_definition}\n")
                    f.write("-- End of Procedure --\n")
            else:
                f.write("\n(No stored procedures found in database 'train_ticket'.)\n")
            f.write("\n--- End of Stored Procedures Export ---\n")

        print(f"所有存储过程已成功追加导出到: {output_file_path}")

    except Error as e:
        print(f"导出存储过程时发生错误: {e}")
    finally:
        if cursor:
            cursor.close()


def main():
    # --- 定义输出文件路径 ---
    output_path = "/home/xb/桌面/trian_ticket/data/data.txt" 

    connection = connect_to_database()
    if connection and connection.is_connected():
        # 先导出表结构和数据
        export_table_info_and_data(connection, output_path)
        # 再导出存储过程
        export_procedures(connection, output_path)
        connection.close()
        print("MySQL 连接已关闭")
    else:
        print("无法建立数据库连接，程序退出。")
        sys.exit(1) # 非正常退出

if __name__ == "__main__":
    main()