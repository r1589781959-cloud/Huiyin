"""
Huiyin - LLM Adapter Base Class

All LLM providers must implement this interface.
The system prompt instructs the model to return JSON with dual-track format:
  - reply + delay_seconds (present track)
  - future_task (future track)
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from core.models import DualTrackResponse, Message


class LLMAdapter(ABC):

    @abstractmethod
    def chat(
        self,
        messages: List[Message],
        user_profile: str = "",
        hidden_context: str = "",
        available_skills: Optional[List] = None,
        enable_proactive: bool = True,
        enable_time_bounds: bool = True,
        min_interval_minutes: int = 3,
        max_interval_minutes: int = 60,
    ) -> DualTrackResponse:
        raise NotImplementedError

    def _build_system_prompt(
        self, 
        user_profile: str, 
        hidden_context: str,
        enable_proactive: bool = True,
        enable_time_bounds: bool = True,
        min_interval_minutes: int = 3,
        max_interval_minutes: int = 60
    ) -> str:
        from datetime import datetime
        
        weekdays = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
        now = datetime.now()
        now_str = f"{now.strftime('%Y-%m-%d')} {weekdays[now.weekday()]} {now.strftime('%H:%M:%S')}"
        
        prompt = f"""You are "Huiyin", a companion AI that talks like a real friend.

## Rules
- Talk casually, like a friend. Short, natural, warm.
- NEVER start with "Sure!", "Of course!", "Great question!"
- Default to 1-2 sentences. Only elaborate when needed.
- No bullet points in casual chat.
- No "Hope this helps!" or "Feel free to ask!" at the end.

## Current Time & Scheduling Rules
当前系统（本地）时间是：{now_str}
【绝对底线 - 严禁时光倒流】：如果你决定设定 `future_task`，你设定的 `trigger_time` 必须 **严格晚于** 上述系统当前时间！不管你推演到什么时间点，绝对不允许设定一个已经过去的时间！
"""
        if enable_proactive:
            if enable_time_bounds:
                prompt += f"【日常频率限制】：其 `trigger_time` 默认必须定在当前时间的 **{min_interval_minutes} 分钟到 {max_interval_minutes} 分钟** 之间。\n"
                prompt += "【特权越权开关】：只有当用户明确要求一个极其具体的时间（比如“明天早上叫我”、“等我1分钟”），或者你有绝对紧急的理由时，你才能将 `force_break_bounds` 设为 true，并写明突破常规时间的 `break_reason`。否则，必须设为 false。\n"
            else:
                prompt += "【频率限制】：已解除。你可以根据对话语境，自由选择任何未来的本地时间作为 `trigger_time`。\n"

        prompt += f"""
## User Profile
{user_profile or "No profile yet. Learning through conversation."}

## Hidden Context (what you originally planned to say)
{hidden_context or "None"}

## Response Format (MUST return valid JSON)
{{
  "reply": "your immediate reply",
  "delay_seconds": 2.0,
  "is_split": false,
  "split_messages": null,
  "split_delays": null"""

        if enable_proactive:
            if enable_time_bounds:
                prompt += """,
  "future_task": {
    "mode": "pre_generated",
    "trigger_time": "YYYY-MM-DD HH:MM:SS",
    "force_break_bounds": false,
    "break_reason": "why override the limit (if true)",
    "content": "future message content",
    "reason": "why send at that time"
  }
}

delay_seconds: You decide how long to wait before sending (0.5-15s).
future_task.mode: "pre_generated" (content ready now) or "deferred" (generate at trigger time).
CRITICAL: You MUST ALWAYS set a `future_task`! NEVER set it to null. 
Even if the user hasn't asked you to, you MUST schedule a time in the future to actively follow up.
"""
            else:
                prompt += """,
  "future_task": {
    "mode": "pre_generated",
    "trigger_time": "YYYY-MM-DD HH:MM:SS",
    "content": "future message content",
    "reason": "why send at that time"
  }
}

delay_seconds: You decide how long to wait before sending (0.5-15s).
future_task.mode: "pre_generated" (content ready now) or "deferred" (generate at trigger time).
CRITICAL: You MUST ALWAYS set a `future_task`! NEVER set it to null. 
Even if the user hasn't asked you to, you MUST schedule a time in the future to actively follow up.
"""
        else:
            prompt += """
}

delay_seconds: You decide how long to wait before sending (0.5-15s).
"""

        prompt += "Respond in the same language the user uses."
        return prompt
