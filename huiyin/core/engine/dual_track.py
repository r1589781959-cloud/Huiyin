"""
回音 - 双轨对话引擎
Phase 1 实现。Phase 0 阶段仅作为直通层，将消息透传给 LLM。
"""

import time
from typing import List, Optional

from core.models import DualTrackResponse, Message
from core.llm.base import LLMAdapter


class DualTrackEngine:
    """
    Phase 0 仅实现当下轨的直通调用。
    """

    def __init__(
        self, 
        llm: LLMAdapter, 
        enable_proactive: bool = True,
        enable_time_bounds: bool = False,
        min_interval_minutes: int = 3, 
        max_interval_minutes: int = 60
    ):
        self.llm = llm
        self.enable_proactive = enable_proactive
        self.enable_time_bounds = enable_time_bounds
        self.min_interval_minutes = min_interval_minutes
        self.max_interval_minutes = max_interval_minutes

    def _chat_with_validation(
        self,
        messages: List[Message],
        user_profile: str,
        hidden_context: str
    ) -> DualTrackResponse:
        from core.models import Role
        from datetime import datetime, timezone
        from loguru import logger
        
        MAX_RETRIES = 1
        current_messages = list(messages)
        
        for attempt in range(MAX_RETRIES + 1):
            response = self.llm.chat(
                current_messages, 
                user_profile, 
                hidden_context, 
                enable_proactive=self.enable_proactive,
                enable_time_bounds=self.enable_time_bounds,
                min_interval_minutes=self.min_interval_minutes,
                max_interval_minutes=self.max_interval_minutes
            )
            
            if not self.enable_proactive:
                return response
                
            ft = response.future_task
            if not ft or not ft.trigger_time:
                return response
                
            now_utc = datetime.now(timezone.utc)
            delay_minutes = (ft.trigger_time - now_utc).total_seconds() / 60.0
            
            error_msg = ""
            if delay_minutes <= 0:
                error_msg = f"你设定的时间是个已经过去的时间（时光倒流）。"
            elif self.enable_time_bounds and not getattr(ft, 'force_break_bounds', False):
                if delay_minutes < self.min_interval_minutes:
                    error_msg = f"你设定的时间间隔太短（仅 {delay_minutes:.1f} 分钟）。如果不开启特权开关，常规闲聊时间间隔必须 >= {self.min_interval_minutes} 分钟。"
                elif delay_minutes > self.max_interval_minutes:
                    error_msg = f"你设定的时间间隔太长（{delay_minutes:.1f} 分钟）。如果不开启特权开关，常规闲聊时间间隔必须 <= {self.max_interval_minutes} 分钟。"
            
            if error_msg and attempt < MAX_RETRIES:
                logger.warning(f"大模型时间设定违规: {error_msg} 正在发起第 {attempt+1} 次自我纠错。")
                if self.enable_time_bounds:
                    error_prompt = f"【系统退回通知】：你刚才设定的计划被系统驳回。原因：{error_msg}请重新结合当前时间规划你的主动回复时间和对话内容。如果你想突破 {self.min_interval_minutes}~{self.max_interval_minutes} 分钟的常规限制，请在 JSON 中设置 force_break_bounds=true 并给出理由。"
                else:
                    error_prompt = f"【系统退回通知】：你刚才设定的计划被系统驳回。原因：{error_msg}请重新规划一个大于当前时间的合理主动回复时间。"
                current_messages.append(Message(role=Role.USER, content=error_prompt))
                continue
                
            return response
            
        return response

    def process(
        self,
        messages: List[Message],
        user_profile: str = "",
        hidden_context: str = "",
    ) -> DualTrackResponse:
        """处理一次用户主动发来的消息"""
        return self._chat_with_validation(
            messages=messages,
            user_profile=user_profile,
            hidden_context=hidden_context,
        )

    def process_deferred(
        self,
        messages: List[Message],
        task_reason: str,
        user_profile: str = "",
    ) -> DualTrackResponse:
        """
        处理未来轨触发的延迟任务。
        将 task_reason 组装成一条强提示的伪造用户消息，让大模型明确意识到自己被唤醒了。
        """
        from core.models import Role
        system_event = Message(
            role=Role.USER,
            content=f"【系统事件】：自你上一条消息后，用户一直没有回复。你定下的闹钟响了，设定的原因为：“{task_reason}”。请根据这个原因，自然地主动开口去找他说话（不要暴露这是个系统事件）。"
        )
        
        context_with_trigger = messages + [system_event]
        
        return self._chat_with_validation(
            messages=context_with_trigger,
            user_profile=user_profile,
            hidden_context="你现在是在异步主动寻找用户。请务必设定好下一次寻找他的 future_task。",
        )
