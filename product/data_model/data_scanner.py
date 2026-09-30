import os
import glob
from collections import defaultdict
from data_model.table_parser import parse_table_name


def scan_data_directory(data_dir: str) -> dict:
    """
    扫描目录下所有CSV文件，按维度建立索引。
    """
    if not os.path.exists(data_dir):
        return {'error': f'目录不存在：{data_dir}'}
    
    csv_files = glob.glob(os.path.join(data_dir, "**", "*.csv"), recursive=True)
    
    index = {
        'total_files': 0,
        'by_table_type': defaultdict(list),
        'by_tenant': defaultdict(list),
        'by_park': defaultdict(list),
        'by_period': defaultdict(list),
        'files': [],
        'unrecognized': []
    }
    
    for filepath in csv_files:
        filename = os.path.basename(filepath)
        info = parse_table_name(filename)
        
        if info is None:
            index['unrecognized'].append(filename)
            continue
        
        index['total_files'] += 1
        index['by_table_type'][info.table_type].append(filename)
        index['by_tenant'][info.tcode].append(filename)
        index['by_park'][info.pcode].append(filename)
        if info.period:
            index['by_period'][info.period].append(filename)
        
        index['files'].append({
            'filename': filename,
            'filepath': filepath,
            'table_type': info.table_type,
            'tcode': info.tcode,
            'pcode': info.pcode,
            'identifier': info.identifier,
            'period': info.period,
        })
    
    index['by_table_type'] = dict(index['by_table_type'])
    index['by_tenant'] = dict(index['by_tenant'])
    index['by_park'] = dict(index['by_park'])
    index['by_period'] = dict(index['by_period'])
    
    return index


def summarize_index(index: dict) -> str:
    """生成面向客户的数据概览"""
    if 'error' in index:
        return index['error']
    
    text = f"📂 数据目录概览\n\n"
    text += f"共发现 {index['total_files']} 个数据文件\n\n"
    
    if index['by_table_type']:
        type_names = {
            'meter_cfg': '分项用电数据',
            'meter_incr': '表计增量数据',
            'meter_original': '表计原始读数',
        }
        text += "【按数据类型】\n"
        for t, files in index['by_table_type'].items():
            text += f"  - {type_names.get(t, t)}：{len(files)} 个文件\n"
    
    if index['by_tenant']:
        text += "\n【按租户】\n"
        for t, files in index['by_tenant'].items():
            text += f"  - {t}：{len(files)} 个文件\n"
    
    if index['by_park']:
        text += "\n【按园区】\n"
        for p, files in index['by_park'].items():
            text += f"  - {p}：{len(files)} 个文件\n"
    
    if index['by_period']:
        text += "\n【按时间粒度】\n"
        for p, files in index['by_period'].items():
            text += f"  - {p}：{len(files)} 个文件\n"
    
    if index['unrecognized']:
        text += f"\n⚠️ 有 {len(index['unrecognized'])} 个文件无法识别命名格式\n"
    
    return text