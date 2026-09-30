from langchain_openai import ChatOpenAI
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate

from tools.meter_tools import (
    describe_meter_file,
    parse_and_analyze_meter_file,
    scan_all_data_files,
    find_meter_files,
)
from tools.generic_data_tools import (
    explore_data_file,
    analyze_data_generic,
    group_by_analysis,
    detect_anomalies,
)
from tools.data_discovery import (
    list_all_data_files,
    peek_data_file,
    search_files_by_keyword,
)
from tools.calc_tools import calculate_pue_savings
from tools.rag_tools import search_knowledge_base
from tools.data_dict_tools import query_data_dictionary
from tools.viz_tools import visualize_meter_trend
from tools.generic_viz_tools import auto_visualize, visualize_group_comparison



# ==================== 数据目录 ====================
DATA_DIR = "/Users/mac/Documents/Caden/2026年暑假实习项目/能源数据/能源实时数据-Tdengine数据库"


# ==================== System Prompt ====================
SYSTEM_PROMPT = f"""你是一个数据中心能耗分析助手，面向不熟悉内部命名规则的客户。

【你当前可访问的数据目录】
{DATA_DIR}

【你的能力】
1. 探索数据目录（list_all_data_files、peek_data_file、search_files_by_keyword）
2. 分析任意数据文件（explore_data_file、analyze_data_generic、group_by_analysis、detect_anomalies）
3. 专用分析（parse_and_analyze_meter_file、find_meter_files）
4. 计算PUE、节电量、回收期（calculate_pue_savings）
5. 查询标准（search_knowledge_base）
6. 查询数据字典（query_data_dictionary）
7. 生成图表（auto_visualize、visualize_group_comparison、visualize_meter_trend）

【工作方式】
当用户提出开放性问题时，按以下步骤：
1. 先理解意图：统计/对比/趋势/异常/排名/计算/查标准
2. 定位数据：
   - 用户提到园区/租户 → 用 find_meter_files 或 search_files_by_keyword
   - 用户没指定 → 用 list_all_data_files 了解有什么
3. 确认结构：用 peek_data_file 或 explore_data_file 看列名和数据类型
4. 选择工具：
   - 整体统计 → analyze_data_generic
   - 分组对比 → group_by_analysis
   - 异常检测 → detect_anomalies
   - 单文件深度分析 → parse_and_analyze_meter_file
   - 要图 → auto_visualize 或 visualize_group_comparison
5. 用自然语言总结，不要直接输出工具原始格式

【重要原则】
- 不预设数据格式，先看列名和数据类型，再决定怎么分析
- 用户不会报精确文件名，从上下文推断
- 计算时缺参数用默认值（电价0.65，年运行8760小时）
- 分析园区数据时，如果文件超过20个，先按周期（优先1d）和类型（优先meter_cfg）筛选，
  再挑最具代表性的几个文件分析，不要试图分析所有文件
- 回答要专业但易懂，避免堆砌术语
- 如果问题含糊，先问清楚关键信息（哪个园区、哪个时间段、什么指标）
"""

# ==================== 模型配置 ====================
llm = ChatOpenAI(
    model="deepseek-chat",
    base_url="https://api.deepseek.com/v1",
    api_key="sk-85639dc9bd654c738b128bca3a86f943",
    temperature=0.3,
)


# ==================== 工具注册 ====================
tools = [
    # 数据发现
    list_all_data_files,
    peek_data_file,
    search_files_by_keyword,
    # 通用分析
    explore_data_file,
    analyze_data_generic,
    group_by_analysis,
    detect_anomalies,
    # 专用分析
    describe_meter_file,
    parse_and_analyze_meter_file,
    scan_all_data_files,
    find_meter_files,
    # 计算
    calculate_pue_savings,
    # 知识
    search_knowledge_base,
    # 数据字典
    query_data_dictionary,
    # 可视化
    visualize_meter_trend,
    auto_visualize,
    visualize_group_comparison,
]


# ==================== 创建 Agent ====================
prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}"),
])

agent = create_tool_calling_agent(llm, tools, prompt)
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
    handle_parsing_errors=True,
    max_iterations=15,
)


# ==================== 对话循环 ====================
def main():
    print("=" * 60)
    print("数据中心能耗分析助手")
    print("输入 'quit' 退出，'clear' 清空上下文")
    print("=" * 60)
    
    chat_history = []
    
    while True:
        user_input = input("\n你：").strip()
        if user_input.lower() in ['quit', 'exit', 'q']:
            break
        if user_input.lower() == 'clear':
            chat_history = []
            print("上下文已清空")
            continue
        if not user_input:
            continue
        
        try:
            context = ""
            if chat_history:
                context = "【之前的对话】\n"
                for h in chat_history[-4:]:
                    context += f"用户：{h['user']}\n助手：{h['assistant']}\n"
                context += "\n【当前问题】\n"
            
            full_input = context + user_input
            result = agent_executor.invoke({"input": full_input})
            reply = result['output']
            
            print(f"\n助手：{reply}")
            
            chat_history.append({
                'user': user_input,
                'assistant': reply
            })
            
        except Exception as e:
            print(f"\n出错了：{str(e)}")


if __name__ == '__main__':
    main()