import os
import glob
import pandas as pd
import numpy as np
from langchain_core.tools import tool


@tool
def explore_data_file(filepath: str) -> str:
    """
    探查任意数据文件的结构和内容。
    支持 CSV、Excel、JSON。
    返回：列名、数据类型、行数、前5行样本、缺失值情况。
    
    参数：
    - filepath: 数据文件路径
    """
    if not os.path.exists(filepath):
        return f"文件不存在：{filepath}"
    
    try:
        ext = os.path.splitext(filepath)[1].lower()
        if ext == '.csv':
            df = pd.read_csv(filepath, nrows=10000)
        elif ext in ['.xlsx', '.xls']:
            df = pd.read_excel(filepath)
        elif ext == '.json':
            df = pd.read_json(filepath)
        else:
            return f"暂不支持的文件格式：{ext}"
    except Exception as e:
        return f"读取失败：{str(e)}"
    
    output = f"📊 数据探查：{os.path.basename(filepath)}\n\n"
    output += f"行数：{len(df):,}\n"
    output += f"列数：{len(df.columns)}\n\n"
    output += "【列信息】\n"
    for col in df.columns:
        dtype = df[col].dtype
        nulls = df[col].isnull().sum()
        sample = df[col].dropna().head(1).tolist()
        output += f"  - {col}（{dtype}，缺失{nulls}个）示例：{sample}\n"
    
    output += f"\n【前5行样本】\n{df.head().to_markdown(index=False)}\n"
    
    return output


@tool
def analyze_data_generic(filepath: str, question: str) -> str:
    """
    对任意数据文件做通用统计分析。
    自动识别数值列、时间列、分类列，根据问题给出统计结果。
    
    参数：
    - filepath: 数据文件路径
    - question: 用户的自然语言问题（如"总共有多少""最大值是多少""按类别汇总"）
    """
    if not os.path.exists(filepath):
        return f"文件不存在：{filepath}"
    
    try:
        ext = os.path.splitext(filepath)[1].lower()
        if ext == '.csv':
            df = pd.read_csv(filepath)
        elif ext in ['.xlsx', '.xls']:
            df = pd.read_excel(filepath)
        else:
            return f"暂不支持：{ext}"
    except Exception as e:
        return f"读取失败：{str(e)}"
    
    # 自动识别列类型
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    datetime_cols = df.select_dtypes(include=['datetime']).columns.tolist()
    
    # 尝试把看起来像时间的列转成 datetime
    for col in df.columns:
        if col not in datetime_cols:
            try:
                df[col] = pd.to_datetime(df[col])
                datetime_cols.append(col)
            except:
                pass
    
    output = f"📈 通用分析：{os.path.basename(filepath)}\n\n"
    output += f"共 {len(df):,} 行，{len(df.columns)} 列\n"
    output += f"数值列：{numeric_cols}\n"
    output += f"时间列：{datetime_cols}\n\n"
    
    # 通用统计
    if numeric_cols:
        output += "【数值列统计】\n"
        output += df[numeric_cols].describe().to_markdown()
        output += "\n\n"
    
    # 时间范围
    if datetime_cols:
        for col in datetime_cols:
            output += f"【{col} 时间范围】\n"
            output += f"  {df[col].min()} 至 {df[col].max()}\n\n"
    
    # 分类列统计
    for col in df.columns:
        if col not in numeric_cols and col not in datetime_cols:
            if df[col].nunique() < 20:
                output += f"【{col} 分布】\n"
                output += df[col].value_counts().head(10).to_markdown()
                output += "\n\n"
    
    return output


@tool
def group_by_analysis(filepath: str, group_col: str, value_col: str, top_n: int = 10) -> str:
    """
    按指定列分组，对数值列做聚合。
    用于回答"哪个类别最多""按XX分组统计"这类问题。
    
    参数：
    - filepath: 数据文件路径
    - group_col: 分组列（如"园区""类别"）
    - value_col: 要聚合的数值列
    - top_n: 返回前N个，默认10
    """
    try:
        df = pd.read_csv(filepath)
    except Exception as e:
        return f"读取失败：{str(e)}"
    
    if group_col not in df.columns or value_col not in df.columns:
        return f"列不存在。可用列：{df.columns.tolist()}"
    
    try:
        grouped = df.groupby(group_col)[value_col].agg(['sum', 'mean', 'count'])
        grouped = grouped.sort_values('sum', ascending=False).head(top_n)
        return f"按 {group_col} 分组，对 {value_col} 聚合：\n\n" + grouped.to_markdown()
    except Exception as e:
        return f"聚合失败：{str(e)}"


@tool
def detect_anomalies(filepath: str, value_col: str) -> str:
    """
    对指定数值列做异常检测（3σ 和 IQR 双方法）。
    
    参数：
    - filepath: 数据文件路径
    - value_col: 要检测的数值列
    """
    try:
        df = pd.read_csv(filepath)
    except Exception as e:
        return f"读取失败：{str(e)}"
    
    if value_col not in df.columns:
        return f"列不存在。可用列：{df.columns.tolist()}"
    
    values = df[value_col].dropna()
    mean = values.mean()
    std = values.std()
    
    # 3σ
    sigma_anomalies = values[np.abs(values - mean) > 3 * std]
    
    # IQR
    q1, q3 = values.quantile([0.25, 0.75])
    iqr = q3 - q1
    iqr_anomalies = values[(values < q1 - 1.5*iqr) | (values > q3 + 1.5*iqr)]
    
    output = f"⚠️ 异常检测：{value_col}\n\n"
    output += f"均值：{mean:.2f}，标准差：{std:.2f}\n"
    output += f"3σ 异常：{len(sigma_anomalies)} 个\n"
    output += f"IQR 异常：{len(iqr_anomalies)} 个\n\n"
    
    if len(sigma_anomalies) > 0:
        output += f"3σ 异常值样本：{sigma_anomalies.head(5).tolist()}\n"
    
    return output