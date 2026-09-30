from langchain_core.tools import tool


@tool
def calculate_pue_savings(
    it_load_kw: float,
    current_pue: float,
    target_pue: float,
    electricity_price: float = 0.65,
    annual_hours: int = 8760,
    investment: float = 0,
) -> str:
    """
    计算PUE优化后的年节电量、年节约电费和投资回收期。
    
    参数：
    - it_load_kw: IT设备负载功率（kW）
    - current_pue: 当前PUE
    - target_pue: 改造后目标PUE
    - electricity_price: 电价（元/kWh），默认0.65
    - annual_hours: 年运行小时数，默认8760
    - investment: 改造投资额（元），默认0
    """
    if it_load_kw <= 0:
        return "IT负载功率必须大于0"
    if current_pue <= target_pue:
        return f"当前PUE({current_pue})不高于目标PUE({target_pue})，无需改造"
    
    # 年IT耗电
    annual_it_kwh = it_load_kw * annual_hours
    
    # 改造前后总耗电
    total_before = annual_it_kwh * current_pue
    total_after = annual_it_kwh * target_pue
    
    # 节电
    saved_kwh = total_before - total_after
    saved_cost = saved_kwh * electricity_price
    
    result = f"【PUE优化测算】\n"
    result += f"  IT负载：{it_load_kw} kW\n"
    result += f"  PUE：{current_pue} → {target_pue}\n"
    result += f"  电价：{electricity_price} 元/kWh\n\n"
    result += f"  年IT耗电：{annual_it_kwh:,.0f} kWh\n"
    result += f"  改造前总耗电：{total_before:,.0f} kWh\n"
    result += f"  改造后总耗电：{total_after:,.0f} kWh\n"
    result += f"  年节电量：{saved_kwh:,.0f} kWh（{saved_kwh/10000:.1f} 万度）\n"
    result += f"  年节约电费：{saved_cost:,.0f} 元（{saved_cost/10000:.1f} 万元）\n"
    
    if investment > 0:
        payback = investment / saved_cost
        result += f"  改造投资：{investment:,.0f} 元\n"
        result += f"  静态回收期：{payback:.1f} 年\n"
    
    return result