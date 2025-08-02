from typing import Dict, Any, List, Union

import mysql.connector


def copy_mysql_tables_structure_safe(
    source_config: Dict[str, Any],
    target_config: Dict[str, Any],
    table_names: Union[str, List[str]],
    source_database: str,
    target_database: str,
    drop_if_exists: bool = False
) -> bool:
    """
    安全地从源MySQL数据库复制一个或多个表结构到目标MySQL数据库

    Args:
        source_config (dict): 源数据库连接配置
        target_config (dict): 目标数据库连接配置
        table_names (str or list): 要复制结构的表名或表名列表
        source_database (str): 源数据库名称
        target_database (str): 目标数据库名称
        drop_if_exists (bool): 如果目标表存在是否删除重建

    Returns:
        bool: 操作是否全部成功
    """
    # 标准化表名为列表格式
    if isinstance(table_names, str):
        table_names = [table_names]

    if not table_names:
        print("未提供要复制的表名")
        return False

    source_conn = None
    target_conn = None
    success_count = 0

    try:
        # 连接源数据库
        source_conn = mysql.connector.connect(**source_config)
        source_cursor = source_conn.cursor()

        # 获取所有表的创建语句
        table_structures = {}
        for table_name in table_names:
            try:
                source_cursor.execute(f"SHOW CREATE TABLE `{source_database}`.`{table_name}`")
                result = source_cursor.fetchone()

                if not result:
                    print(f"警告: 表 '{table_name}' 在源数据库 '{source_database}' 中不存在，跳过")
                    continue

                create_table_sql = result[1]
                # 移除可能的数据库名前缀
                import re
                create_table_sql = re.sub(rf'`{source_database}`\.', '', create_table_sql)
                table_structures[table_name] = create_table_sql

            except mysql.connector.Error as e:
                print(f"获取表 '{table_name}' 结构时出错: {e}")
                continue

        source_cursor.close()
        source_conn.close()

        if not table_structures:
            print("没有有效的表结构可以复制")
            return False

        # 连接目标数据库
        target_conn = mysql.connector.connect(**target_config)
        target_cursor = target_conn.cursor()

        # 选择目标数据库
        target_cursor.execute(f"USE `{target_database}`")

        # 处理每个表
        for table_name, create_table_sql in table_structures.items():
            try:
                # 检查目标表是否存在
                target_cursor.execute(f"SHOW TABLES LIKE '{table_name}'")
                table_exists = target_cursor.fetchone() is not None

                if table_exists:
                    if drop_if_exists:
                        # 删除已存在的表
                        target_cursor.execute(f"DROP TABLE `{table_name}`")
                        print(f"已删除目标数据库中已存在的表 '{table_name}'")
                    else:
                        print(f"表 '{table_name}' 在目标数据库中已存在，操作取消")
                        continue

                # 创建表
                target_cursor.execute(create_table_sql)
                success_count += 1
                print(f"成功在 '{target_database}' 数据库中创建表 '{table_name}'")

            except mysql.connector.Error as e:
                print(f"创建表 '{table_name}' 时出错: {e}")
                continue

        target_conn.commit()
        target_cursor.close()
        target_conn.close()

        print(f"成功复制 {success_count}/{len(table_names)} 个表结构")
        return success_count == len(table_names) or (success_count > 0 and len(table_names) > 0)

    except mysql.connector.Error as e:
        print(f"MySQL错误: {e}")
        return False
    except Exception as e:
        print(f"复制表结构时出错: {e}")
        return False
    finally:
        # 确保连接被关闭
        if source_conn and source_conn.is_connected():
            source_conn.close()
        if target_conn and target_conn.is_connected():
            target_conn.close()


# 使用示例
if __name__ == "__main__":
    # 数据库连接配置
    source_db_config = {
        'host': '10.20.3.122',
        'user': 'root',
        'password': 'jide2025',
        'port': 3306
    }

    target_db_config = {
        'host': '223.5.242.173',
        'user': 'bc_yiyuan_test',
        'password': 'yiyuan12345678',
        'port': 3306
    }

    table_name_list = ['tb_tg_万相台无界_基础报表_人群报表_202504',
                   'tb_tg_万相台无界_基础报表_宝贝主体_202504',
                   'tb_tg_万相台无界_基础报表_关键词_202504']


    # 复制多个表结构
    success = copy_mysql_tables_structure_safe(
        source_config=source_db_config,
        target_config=target_db_config,
        table_names=table_name_list,  # 多个表
        source_database='project',
        target_database='yiyuan_test',
        drop_if_exists = False
    )
    
    if success:
        print("表结构复制成功")
    else:
        print("表结构复制失败")
