# 回音（Huiyin）

回音是一个使用 Python 开发的陪伴型 AI 项目。目前项目处于原型验证阶段，重点探索自然对话、长期记忆、多模型接入和主动陪伴等能力。

当前版本可以在本地命令行中运行，支持连接多种大语言模型，并将对话记录保存在本地数据库中。

## 项目背景

大多数 AI 助手以问答和任务处理为主。用户发出消息，AI 才开始工作；对话结束后，它也随之安静下来。这种方式适合查资料和解决问题，但很难形成持续的陪伴感。

有些人并不缺少一个随时能回答问题的工具。他们更需要的是一种轻量、自然的联系：记得之前聊过什么，理解最近的状态，偶尔主动问一句，而不是每次都等用户重新打开聊天框。

回音就是从这个想法开始的。名字里的“回”是回来，“音”是声音。项目希望做一个能延续对话、保留记忆，并在合适的时候主动联系用户的 AI 陪伴体。

它主要面向以下使用场景：

- 独居、异地生活或日常社交较少，希望有人偶尔主动联系
- 工作和学习节奏紧张，没有精力长期维护高频社交
- 希望 AI 能记住过往交流，而不是每次从头认识
- 对本地运行、数据隐私和自定义模型有要求

回音仍是实验性项目。它不能替代真实的人际关系，也不用于提供医疗、心理诊断或紧急援助。当前阶段主要验证自然对话、记忆延续和主动陪伴是否能组合成一种更接近长期交流的体验。

## 功能概览

- 支持 DeepSeek、Gemini、MiMo 和 OpenAI 兼容接口
- 支持命令行连续对话
- 支持本地保存历史消息
- 支持历史消息全文检索
- 支持基础的主动消息与定时任务
- 提供统一的模型和消息通道扩展接口
- API Key、聊天记录和日志默认只保存在本机

## 项目进度

### 已完成

| 功能 | 当前状态 |
| --- | --- |
| 项目基础结构 | 已完成 |
| CLI 命令行交互 | 已完成 |
| DeepSeek 接入 | 已完成 |
| Gemini 接入 | 已完成 |
| MiMo 接入 | 已完成 |
| OpenAI 兼容接口 | 已完成 |
| SQLite 对话存储 | 已完成 |
| 历史消息全文检索 | 已完成 |
| 基础定时任务 | 已完成 |
| 日志和环境变量配置 | 已完成 |

### 开发中

- 用户画像与长期记忆整理
- 更稳定的上下文管理
- 主动消息体验优化
- 异常处理和运行稳定性改进
- 技能系统的实际功能接入

### 后续计划

- 接入 Telegram 消息通道
- 研究微信消息通道的可行方案
- 增加更多可调用技能
- 增加配置界面或管理界面
- 补充自动化测试
- 优化安装和部署流程

> 以上进度以当前仓库代码为准，Telegram 和微信目录目前仅用于预留扩展位置。

## 大致架构

项目按职责划分为交互层、应用层、模型适配层、数据层和扩展层：

```text
用户
 │
 ▼
消息通道
目前为 CLI，其他通道预留
 │
 ▼
应用入口与核心服务
负责配置加载、消息处理和组件协作
 ├──────────────┬──────────────┐
 ▼              ▼              ▼
模型适配层      记忆服务        任务调度服务
 │              │              │
 ▼              ▼              ▼
大模型 API      SQLite         本地后台任务
```

各模块的公开职责如下：

- `main.py`：程序启动入口，负责加载配置并初始化各项服务。
- `channels/`：消息输入与输出通道，当前实现 CLI。
- `config/`：读取 `.env` 配置并检查必要参数。
- `core/llm/`：不同大语言模型服务的适配器。
- `core/engine/`：对话、记忆和任务相关的核心服务。
- `core/models.py`：项目内部使用的数据模型。
- `skills/`：技能注册和后续能力扩展接口。
- `data/`：本地运行时生成的数据目录，不会上传到 GitHub。

## 项目结构

```text
Huiyin/
├─ README.md
├─ .gitignore
└─ huiyin/
   ├─ main.py
   ├─ requirements.txt
   ├─ .env.example
   ├─ channels/
   │  ├─ base.py
   │  ├─ cli.py
   │  ├─ telegram/
   │  └─ wechat/
   ├─ config/
   │  └─ settings.py
   ├─ core/
   │  ├─ models.py
   │  ├─ engine/
   │  └─ llm/
   ├─ memory/
   └─ skills/
```

## 环境要求

- Python 3.10 或更高版本
- Windows、Linux 或 macOS
- 至少一个受支持模型服务的 API Key
- 可以正常访问所选模型服务的网络环境

## Windows 快速启动

下面的命令以 PowerShell 为例。请按顺序执行。

### 1. 下载项目

```powershell
git clone https://github.com/r1589781959-cloud/Huiyin.git
cd Huiyin
```

如果没有安装 Git，也可以在 GitHub 页面点击 `Code`，选择 `Download ZIP`，解压后在终端中进入项目目录。

### 2. 创建虚拟环境并安装依赖

在仓库根目录执行：

```powershell
cd huiyin
python -m venv venv
.\venv\Scripts\python.exe -m pip install --upgrade pip
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

这里直接调用虚拟环境中的 Python，不要求手动激活虚拟环境。

### 3. 创建配置文件

```powershell
Copy-Item .env.example .env
notepad .env
```

在打开的 `.env` 文件中选择一个模型服务，并填写对应的 API Key。配置完成后保存并关闭记事本。

### 4. 启动项目

确认当前目录为 `Huiyin\huiyin`，然后执行：

```powershell
.\venv\Scripts\python.exe main.py
```

以后再次启动时，只需要进入项目目录并执行：

```powershell
cd Huiyin\huiyin
.\venv\Scripts\python.exe main.py
```

如果终端已经位于仓库根目录，则执行：

```powershell
cd huiyin
.\venv\Scripts\python.exe main.py
```

## macOS 和 Linux 快速启动

```bash
git clone https://github.com/r1589781959-cloud/Huiyin.git
cd Huiyin/huiyin

python3 -m venv venv
./venv/bin/python -m pip install --upgrade pip
./venv/bin/python -m pip install -r requirements.txt

cp .env.example .env
```

编辑 `.env` 并填写 API Key，然后启动：

```bash
./venv/bin/python main.py
```

## 模型配置

项目从 `huiyin/.env` 读取配置。只需要启用一个模型服务，并填写相应的 API Key。

### DeepSeek

```dotenv
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=填写你的_API_Key
DEEPSEEK_MODEL=deepseek-chat
```

### Gemini

```dotenv
LLM_PROVIDER=gemini
GEMINI_API_KEY=填写你的_API_Key
GEMINI_MODEL=gemini-3.5-flash
```

### MiMo

```dotenv
LLM_PROVIDER=mimo
MIMO_API_KEY=填写你的_API_Key
MIMO_MODEL=mimo-v2-pro
MIMO_BASE_URL=https://api.mimo-v2.com/v1
```

### OpenAI 兼容接口

```dotenv
LLM_PROVIDER=openai_compat
OPENAI_COMPAT_API_KEY=填写你的_API_Key
OPENAI_COMPAT_BASE_URL=https://api.openai.com/v1
OPENAI_COMPAT_MODEL=gpt-4o
```

如果使用其他兼容 OpenAI 接口格式的服务，请将 `OPENAI_COMPAT_BASE_URL` 和 `OPENAI_COMPAT_MODEL` 修改为服务商提供的值。

## 其他配置

| 配置项 | 默认值 | 说明 |
| --- | --- | --- |
| `CHANNEL` | `cli` | 消息通道，当前版本请使用 `cli` |
| `DATA_DIR` | `./data` | 数据库和日志保存目录 |
| `LOG_LEVEL` | `INFO` | 日志级别 |
| `TELEGRAM_BOT_TOKEN` | 空 | Telegram 预留配置 |
| `TELEGRAM_CHAT_ID` | 空 | Telegram 预留配置 |

## 使用方式

程序启动后，终端会显示输入提示：

```text
You:
```

输入消息并按回车即可开始对话。

输入以下任意命令可以退出：

```text
quit
exit
q
```

也可以按 `Ctrl+C` 停止程序。

## 常用命令

### Windows PowerShell

从仓库根目录启动：

```powershell
cd huiyin
.\venv\Scripts\python.exe main.py
```

重新安装依赖：

```powershell
cd huiyin
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

查看 Git 状态：

```powershell
git status
```

### macOS 或 Linux

从仓库根目录启动：

```bash
cd huiyin
./venv/bin/python main.py
```

## 本地数据与隐私

运行后，程序默认会在 `huiyin/data/` 中创建数据库和日志。这里可能包含真实聊天内容，因此该目录不会提交到 GitHub。

以下文件和目录也会被 Git 忽略：

- `huiyin/.env`
- `huiyin/data/`
- `huiyin/venv/`
- `__pycache__/`
- `*.db`
- `*.log`

提交代码前建议执行：

```bash
git status
```

确认 `.env`、数据库、日志和聊天记录没有出现在待提交文件中。

如果 API Key 曾经被上传到 GitHub，仅删除文件并不安全。请立即在对应服务商后台撤销旧 Key，并生成新的 Key。

## 常见问题

### 提示找不到 `python`

请先安装 Python，并在安装时勾选 `Add Python to PATH`。安装完成后重新打开终端。

### 提示缺少 API Key

检查以下内容：

1. `huiyin/.env` 文件是否存在。
2. `LLM_PROVIDER` 是否填写正确。
3. 是否填写了与该模型服务对应的 API Key。

例如使用 DeepSeek 时，应同时配置：

```dotenv
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=你的_Key
```

### 修改 `.env` 后没有生效

停止程序并重新启动。环境变量会在程序启动时加载。

### 依赖安装失败

先升级 pip，再重新安装：

Windows：

```powershell
.\venv\Scripts\python.exe -m pip install --upgrade pip
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

macOS 或 Linux：

```bash
./venv/bin/python -m pip install --upgrade pip
./venv/bin/python -m pip install -r requirements.txt
```

### 数据保存在哪里

默认保存在 `huiyin/data/`。可以通过 `.env` 中的 `DATA_DIR` 修改保存位置。

### 为什么 Telegram 或微信不能使用

当前公开版本只实现了 CLI 通道。Telegram 和微信相关目录目前是扩展预留。

### 为什么关闭程序后不会继续运行

当前版本是本地命令行程序。关闭终端或退出程序后，相关服务也会停止。

## 安全提示

- 不要上传 `.env`、数据库、日志和真实聊天记录。
- 不要在截图、Issue 或提交记录中展示完整 API Key。
- 建议始终使用独立虚拟环境安装依赖。
- 当前项目处于原型阶段，不建议直接用于生产环境或处理敏感数据。

## 许可证

当前仓库暂未添加开源许可证。在许可证明确之前，默认保留全部权利。
