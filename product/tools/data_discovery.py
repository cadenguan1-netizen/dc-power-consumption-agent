import os
import glob
import pandas as pd
from langchain_core.tools import tool


@tool
def list_all_data_files(data_dir: str, max_files: int = 50) -> str:
    """
    列出数据目录下所有数据文件的概览。
    用于回答"我有哪些数据""数据目录里有什么"这类问题。
    
    参数：
    - data_dir: 数据目录路径
    - max_files: 最多返回多少个文件，默认50
    """
    if not os.path.exists(data_dir):
        return f"目录不存在：{data_dir}"
    
    # 扫描所有支持的文件
    extensions = ['*.csv', '*.xlsx', '*.xls', '*.json']
    all_files = []
    for ext in extensions:
        all_files.extend(glob.glob(os.path.join(data_dir, "**", ext), recursive=True))
    
    if not all_files:
        return f"目录 {data_dir} 下没有找到数据文件"
    
    # 按扩展名分组统计
    by_ext = {}
    for f in all_files:
        ext = os.path.splitext(f)[1].lower()
        by_ext.setdefault(ext, []).append(f)
    
    output = f"📂 数据目录概览：{data_dir}\n\n"
    output += f"共发现 {len(all_files)} 个数据文件\n\n"
    
    for ext, files in by_ext.items():
        output += f"【{ext}】{len(files)} 个文件\n"
        for f in files[:max_files // len(by_ext)]:
            output += f"  - {os.path.relpath(f, data_dir)}\n"
        if len(files) > max_files // len(by_ext):
            output += f"  ...还有 {len(files) - max_files // len(by_ext)} 个\n"
        output += "\n"
    
    return output


@tool
def peek_data_file(filepath: str) -> str:
    """
    快速查看一个数据文件的前几行，了解它长什么样。
    用于在分析前先确认数据结构。
    
    参数：
    - filepath: 数据文件路径
    """
    if not os.path.exists(filepath):
        return f"文件不存在：{filepath}"
    
    try:
        ext = os.path.splitext(filepath)[1].lower()
        if ext == '.csv':
            df = pd.read_csv(filepath, nrows=5)
        elif ext in ['.xlsx', '.xls']:
            df = pd.read_excel(filepath, nrows=5)
        elif ext == '.json':
            df = pd.read_json(filepath)
            df = df.head(5)
        else:
            return f"暂不支持：{ext}"
    except Exception as e:
        return f"读取失败：{str(e)}"
    
    output = f"📄 {os.path.basename(filepath)}\n\n"
    output += f"列：{df.columns.tolist()}\n\n"
    output += f"前5行：\n{df.to_markdown(index=False)}\n"
    return output


@tool
def search_files_by_keyword(keyword: str, data_dir: str) -> str:
    """
    在数据目录中按关键词搜索文件（匹配文件名和内容）。
    用于回答"哪个文件包含XX数据"这类问题。
    
    参数：
    - keyword: 搜索关键词
    - data_dir: 数据目录路径
    """
    if not os.path.exists(data_dir):
        return f"目录不存在：{data_dir}"
    
    # 先按文件名匹配
    matched_by_name = []
    for ext in ['*.csv', '*.xlsx', '*.xls']:
        for f in glob.glob(os.path.join(data_dir, "**", ext), recursive=True):
            if keyword.lower() in os.path.basename(f).lower():
                matched_by_name.append(f)
    
    output = f"🔍 搜索「{keyword}」\n\n"
    
    if matched_by_name:
        output += f"【文件名匹配】{len(matched_by_name)} 个：\n"
        for f in matched_by_name[:20]:
            output += f"  - {os.path.relpath(f, data_dir)}\n"
    else:
        output += "文件名中未找到匹配\n"
    
    return output