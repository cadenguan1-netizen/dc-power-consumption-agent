import os
from langchain_core.tools import tool
from data_model.table_parser import parse_table_name
from analysis.meter_analyzer import analyze_meter_csv
from data_model.data_scanner import scan_data_directory, summarize_index

@tool
def parse_and_analyze_meter_file(filepath: str) -> str:
    """
    分析数据中心能源表计数据文件（CSV格式）。
    输入文件路径，自动识别文件类型（分项数据/表计增量/原始读数），
    并返回统计结果：时间范围、总用电量、日均用电量、运行状态判断、异常检测。
    
    适用于文件名格式如：meter_cfg_sk_fdds_1_1d.csv
    
    参数：
    - filepath: CSV文件的完整路径或相对路径
    """
    if not os.path.exists(filepath):
        return f"文件不存在：{filepath}"
    
    filename = os.path.basename(filepath)
    table_info = parse_table_name(filename)
    
    output = f"📁 文件：{filename}\n\n"
    
    if table_info:
        output += "【文件识别】\n"
        output += table_info.describe() + "\n"
    else:
        output += "⚠️ 无法识别文件名格式，将直接分析数据内容\n\n"
    
    period = table_info.period if table_info and table_info.period else '1d'
    
    try:
        result = analyze_meter_csv(filepath, period=period)
        output += result.to_text()
    except Exception as e:
        output += f"❌ 分析失败：{str(e)}\n"
    
    return output


@tool
def describe_meter_file(filename: str) -> str:
    """
    仅解析文件名，说明这份数据是什么，不做数值分析。
    用于客户不确定文件含义时，先解释文件的结构和来源。
    
    参数：
    - filename: CSV文件名（如 meter_cfg_sk_fdds_1_1d.csv）
    """
    table_info = parse_table_name(filename)
    if table_info:
        return table_info.describe()
    else:
        return "无法识别该文件名格式。请确认文件名符合 meter_cfg_xxx、meter_incr_xxx 或 meter_original_xxx 的命名规则。"

@tool
def scan_all_data_files(data_dir: str) -> str:
    """
    扫描数据目录，列出所有数据文件的概览。
    当客户问"我有哪些数据""数据目录里有什么"时使用。
    
    参数：
    - data_dir: 数据目录路径
    """
    index = scan_data_directory(data_dir)
    return summarize_index(index)

@tool
def find_meter_files(
    park: str = None,
    tenant: str = None,
    table_type: str = None,
    period: str = None,
) -> str:
    """
    根据园区、租户、表类型、周期查找匹配的数据文件。
    用户提到某个园区或租户时，先用这个工具找到相关文件。
    
    参数：
    - park: 园区编码（如 fdds、sjzskfu）
    - tenant: 租户编码（如 sk）
    - table_type: 表类型（meter_cfg / meter_incr / meter_original）
    - period: 时间粒度（15m / 1h / 1d）
    """
    from data_model.data_scanner import scan_data_directory
    
    data_dir = "/Users/mac/Documents/Caden/2026年暑假实习项目/能源数据/能源实时数据-Tdengine数据库"
    index = scan_data_directory(data_dir)
    
    if 'error' in index:
        return index['error']
    
    files = index['files']
    if park:
        files = [f for f in files if f['pcode'] == park]
    if tenant:
        files = [f for f in files if f['tcode'] == tenant]
    if table_type:
        files = [f for f in files if f['table_type'] == table_type]
    if period:
        files = [f for f in files if f['period'] == period]
    
    if not files:
        return "未找到匹配的数据文件"
    
    result = f"找到 {len(files)} 个匹配文件：\n"
    for f in files[:10]:
        result += f"  - {f['filename']}（路径：{f['filepath']}）\n"
    if len(files) > 10:
        result += f"  ...还有 {len(files)-10} 个\n"
    return result