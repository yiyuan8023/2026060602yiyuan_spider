def get_all_table_structures(connection_config: dict, database_name: str) -> dict:
    """
    获取指定数据库中所有表的创建SQL语句
    
    Args:
        connection_config (dict): 数据库连接配置
        database_name (str): 数据库名称
    
    Returns:
        dict: 表名和对应创建SQL语句的字典
    """
    import mysql.connector
    import re

    # 存储表结构的字典
    table_structures = {}

    try:
        # 连接数据库
        conn = mysql.connector.connect(**connection_config)
        cursor = conn.cursor()

        # 获取所有表名
        cursor.execute(f"SHOW TABLES FROM `{database_name}`")
        tables = cursor.fetchall()

        if not tables:
            print(f"数据库 '{database_name}' 中没有找到任何表")
            return table_structures

        # 遍历每个表，获取创建语句
        for table_row in tables:
            table_name = table_row[0]
            try:
                # 获取表的创建语句
                cursor.execute(f"SHOW CREATE TABLE `{database_name}`.`{table_name}`")
                result = cursor.fetchone()

                if result:
                    # result[1] 包含创建表的SQL语句
                    create_table_sql = result[1]
                    # 移除数据库名前缀
                    create_table_sql = re.sub(rf'`{database_name}`\.', '', create_table_sql)
                    table_structures[table_name] = create_table_sql
                    print(f"成功获取表 '{table_name}' 的结构")
                else:
                    print(f"无法获取表 '{table_name}' 的结构")

            except mysql.connector.Error as e:
                print(f"获取表 '{table_name}' 结构时出错: {e}")
                continue

        cursor.close()
        conn.close()

        print(f"共获取 {len(table_structures)} 个表的结构")
        return table_structures

    except mysql.connector.Error as e:
        print(f"MySQL连接错误: {e}")
        return table_structures
    except Exception as e:
        print(f"获取表结构时出错: {e}")
        return table_structures


# 使用示例
if __name__ == "__main__":
    # 数据库连接配置
    db_config = {
        'host': '10.20.3.122',
        'user': 'root',
        'password': 'jide2025',
        'port': 3306
    }

    db_name = 'project'
    # 获取数据库中所有表的结构
    table_structures = get_all_table_structures(db_config, db_name)

    # 打印结果
    for table_name, create_sql in table_structures.items():
        print(f"\n表名: {table_name}")
        print(f"创建语句: {create_sql}")
