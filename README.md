# 🌟 AI 多模态语音助手系统 (GPT-SoVITS + DeepSeek + ToolAgent)

该项目是一个集成了语音识别 (ASR)，大语言模型生成 (LLM)，语音合成 (TTS)，多人物角色管理和记忆/任务管理二维 AI 助手系统，支持用户分离、记忆组织、任务提醒、定时 TTS 操作等功能。

---

## 🚀 项目启动

```bash
# 安装依赖
pip install -r requirements.txt

# 启动 Flask 后端 (5001 端口)
3090 gpu: 117.50.190.72     python app.py      40系gpu: 106.75.127.211    ./start.sh
```

---

## 🔧 核心流程说明

### 用户需求（输入语音/文本）

* `/api/dispatch` 接收用户请求，判断是 **语音输入** 还是 **文本输入**
* 如果是语音：保存文件，传入 `/api/asr`，调用 Faster-Whisper 转成文本

### 调度器处理

* 通过 MCP 协议打包为规范化消息
* 调用 `PlannerAgent` 解析意图，根据 DeepSeek 生成多 Agent 调用计划：

  * MemoryAgent: 操作记忆/任务
  * ToolAgent: 切换角色/操作本地应用
  * SearchAgent: 联网搜索
* 后续给 ChatAgent 进行最终展示

### 回复生成 + 语音合成

* ChatAgent 采用 `qwen-plus` 生成文本回复
* 后续传入 `/api/tts`，调用 GPT-SoVITS API 进行合成
* 同时进行简单情绪分析，返回 Base64 音频 + 角色信息

### 需要时间触发

* 所有 `add_todo`任务，创建后自动被 `scheduler.py` 扫描和定时 trigger
* 到点后调用 `/api/tts` + `say` 操作播放声音

---

## 🤖 Agent 体系

| Agent          | 作用                                       |
| -------------- | ---------------------------------------- |
| `PlannerAgent` | 识别用户 intent，生成规范化调度列表                    |
| `MemoryAgent`  | 操作 memory / personality / todo 数据，进行综合维护 |
| `ToolAgent`    | 调用 toolbox.py 本地功能，如播放音乐，切换角色            |
| `SearchAgent`  | 联网搜索 (日期/天气)                             |
| `ChatAgent`    | 体环，构造文本回复，进行 TTS                         |

---

##  执行流程与模块对照图

```
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
```

---

## 📄 数据库表设计

### `users`

* user\_id (PK)
* created\_at

### `memory`

* id, user\_id (FK), role, type, content, created\_at

### `personality`

* (user\_id, type, tag) 为联合 PK
* content

### `todos`

* id, user\_id, owner\_type, title, due\_time, status, description

---

## 📊 短期记忆系统

* 保存最近 50 条记录 (role + text)
* 在 ChatAgent / MemoryAgent / ToolAgent 中使用
* 可通过 `clear_short_term(user_id)` 清空

---

## 🎧 语音功能模块

### ASR

* 基于 Faster-Whisper
* 16kHz 单声道标准化，自动转简体

### TTS

* 基于 GPT-SoVITS API
* 支持角色预设、prompt文本、情绪控制

---

## 📁 代码位置快速索引（路径定位）

| 功能                | 文件路径                                 |
| ----------------- | ------------------------------------ |
| Flask 启动          | `app.py`                             |
| MCP 构建格式          | `core/message/mcp_message.py`        |
| ASR 模块            | `core/audio/asr_server.py`           |
| TTS 合成            | `core/audio/generate_audio.py`       |
| Prompt 构建         | `core/llm/prompt_builder.py`         |
| Prompt 实现状态       | `core/llm/prompt_state.py`           |
| LLM API（DeepSeek） | `core/llm/deepseek_api.py`           |
| LLM API（通义）       | `core/llm/qwen_api.py`               |
| 短期记忆缓存            | `core/short_memory/memory_buffer.py` |
| 数据模型定义            | `database/model.py`                  |
| 数据服务操作            | `database/services.py`               |
| 定时器调度             | `database/scheduler.py`              |
| 工具函数集合            | `utils/toolbox.py`                   |
| 各 Agent 实现        | `agents/` 目录下所有模块                    |

---

## 计划：
模块方向	简述目标
5🎭 2D Live 看板娘接入	使用 Unity 显示角色表情、嘴型、动作，与语音联动；通过 WebSocket 实时控制。                         
2🧠 Agent部分 ，继续更新，向着crewAi 和mnn chat （crewAi 为主，MNN chat 参考其轻量化设计）         （手搓版就是已经差不多了，后续需要优化结构和逻辑）
3💬 前端 UI 优化	完善多端聊天界面（桌面/移动），包含角色头像、情绪切换按钮、气泡语音动画等。
2🛠 ToolAgent 功能拓展	增加更多本地系统调用能力：如定时任务、应用控制、角色切换、自定义声音等。
2🔐 用户数据隔离与安全控制	
4🕸 图数据库与知识图谱系统	将 memory/personality/todo 等存储转为图结构（如 neo4j），支持结构化检索与可视关系图分析。 （如果要改就得早一些，不然后期要大改）
5🎙 实时语音唤醒（Wake Word Detection）


## 备注：
目前app.py下 alarm 和整体闹钟与计划没有更新到服务器版本，qq_bot在进行中


## 结言

该项目是一个成熟的多 Agent + 多模态合作设计，适合作为本地 AI 语音/定时/助理型应用的基础库，其构成性、分层性和抽象级别明确。

🚀 可展望方向：动作库扩展、Unity 口型动作管理、人物无缝软切换、定制化资料记忆库、n8n 自动化搭配。
