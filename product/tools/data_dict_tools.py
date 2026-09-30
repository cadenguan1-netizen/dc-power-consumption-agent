import os
import pandas as pd
from langchain_core.tools import tool

DATA_DICT_PATH = "/Users/mac/Documents/Caden/2026年暑假实习项目/能源数据/数据字典信息表.xlsx"


@tool
def query_data_dictionary(keyword: str) -> str:
    """
    查询数据中心能源管理系统的数据字典。
    可查询表名、字段名、字段描述、数据类型等信息。
    
    参数：
    - keyword: 查询关键词（如"meter_cfg"、"flow_num"、"字段"）
    """
    if not os.path.exists(DATA_DICT_PATH):
        return f"数据字典文件不存在：{DATA_DICT_PATH}"
    
    try:
        sheets = pd.read_excel(DATA_DICT_PATH, sheet_name=None)
    except Exception as e:
        return f"读取数据字典失败：{str(e)}"
    
    results = []
    for sheet_name, df in sheets.items():
        mask = df.astype(str).apply(
            lambda row: row.str.contains(keyword, case=False, na=False).any(),
            axis=1
        )
        matched = df[mask]
        if len(matched) > 0:
            results.append(f"【{sheet_name}】匹配 {len(matched)} 条：\n")
            results.append(matched.to_markdown(index=False))
            results.append("\n")
    
    if not results:
        return f"数据字典中未找到与「{keyword}」相关的内容"
    
    return "".join(results)