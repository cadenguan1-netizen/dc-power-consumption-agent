import pandas as pd
import numpy as np
from dataclasses import dataclass
from typing import Optional
from datetime import datetime
import json


@dataclass
class MeterAnalysisResult:
    """面向客户的分析结果"""
    # 基本信息
    time_start: str
    time_end: str
    days: int
    records: int
    period: str
    
    # 用电统计
    total_kwh: float
    daily_avg_kwh: float
    max_value: float
    min_value: float
    mean_value: float
    
    # 运行状态
    zero_ratio: float          # 零值比例
    active_ratio: float        # 非零值比例
    
    # 异常
    anomalies: list
    
    def to_text(self) -> str:
        """生成面向客户的文字描述"""
        text = "📊 数据分析结果\n\n"
        
        text += "【时间范围】\n"
        text += f"  {self.time_start} 至 {self.time_end}（共{self.days}天）\n"
        text += f"  数据粒度：{self.period}，共{self.records:,}条记录\n\n"
        
        text += "【用电统计】\n"
        text += f"  总用电量：{self.total_kwh:,.2f} kWh\n"
        text += f"  日均用电量：{self.daily_avg_kwh:,.2f} kWh\n"
        text += f"  最大单点值：{self.max_value:,.2f} kWh\n"
        text += f"  平均单点值：{self.mean_value:,.2f} kWh\n\n"
        
        text += "【运行状态】\n"
        text += f"  零值比例：{self.zero_ratio*100:.1f}%\n"
        text += f"  非零比例：{self.active_ratio*100:.1f}%\n"
        
        # 运行状态判断
        if self.zero_ratio > 0.95:
            text += f"\n  ⚠️ 判断：该分项在统计期内几乎不耗电（{self.zero_ratio*100:.1f}%时间为0）\n"
            text += "  可能原因：\n"
            text += "    1. 设备处于停机/待机状态\n"
            text += "    2. 该分项未投入使用\n"
            text += "    3. 采集器故障或配置错误\n"
            text += "  建议：确认该分项对应的设备是否应处于运行状态。\n"
        elif self.zero_ratio > 0.5:
            text += f"\n  ⚠️ 判断：该分项超过一半时间为0，运行不规律\n"
            text += "  可能原因：设备间歇性运行，或采集不稳定\n"
        else:
            text += f"\n  ✅ 判断：该分项运行正常，持续有能耗\n"
        
        # 异常信息
        if self.anomalies:
            text += f"\n【异常检测】\n"
            for a in self.anomalies:
                text += f"  - {a}\n"
        
        return text
    
    def to_dict(self) -> dict:
        """导出为字典（供LangChain Tool返回）"""
        return {
            'time_start': self.time_start,
            'time_end': self.time_end,
            'days': self.days,
            'records': self.records,
            'period': self.period,
            'total_kwh': round(self.total_kwh, 2),
            'daily_avg_kwh': round(self.daily_avg_kwh, 2),
            'max_value': round(self.max_value, 2),
            'min_value': round(self.min_value, 2),
            'mean_value': round(self.mean_value, 2),
            'zero_ratio': round(self.zero_ratio, 4),
            'active_ratio': round(self.active_ratio, 4),
            'anomalies': self.anomalies,
            'summary': self.to_text()
        }


def analyze_meter_data(
    df: pd.DataFrame,
    period: str = '1d'
) -> MeterAnalysisResult:
    """
    分析表计数据（ts, val 格式）
    
    参数：
    - df: 包含 ts 和 val 两列的 DataFrame
    - period: 时间粒度（15m/1h/1d）
    """
    # 1. 时间戳处理
    df = df.copy()
    df['ts'] = pd.to_datetime(df['ts'], unit='ms')
    df = df.sort_values('ts').reset_index(drop=True)
    
    time_start = df['ts'].min().strftime('%Y-%m-%d %H:%M')
    time_end = df['ts'].max().strftime('%Y-%m-%d %H:%M')
    
    # 计算天数
    days = (df['ts'].max() - df['ts'].min()).days + 1
    
    # 2. 基础统计
    total_kwh = df['val'].sum()
    daily_avg = total_kwh / days if days > 0 else 0
    max_val = df['val'].max()
    min_val = df['val'].min()
    mean_val = df['val'].mean()
    
    # 3. 运行状态
    zero_count = (df['val'] == 0).sum()
    zero_ratio = zero_count / len(df) if len(df) > 0 else 0
    active_ratio = 1 - zero_ratio
    
    # 4. 异常检测
    anomalies = []
    
    # 4.1 突增检测：超过均值 + 3σ
    if df['val'].std() > 0:
        threshold = mean_val + 3 * df['val'].std()
        spikes = df[df['val'] > threshold]
        if len(spikes) > 0:
            anomalies.append(
                f"检测到 {len(spikes)} 次用电突增（超过阈值 {threshold:.2f}），"
                f"最大突增值 {spikes['val'].max():.2f}，"
                f"发生于 {spikes.loc[spikes['val'].idxmax(), 'ts'].strftime('%Y-%m-%d %H:%M')}"
            )
    
    # 4.2 长时间连续为0检测
    if zero_ratio > 0.9:
        # 找出最长连续0区间
        is_zero = (df['val'] == 0).astype(int)
        zero_groups = is_zero.groupby((is_zero != is_zero.shift()).cumsum())
        max_zero_run = zero_groups.sum().max()
        if max_zero_run > 24:  # 超过1天的连续0
            anomalies.append(
                f"存在长时间连续零值（最长连续 {int(max_zero_run)} 个周期无用电）"
            )
    
    # 4.3 负值检测（数据异常）
    neg_count = (df['val'] < 0).sum()
    if neg_count > 0:
        anomalies.append(f"检测到 {neg_count} 个负值，数据可能有误")
    
    return MeterAnalysisResult(
        time_start=time_start,
        time_end=time_end,
        days=days,
        records=len(df),
        period=period,
        total_kwh=total_kwh,
        daily_avg_kwh=daily_avg,
        max_value=max_val,
        min_value=min_val,
        mean_value=mean_val,
        zero_ratio=zero_ratio,
        active_ratio=active_ratio,
        anomalies=anomalies
    )


def analyze_meter_csv(filepath: str, period: str = '1d') -> MeterAnalysisResult:
    """从CSV文件读取并分析"""
    df = pd.read_csv(filepath)
    if 'ts' not in df.columns or 'val' not in df.columns:
        raise ValueError(f"文件缺少 ts 或 val 列，实际列：{df.columns.tolist()}")
    return analyze_meter_data(df, period)


# ==================== 测试 ====================
if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        filepath = sys.argv[1]
    else:
        # 默认测试文件
        filepath = 'meter_cfg_sk_fdds_1_1d.csv'
    
    print(f"正在分析：{filepath}")
    print("=" * 60)
    
    try:
        result = analyze_meter_csv(filepath)
        print(result.to_text())
    except FileNotFoundError:
        print(f"❌ 文件不存在：{filepath}")
        print("用法：python meter_analyzer.py <csv文件路径>")