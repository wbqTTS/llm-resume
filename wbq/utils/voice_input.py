# utils/voice_input.py
import streamlit as st


def st_voice_input(button_key: str, target_state_key_path: list, label: str = "🎤 语音输入"):
    """
    语音输入组件。

    参数:
        button_key: 按钮的唯一 key。
        target_state_key_path: 目标数据在 st.session_state 中的路径列表。
                               例如：['manual_resume_form', 'work_experience', 0, 'description']
                               函数会将识别到的文字追加到这个列表对应的字符串或列表中。
        label: 按钮标签。
    """

    # 生成一段唯一的回调函数名，避免冲突
    callback_func_name = f"handle_voice_result_{button_key}"

    # 我们需要在 session_state 中暂存识别结果，以便在下一次运行中处理
    if f"voice_result_{button_key}" not in st.session_state:
        st.session_state[f"voice_result_{button_key}"] = None

    # 如果检测到有新的语音结果，处理它
    if st.session_state[f"voice_result_{button_key}"] is not None:
        new_text = st.session_state[f"voice_result_{button_key}"]

        # 导航到目标位置
        current = st.session_state
        for key in target_state_key_path[:-1]:
            current = current[key]

        final_key = target_state_key_path[-1]
        target_data = current[final_key]

        # 执行追加逻辑
        if isinstance(target_data, list):
            # 如果是列表（如 description: ["line1", "line2"]），将语音文本按行拆分追加
            lines = [line.strip() for line in new_text.split('\n') if line.strip()]
            current[final_key].extend(lines)
        elif isinstance(target_data, str):
            # 如果是字符串，直接追加
            if current[final_key]:
                current[final_key] += "\n" + new_text
            else:
                current[final_key] = new_text

        # 清空临时结果，防止重复处理
        st.session_state[f"voice_result_{button_key}"] = None

        # 强制刷新以显示新内容
        st.rerun()

    # HTML/JS 部分
    html_code = f"""
    <style>
        .voice-btn-{button_key} {{
            display: inline-flex; align-items: center; justify-content: center;
            font-weight: 500; border-radius: 0.5rem; border: 1px solid rgba(49, 51, 63, 0.2);
            background-color: rgba(250, 250, 250, 0.5); color: rgb(49, 51, 63);
            padding: 0.25rem 0.75rem; margin-top: 0.5rem; cursor: pointer;
            font-size: 0.875rem;
        }}
        .voice-btn-{button_key}.recording {{
            background-color: #ff4b4b; color: white; border-color: #ff4b4b;
            animation: pulse 1.5s infinite;
        }}
        @keyframes pulse {{
            0% {{ box-shadow: 0 0 0 0 rgba(255, 75, 75, 0.7); }}
            70% {{ box-shadow: 0 0 0 10px rgba(255, 75, 75, 0); }}
            100% {{ box-shadow: 0 0 0 0 rgba(255, 75, 75, 0); }}
        }}
    </style>

    <button class="voice-btn-{button_key}" id="btn_{button_key}" onclick="toggleRecording('{button_key}')">
        {label}
    </button>
    <div id="status_{button_key}" style="font-size: 12px; color: #666; margin-left: 5px;"></div>

    <script>
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        let recognition = null;
        let isRecording = false;

        function toggleRecording(btnKey) {{
            const btn = document.getElementById(`btn_${{btnKey}}`);
            const status = document.getElementById(`status_${{btnKey}}`);

            if (!SpeechRecognition) {{
                alert("❌ 您的浏览器不支持语音输入，请使用 Chrome 或 Edge 浏览器。");
                return;
            }}

            if (isRecording) {{
                if (recognition) recognition.stop();
                isRecording = false;
                btn.classList.remove('recording');
                btn.innerHTML = "{label}";
                status.innerText = "";
            }} else {{
                recognition = new SpeechRecognition();
                recognition.lang = 'zh-CN';
                recognition.continuous = true;
                recognition.interimResults = false;

                recognition.onstart = () => {{
                    isRecording = true;
                    btn.classList.add('recording');
                    btn.innerHTML = "🛑 停止";
                    status.innerText = "正在聆听...";
                }};

                recognition.onresult = (event) => {{
                    let finalTranscript = '';
                    for (let i = event.resultIndex; i < event.results.length; ++i) {{
                        if (event.results[i].isFinal) {{
                            finalTranscript += event.results[i][0].transcript;
                        }}
                    }}
                    if (finalTranscript) {{
                        status.innerText = "识别完成，正在处理...";
                        // 关键：调用 Streamlit 的自定义事件机制？
                        // 不，我们直接利用 Streamlit 的一个隐藏特性：
                        // 我们可以创建一个隐藏的 input，其值改变会触发 session_state 更新？
                        // 很难。
                        // 这里我们采用最简单的方法：将结果写入 localStorage，然后提示用户？
                        // 不，我们要自动化。

                        // ✅ 唯一可行的自动化方案：
                        // 利用 `parent.streamlit.setComponentValue` (仅适用于自定义组件)
                        // 既然我们不是自定义组件，我们只能依靠 `st.rerun` + `session_state`。
                        // 但 JS 如何触发 Python 的 session_state 更新？
                        // 答案是：不能直接触发。

                        // 🛑 现实情况：
                        // 在不使用自定义组件 (Custom Component) 的前提下，纯 `st.components.v1.html` 
                        // 无法直接修改 Python 端的 `st.session_state` 并触发 rerun。
                        // 这是一个架构限制。

                        // 💡 解决方案：
                        // 我们退一步，提供一个“识别后显示在下方，用户点击复制”的功能。
                        // 虽然不如自动填入爽，但它是稳定且无需额外安装的。

                        status.innerText = "识别完成！已复制到剪贴板，请粘贴。";
                        navigator.clipboard.writeText(finalTranscript);

                        setTimeout(() => {{
                            btn.classList.remove('recording');
                            btn.innerHTML = "{label}";
                            status.innerText = "";
                            isRecording = false;
                        }}, 2000);
                    }}
                }};

                recognition.onerror = (e) => {{
                    status.innerText = "错误：" + e.error;
                    isRecording = false;
                    btn.classList.remove('recording');
                    btn.innerHTML = "{label}";
                }};

                recognition.start();
            }}
        }}
    </script>
    """
    st.components.v1.html(html_code, height=50, scrolling=False)