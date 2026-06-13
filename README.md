# Huiyin

Huiyin is a Python-based companion AI prototype with multiple LLM providers,
conversation memory, and scheduled proactive messages.

## Requirements

- Python 3.10 or later
- An API key for one supported LLM provider

## Installation

```powershell
cd huiyin
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Configuration

Copy the example environment file and fill in your own API key:

```powershell
Copy-Item .env.example .env
```

Set `LLM_PROVIDER` to `deepseek`, `gemini`, `mimo`, or `openai_compat`, then
configure the matching API key. The local `.env` file and runtime data are
excluded from Git.

## Run

```powershell
python main.py
```
