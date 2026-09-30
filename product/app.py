import streamlit as st
import os
from chat import agent_executor

st.set_page_config(page_title="数据中心能耗助手", layout="wide")
st.title("💡 数据中心能耗智能助手")

# 初始化会话状态
if "messages" not in st.session_state:
    st.session_state.messages = []
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# 侧边栏：清空按钮
with st.sidebar:
    st.header("操作")
    if st.button("清空对话"):
        st.session_state.messages = []
        st.session_state.chat_history = []
        st.rerun()
    st.markdown("---")
    st.markdown("**示例问题**")
    st.markdown("- 我有哪些数据？")
    st.markdown("- fdds 园区用电情况怎么样？")
    st.markdown("- 哪个分项最耗电？")
    st.markdown("- PUE 1.6 符合国家标准吗？")
    st.markdown("- IT功率500kW，PUE从1.6降到1.3，一年省多少钱？")

# 显示历史消息
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("image") and os.path.exists(msg["image"]):
            st.image(msg["image"])

# 用户输入
if prompt := st.chat_input("请输入您的问题..."):
    # 显示用户消息
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # 调用 Agent
    with st.chat_message("assistant"):
        with st.spinner("思考中..."):
            try:
                # 拼接上下文
                context = ""
                if st.session_state.chat_history:
                    context = "【之前的对话】\n"
                    for h in st.session_state.chat_history[-4:]:
                        context += f"用户：{h['user']}\n助手：{h['assistant']}\n"
                    context += "\n【当前问题】\n"
                
                full_input = context + prompt
                result = agent_executor.invoke({"input": full_input})
                reply = result['output']
            except Exception as e:
                reply = f"出错了：{str(e)}"
        
        st.markdown(reply)
        
        # 检查是否有生成的图片
        image_path = None
        for f in os.listdir("."):
            if f.endswith("_chart.png") or f.endswith("_vs_.png") or f == "meter_trend.png":
                if os.path.getmtime(f) > (os.path.getmtime(__file__) - 60):  # 最近1分钟生成的
                    image_path = f
                    break
        
        if image_path and os.path.exists(image_path):
            st.image(image_path)
        
        # 记录
        st.session_state.messages.append({
            "role": "assistant",
            "content": reply,
            "image": image_path
        })
        st.session_state.chat_history.append({
            "user": prompt,
            "assistant": reply
        })