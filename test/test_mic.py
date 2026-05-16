# test_mic.py
import streamlit as st
from streamlit_mic_recorder import mic_recorder

st.title("🎤 麦克风深度调试")

state = mic_recorder(
    start_prompt="Start Recording",
    stop_prompt="Stop Recording",
    key="debug_mic_001"
)

if state:
    st.write("### 原始返回数据 (Raw State):")
    st.json(state)  # <--- 关键：看这里有没有 'text' 字段

    if "text" in state and state["text"]:
        st.success(f"✅ 识别成功: {state['text']}")
    else:
        st.error("❌ 识别失败：有音频数据但没有文字。")
        st.warning("可能原因：1. 网络不通（无法连接谷歌/微软识别服务）; 2. 浏览器语言设置不是中文; 3. 说话声音太小。")

    if "bytes" in state:
        st.info(f"🎵 音频数据长度：{len(state['bytes'])} bytes (说明录音本身是成功的)")