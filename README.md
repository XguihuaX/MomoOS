# 🌟 AI 多模态语音助手系统 (GPT-SoVITS + DeepSeek + ToolAgent)

该项目是一个集成了语音识别 (ASR)，大语言模型生成 (LLM)，语音合成 (TTS)，多人物角色管理和记忆/任务管理二维 AI 助手系统，支持用户分离、记忆组织、任务提醒、定时 TTS 操作等功能。

---

## 🚀 项目启动

```bash
# 安装依赖
pip install -r requirements.txt

# 启动 Flask 后端 (5001 端口)
./start.sh
```

---
🎙 用户输入（文本或语音）
│
├──> 🌐 /api/dispatch（app.py）
│     ├─ 如果是语音 → 🔊 /api/asr（asr_server.py） → 返回文本
│     └─ 构建标准消息 → 📦 build_message（mcp_message.py）
│
├──> 🧠 PlannerAgent.handle（PlannerAgent.py）
│     ├─ 调用 DeepSeek → core/llm/deepseek_api.py
│     └─ 解析指令为任务调用链
│
├──> 多个 Agent 被调用（根据 planner 输出）
│     ├─ 🗂 MemoryAgent.handle → 操作数据库（model.py + services.py）
│     ├─ 🛠 ToolAgent.handle → 操作 toolbox.py（播放音乐、播报、角色切换）
│     ├─ 🌐 SearchAgent.handle → 执行联网查询（如天气）
│     └─ 💬 ChatAgent.handle → 调用 qwen_api.py 生成文本
│
├──> 合成语音：
│     └─ 🗣 generate_audio.py（调用 GPT-SoVITS 本地推理服务）
│
└──> 📤 返回结果：
      JSON 格式 = {"character": "...", "text": "...", "audio": Base64音频}


-----------
📁 代码位置快速索引（可写在 README 最后）
功能	文件路径
Flask 启动	app.py
MCP 构建格式	core/message/mcp_message.py
ASR 模块	core/audio/asr_server.py
TTS 合成	core/audio/generate_audio.py
Prompt 构建	core/llm/prompt_builder.py
Prompt 实现 core/llm/prompt_state.py
LLM API（DeepSeek）	core/llm/deepseek_api.py
LLM API（通义）	core/llm/qwen_api.py
短期记忆缓存	core/short_memory/memory_buffer.py
数据模型	database/model.py
数据服务操作	database/services.py
定时器调度	database/scheduler.py
工具函数	utils/toolbox.py
各 Agent 实现	agents/ 目录下七个模块


## 结言

该项目是一个成熟的多 Agent + 多模态合作设计，适合作为本地 AI 语音/定时/助理型应用的基础库，其构成性、分层性和抽象级别明确。

🚀 可展望方向：动作库扩展、Unity 口型动作管理、人物无缝软切换、定制化资料记忆库、n8n 自动化搭配。
