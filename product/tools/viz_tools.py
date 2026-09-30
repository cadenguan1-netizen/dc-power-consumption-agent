import os
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from langchain_core.tools import tool

plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial']
plt.rcParams['axes.unicode_minus'] = False


@tool
def visualize_meter_trend(csv_path: str, save_path: str = "meter_trend.png") -> str:
    """
    对表计数据（ts, val 格式）生成用电趋势图。
    
    参数：
    - csv_path: CSV文件路径
    - save_path: 图片保存路径，默认 meter_trend.png
    """
    if not os.path.exists(csv_path):
        return f"文件不存在：{csv_path}"
    
    try:
        df = pd.read_csv(csv_path)
        if 'ts' not in df.columns or 'val' not in df.columns:
            return f"文件缺少 ts 或 val 列，实际列：{df.columns.tolist()}"
        
        df['ts'] = pd.to_datetime(df['ts'], unit='ms')
        df = df.sort_values('ts')
        
        fig, ax = plt.subplots(figsize=(12, 5))
        ax.plot(df['ts'], df['val'], linewidth=1, color='#1f77b4')
        ax.set_xlabel('Time')
        ax.set_ylabel('Value (kWh)')
        ax.set_title(f'Meter Trend: {os.path.basename(csv_path)}')
        ax.grid(True, alpha=0.3)
        plt.xticks(rotation=30)
        plt.tight_layout()
        plt.savefig(save_path, dpi=120, bbox_inches='tight')
        plt.close()
        
        total = df['val'].sum()
        mean = df['val'].mean()
        max_v = df['val'].max()
        
        return (
            f"趋势图已生成：{save_path}\n\n"
            f"统计摘要：\n"
            f"  记录数：{len(df):,}\n"
            f"  总用电量：{total:,.2f} kWh\n"
            f"  平均值：{mean:,.2f}\n"
            f"  最大值：{max_v:,.2f}"
        )
    except Exception as e:
        return f"生成图表失败：{str(e)}"