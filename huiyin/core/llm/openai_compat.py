"""
Huiyin - OpenAI Compatible Adapter
Supports OpenAI, MiMo, and other endpoints that use the OpenAI API format.
"""
import json
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from openai import OpenAI

from core.models import (
    DualTrackResponse, FutureTask, GenerationMode,
    Message, Role, SplitMessage, TaskStatus
)
from core.llm.base import LLMAdapter


class OpenAICompatAdapter(LLMAdapter):

    def __init__(self, api_key: str, base_url: str, model_name: str):
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url,
        )
        self.model = model_name

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
        system_prompt = self._build_system_prompt(
            user_profile, 
            hidden_context,
            enable_proactive,
            enable_time_bounds,
            min_interval_minutes,
            max_interval_minutes
        )

        api_messages = [{"role": "system", "content": system_prompt}]
        for msg in messages:
            role = "user" if msg.role == Role.USER else "assistant"
            content = msg.content
            if msg.timestamp:
                time_str = msg.timestamp.strftime("%Y-%m-%d %H:%M:%S")
                # 系统消息不需要加时间前缀（比如伪造的系统事件）
                if msg.role != Role.SYSTEM:
                    content = f"[{time_str}] {content}"
            api_messages.append({"role": role, "content": content})

        from loguru import logger
        
        # 为了防止刷屏，构造一个用于日志打印的精简版本
        log_messages = [api_messages[0]]  # 保留 System Prompt
        if len(api_messages) > 4:
            log_messages.append({"role": "system", "content": f"... [已隐藏 {len(api_messages)-3} 条中间历史记录] ..."})
            log_messages.extend(api_messages[-2:])
        else:
            log_messages.extend(api_messages[1:])
            
        logger.debug(f"📤 [发给大模型的完整包 (已折叠历史)]:\n{json.dumps(log_messages, ensure_ascii=False, indent=2)}")

        for attempt in range(2):
            response = self.client.chat.completions.create(
                model=self.model,
                messages=api_messages,
                response_format={"type": "json_object"},
                temperature=0.9,
            )

            raw = response.choices[0].message.content
            
            try:
                return self._parse_response(raw)
            except json.JSONDecodeError:
                if attempt == 0:
                    logger.warning(f"⚠️ 大模型输出 JSON 格式完全崩坏，启动自动回炉重造 (Reflection)...")
                    api_messages.append({"role": "assistant", "content": raw})
                    api_messages.append({"role": "user", "content": "【系统通知】：你刚才生成的响应不是规范的 JSON 格式（缺少闭合的大括号或混杂了额外文本）。请严格按照 JSON 规范，检查并补全所有缺失的括号，重新输出你的决定。"})
                else:
                    logger.error(f"❌ 大模型连续两次 JSON 格式严重错误，放弃挣扎，触发降级回复，原始输出为:\n{raw}")
                    return DualTrackResponse(reply=raw, delay_seconds=1.5)

    def _parse_response(self, raw: str) -> DualTrackResponse:
        import re
        
        # 尝试剥离大模型可能在外面加的废话（提取首尾大括号之间的内容）
        match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', raw, re.DOTALL)
        if match:
            raw_json = match.group(1)
        else:
            match = re.search(r'(\{.*\})', raw, re.DOTALL)
            raw_json = match.group(1) if match else raw
            
        # 脏数据暴力修复：清理大模型瞎输出的结尾比如 }"} 或 }"
        raw_json = re.sub(r'\}"?\}$', '}}', raw_json.strip())

        try:
            data = json.loads(raw_json)
        except json.JSONDecodeError:
            try:
                # 暴力修复 1：大模型漏了最后的大括号
                data = json.loads(raw_json + "}")
            except json.JSONDecodeError:
                try:
                    # 暴力修复 2：大模型漏了最后两个大括号
                    data = json.loads(raw_json + "}}")
                except json.JSONDecodeError as e:
                    # 终极修复也失败，直接抛出异常交给 chat 函数去执行“回炉重造”
                    raise e

        from loguru import logger
        formatted_json = json.dumps(data, ensure_ascii=False, indent=2)
        logger.debug(f"📥 [大模型返回的 JSON (格式化后)]:\n{formatted_json}")

        reply = data.get("reply", raw)
        delay = float(data.get("delay_seconds", 1.5))
        is_split = data.get("is_split", False)
        split_messages = data.get("split_messages")
        split_delays = data.get("split_delays")

        future_task = None
        ft = data.get("future_task")
        if ft and isinstance(ft, dict):
            mode = (
                GenerationMode.DEFERRED
                if ft.get("mode") == "deferred"
                else GenerationMode.PRE_GENERATED
            )
            try:
                # 解析本地时间大白话
                local_time_str = ft.get("trigger_time", "")
                local_dt = datetime.strptime(local_time_str, "%Y-%m-%d %H:%M:%S")
                # 转成系统本地时区的 aware datetime，然后再转为 UTC（调度器需要 UTC）
                trigger_time = local_dt.astimezone(timezone.utc)
            except (KeyError, ValueError, TypeError):
                trigger_time = datetime.now(timezone.utc) + timedelta(minutes=5)

            content = None
            if mode == GenerationMode.PRE_GENERATED and ft.get("content"):
                content = SplitMessage(messages=[ft["content"]], delays=[0.0])
                
            force_break_bounds = ft.get("force_break_bounds", False)
            break_reason = ft.get("break_reason", "")

            future_task = FutureTask(
                trigger_time=trigger_time,
                generation_mode=mode,
                content=content,
                reason=ft.get("reason", ""),
                force_break_bounds=force_break_bounds,
                break_reason=break_reason,
            )

        return DualTrackResponse(
            reply=reply,
            delay_seconds=delay,
            is_split=is_split,
            split_messages=split_messages,
            split_delays=split_delays,
            future_task=future_task,
        )
