import numpy as np
import pandas as pd


def df_to_dict(df):
    """
    将DataFrame转换为字典列表，只做基本的转换和容错处理
    Args:
        df (pd.DataFrame): 输入的DataFrame
    Returns:
        list: 字典列表
    """

    def clean_value(value):
        """清理单个值"""
        if pd.isna(value) or value is None:
            return ""
        elif isinstance(value, (int, float)):
            if pd.isna(value) or np.isinf(value):
                return ""
            return value
        else:
            return str(value)

    def clean_column_name(col_name):
        """清理列名"""
        if pd.isna(col_name) or col_name is None:
            return ""
        return str(col_name)

    # 输入验证
    if not isinstance(df, pd.DataFrame):
        raise TypeError("输入必须是pandas DataFrame")

    if df.empty:
        return []

    try:
        # 清理列名
        df_clean = df.copy()
        clean_columns = {col: clean_column_name(col) for col in df_clean.columns}
        df_clean = df_clean.rename(columns=clean_columns)

        # 转换为字典
        dict_list = df_clean.to_dict('records')

        # 清理每个字典项的值
        cleaned_dict_list = []
        for item in dict_list:
            cleaned_item = {}
            for key, value in item.items():
                clean_key = clean_column_name(key)
                if clean_key:  # 只保留有效的列名
                    cleaned_item[clean_key] = clean_value(value)
            cleaned_dict_list.append(cleaned_item)

        return cleaned_dict_list

    except Exception as e:
        print(f"转换DataFrame时出错: {e}")
        return []


def dict_to_df(dict_list):
    """
    将字典列表转换为DataFrame，只做基本的转换和容错处理
    Args:
        dict_list (list): 字典列表
    Returns:
        pd.DataFrame: 转换后的DataFrame
    """

    # 输入验证
    if not isinstance(dict_list, list):
        raise TypeError("输入必须是字典列表")

    if not dict_list:
        return pd.DataFrame()

    # 验证每个元素都是字典
    for item in dict_list:
        if not isinstance(item, dict):
            raise TypeError("列表中的每个元素都必须是字典")

    try:
        # 转换为DataFrame
        df = pd.DataFrame(dict_list)

        # 处理空值
        # 将空字符串替换为NaN（可选）
        df = df.replace("", np.nan)

        return df

    except Exception as e:
        print(f"转换字典到DataFrame时出错: {e}")
        return pd.DataFrame()
