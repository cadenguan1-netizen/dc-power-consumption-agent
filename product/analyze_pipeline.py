import os
import sys
import pandas as pd

from data_model.table_parser import parse_table_name
from analysis.meter_analyzer import analyze_meter_csv


def analyze_file(filepath: str) -> str:
    """
    一站式分析：解析文件名 → 读取数据 → 分析 → 生成客户报告
    """
    filename = os.path.basename(filepath)
    
    # 第一步：解析文件名
    table_info = parse_table_name(filename)
    
    output = "=" * 60 + "\n"
    output += f"📁 文件：{filename}\n"
    output += "=" * 60 + "\n\n"
    
    if table_info:
        output += "【文件识别】\n"
        output += table_info.describe() + "\n"
    else:
        output += "⚠️ 无法识别文件名格式，将直接分析数据内容\n\n"
    
    # 第二步：判断周期
    period = table_info.period if table_info and table_info.period else '1d'
    
    # 第三步：数据分析
    try:
        result = analyze_meter_csv(filepath, period=period)
        output += result.to_text()
    except Exception as e:
        output += f"❌ 分析失败：{str(e)}\n"
    
    return output


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法：python analyze_pipeline.py <csv文件路径>")
        sys.exit(1)
    
    filepath = sys.argv[1]
    if not os.path.exists(filepath):
        print(f"❌ 文件不存在：{filepath}")
        sys.exit(1)
    
    print(analyze_file(filepath))