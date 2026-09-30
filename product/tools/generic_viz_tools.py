import os
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from langchain_core.tools import tool

plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial']
plt.rcParams['axes.unicode_minus'] = False


@tool
def auto_visualize(filepath: str, save_path: str = None) -> str:
    """
    自动为任意数据文件生成合适的图表。
    根据数据特征自动选择图表类型：
    - 有时间列 + 数值列 → 折线图（趋势）
    - 有分类列 + 数值列 → 柱状图（对比）
    - 只有数值列 → 直方图（分布）
    - 两个数值列 → 散点图（相关性）
    
    参数：
    - filepath: 数据文件路径
    - save_path: 保存路径，默认 auto_chart.png
    """
    if not os.path.exists(filepath):
        return f"文件不存在：{filepath}"
    
    if save_path is None:
        save_path = f"{os.path.splitext(os.path.basename(filepath))[0]}_chart.png"
    
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
    
    # 识别列类型
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    datetime_cols = []
    for col in df.columns:
        if col not in numeric_cols:
            try:
                df[col] = pd.to_datetime(df[col])
                datetime_cols.append(col)
            except:
                pass
    
    fig, ax = plt.subplots(figsize=(12, 5))
    
    # 自动选图
    if datetime_cols and numeric_cols:
        # 时间序列 → 折线图
        time_col = datetime_cols[0]
        df = df.sort_values(time_col)
        for col in numeric_cols[:3]:  # 最多3条线
            ax.plot(df[time_col], df[col], label=col, linewidth=1)
        ax.set_xlabel(time_col)
        ax.set_ylabel('Value')
        ax.set_title(f'Trend: {os.path.basename(filepath)}')
        ax.legend()
        chart_type = "折线图（趋势）"
    
    elif numeric_cols and len(df) < 50:
        # 少量数据 → 柱状图
        ax.bar(range(len(df)), df[numeric_cols[0]])
        ax.set_xlabel('Index')
        ax.set_ylabel(numeric_cols[0])
        ax.set_title(f'Bar: {os.path.basename(filepath)}')
        chart_type = "柱状图（对比）"
    
    elif numeric_cols:
        # 纯数值 → 直方图
        ax.hist(df[numeric_cols[0]].dropna(), bins=30, edgecolor='black', alpha=0.7)
        ax.set_xlabel(numeric_cols[0])
        ax.set_ylabel('Frequency')
        ax.set_title(f'Distribution: {numeric_cols[0]}')
        chart_type = "直方图（分布）"
    
    else:
        return "数据中没有可绘制的数值列"
    
    ax.grid(True, alpha=0.3)
    plt.xticks(rotation=30)
    plt.tight_layout()
    plt.savefig(save_path, dpi=120, bbox_inches='tight')
    plt.close()
    
    return f"✅ 已生成{chart_type}：{save_path}\n\n数据规模：{len(df):,} 行，{len(df.columns)} 列"


@tool
def visualize_group_comparison(filepath: str, group_col: str, value_col: str, save_path: str = None) -> str:
    """
    按分类列分组，对数值列做对比图（柱状图或饼图）。
    
    参数：
    - filepath: 数据文件路径
    - group_col: 分组列
    - value_col: 数值列
    - save_path: 保存路径
    """
    if save_path is None:
        save_path = f"{group_col}_vs_{value_col}.png"
    
    try:
        df = pd.read_csv(filepath)
    except Exception as e:
        return f"读取失败：{str(e)}"
    
    if group_col not in df.columns or value_col not in df.columns:
        return f"列不存在。可用列：{df.columns.tolist()}"
    
    grouped = df.groupby(group_col)[value_col].sum().sort_values(ascending=False).head(10)
    
    fig, ax = plt.subplots(figsize=(10, 6))
    grouped.plot(kind='bar', ax=ax, color='#3498db')
    ax.set_xlabel(group_col)
    ax.set_ylabel(f'Sum of {value_col}')
    ax.set_title(f'{group_col} vs {value_col}')
    ax.grid(True, alpha=0.3, axis='y')
    plt.xticks(rotation=30)
    plt.tight_layout()
    plt.savefig(save_path, dpi=120, bbox_inches='tight')
    plt.close()
    
    return f"对比图已生成：{save_path}\n\nTop 10：\n{grouped.to_markdown()}"