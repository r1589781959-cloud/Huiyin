# 回音（Huiyin）

回音是一个使用 Python 开发的陪伴型 AI 原型。它不仅能够根据当前对话生成回复，还支持保存对话记忆、维护用户画像，并通过定时任务在合适的时间主动发起下一次交流。

项目目前主要用于本地开发和功能验证，已经实现命令行交互，并预留了 Telegram、微信等消息通道的扩展位置。

## 主要功能

- **多模型支持**：可接入 DeepSeek、Gemini、MiMo，以及兼容 OpenAI API 格式的服务。
- **连续对话**：保存用户和 AI 的历史消息，为后续回复提供上下文。
- **用户记忆**：从历史对话中读取相关信息，并生成用户画像摘要。
- **主动消息**：通过调度器保存未来任务，在指定时间主动继续对话。
- **结构化响应**：模型能够同时返回当前回复和未来任务计划。
- **通道扩展**：当前支持 CLI 命令行交互，并为其他消息平台保留统一接口。
- **本地数据存储**：对话记录、日志等运行数据默认保存在本机，不会提交到 Git 仓库。

## 当前状态

| 模块 | 状态 | 说明 |
| --- | --- | --- |
| CLI 命令行通道 | 可用 | 可以直接在终端中与回音对话 |
| DeepSeek | 可用 | 需要配置 DeepSeek API Key |
| Gemini | 可用 | 需要配置 Gemini API Key |
| MiMo | 可用 | 支持配置模型名称和 API 地址 |
| OpenAI 兼容接口 | 可用 | 可连接采用 OpenAI Chat Completions 格式的服务 |
| 对话记忆 | 可用 | 使用本地 SQLite 数据库存储 |
| 主动消息调度 | 可用 | 程序运行期间可以触发未来任务 |
| Telegram 通道 | 预留 | 已有目录和配置项，尚未接入主程序 |
| 微信通道 | 预留 | 已有目录，尚未实现 |

## 项目结构

```text
Huiyin/
├─ README.md
├─ .gitignore
└─ huiyin/
   ├─ main.py                 # 程序入口和组件初始化
   ├─ requirements.txt        # Python 依赖
   ├─ .env.example            # 环境变量配置模板
   ├─ channels/               # 消息通道
   │  ├─ base.py              # 通道抽象接口
   │  ├─ cli.py               # 命令行通道
   │  ├─ telegram/            # Telegram 预留目录
   │  └─ wechat/              # 微信预留目录
   ├─ config/
   │  └─ settings.py          # 配置读取与校验
   ├─ core/
   │  ├─ models.py            # 消息、回复和未来任务数据模型
   │  ├─ engine/
   │  │  ├─ dual_track.py     # 当前回复与未来任务处理
   │  │  ├─ memory.py         # 对话记忆和用户画像
   │  │  └─ scheduler.py      # 主动消息调度
   │  └─ llm/                 # 各模型服务适配器
   ├─ memory/                 # 记忆模块扩展目录
   └─ skills/                 # 技能接口与扩展目录
```

以下内容只会在本地生成，不会上传到 GitHub：

- `huiyin/.env`：API Key 和本地配置
- `huiyin/data/`：数据库、对话记录和日志
- `huiyin/venv/`：Python 虚拟环境
- `__pycache__/`：Python 缓存文件

## 环境要求

- Python 3.10 或更高版本
- Windows、Linux 或 macOS
- 至少一个受支持模型服务的 API Key

## 安装

### 1. 克隆仓库

```bash
git clone https://github.com/r1589781959-cloud/Huiyin.git
cd Huiyin/huiyin
```

也可以直接下载仓库压缩包，解压后进入 `huiyin` 目录。

### 2. 创建虚拟环境

Windows PowerShell：

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

Windows CMD：

```bat
python -m venv venv
venv\Scripts\activate.bat
```

Linux 或 macOS：

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

## 配置

先复制配置模板：

Windows PowerShell：

```powershell
Copy-Item .env.example .env
```

Linux 或 macOS：

```bash
cp .env.example .env
```

然后编辑 `.env`，选择一个模型服务并填写对应的 API Key。

### DeepSeek 示例

```dotenv
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=填写你的_API_Key
DEEPSEEK_MODEL=deepseek-chat
```

### Gemini 示例

```dotenv
LLM_PROVIDER=gemini
GEMINI_API_KEY=填写你的_API_Key
GEMINI_MODEL=gemini-3.5-flash
```

### MiMo 示例

```dotenv
LLM_PROVIDER=mimo
MIMO_API_KEY=填写你的_API_Key
MIMO_MODEL=mimo-v2-pro
MIMO_BASE_URL=https://api.mimo-v2.com/v1
```

### OpenAI 兼容接口示例

```dotenv
LLM_PROVIDER=openai_compat
OPENAI_COMPAT_API_KEY=填写你的_API_Key
OPENAI_COMPAT_BASE_URL=https://api.openai.com/v1
OPENAI_COMPAT_MODEL=gpt-4o
```

### 其他配置

| 配置项 | 默认值 | 说明 |
| --- | --- | --- |
| `CHANNEL` | `cli` | 消息通道；当前请使用 `cli` |
| `DATA_DIR` | `./data` | 数据库和日志的本地保存目录 |
| `LOG_LEVEL` | `INFO` | 日志等级，例如 `DEBUG`、`INFO`、`WARNING` |
| `TELEGRAM_BOT_TOKEN` | 空 | Telegram 预留配置，当前尚未接入 |
| `TELEGRAM_CHAT_ID` | 空 | Telegram 预留配置，当前尚未接入 |

请勿把真实 API Key 写入 `.env.example`、源码或 README。项目已经通过 `.gitignore` 排除 `.env`，但提交前仍建议使用 `git status` 检查待提交文件。

## 运行

确认当前终端位于 `huiyin` 目录，并且虚拟环境已经激活：

```bash
python main.py
```

启动后可以直接在终端输入消息：

```text
You: 你好

Huiyin: 你好，今天过得怎么样？
```

输入以下任意命令可以退出：

```text
quit
exit
q
```

也可以按 `Ctrl+C` 停止程序。

## 数据与隐私

默认情况下，程序会在 `huiyin/data/` 中创建数据库和日志文件。这里可能包含真实对话内容，因此该目录已经被 Git 忽略。

公开或分享项目之前，请重点确认以下内容没有进入提交：

```bash
git status
git ls-files
```

不应出现在公开仓库中的内容包括：

- `.env` 和任何真实 API Key
- `.db`、`.sqlite` 等数据库文件
- `.log` 日志文件
- 用户聊天记录和个人资料
- 本地虚拟环境与缓存文件

如果密钥曾经被提交或上传，即使后来删除文件，也应立即前往对应服务商后台撤销旧密钥并生成新密钥。

## 常见问题

### 启动时提示缺少 API Key

检查 `.env` 中的 `LLM_PROVIDER` 是否与填写的密钥一致。例如选择 `deepseek` 时，必须填写 `DEEPSEEK_API_KEY`。

### 修改 `.env` 后没有生效

重新启动程序。配置会在程序启动时从 `huiyin/.env` 加载。

### 数据保存在哪里

默认保存在当前 `huiyin` 目录下的 `data/` 文件夹。可以通过 `.env` 中的 `DATA_DIR` 修改位置。

### 为什么 Telegram 或微信通道无法使用

当前版本只完成了 CLI 通道。Telegram 和微信目录属于扩展预留，尚未连接到程序入口。

### 主动消息为什么必须保持程序运行

当前调度器运行在本地进程中。程序退出后，尚未触发的定时任务不会继续在后台执行。

## 安全提示

- 不要上传 `.env`、数据库、日志或真实聊天记录。
- 不要在 Issue、截图或提交记录中展示完整 API Key。
- 仅从可信来源安装依赖，并建议始终使用虚拟环境。
- 本项目仍处于原型阶段，不建议直接用于生产环境或处理敏感数据。

## 许可证

当前仓库暂未添加开源许可证。在许可证明确之前，默认保留全部权利。
