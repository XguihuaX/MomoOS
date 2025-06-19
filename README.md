# 🌟 AI 多模态语音助手系统 (GPT-SoVITS + DeepSeek + ToolAgent)

该项目是一个集成了语音识别 (ASR)，大语言模型生成 (LLM)，语音合成 (TTS)，多人物角色管理和记忆/任务管理二维 AI 助手系统，支持用户分离、记忆组织、任务提醒、定时 TTS 操作等功能。

---

## 🚀 项目启动

```bash
# 安装依赖
pip install -r requirements.txt

# 启动 Flask 后端 (5001 端口)
./start.sh 或 python app.py
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

## 🚧 本地功能 (系统/GUI)

ToolAgent 通过 `toolbox.py` 调用以下功能：

* 操作 macOS 通知
* 播放语音提醒
* 操作等 pyautogui 应用 (ex: 播放音乐)
* 切换聊天角色

---

## 结言

该项目是一个成熟的多 Agent + 多模态合作设计，适合作为本地 AI 语音/定时/助理型应用的基础库，其构成性、分层性和抽象级别明确。

🚀 可展望方向：动作库扩展、Unity 口型动作管理、人物无缝软切换、定制化资料记忆库、n8n 自动化搭配。
