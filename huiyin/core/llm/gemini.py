"""
Huiyin - Gemini Adapter
Uses the new Google GenAI SDK.
"""
import json
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from google import genai
from google.genai import types

from config.settings import settings
from core.models import (
    DualTrackResponse, FutureTask, GenerationMode,
    Message, Role, SplitMessage, TaskStatus
)
from core.llm.base import LLMAdapter


class GeminiAdapter(LLMAdapter):

    def __init__(self):
        # Initialize the new GenAI client
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.model_name = settings.GEMINI_MODEL

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
            max_interval_minutes,
        )

        api_messages = []
        for msg in messages:
            # The new SDK uses "user" and "model" for roles
            role = "user" if msg.role == Role.USER else "model"
            content = msg.content
            if msg.timestamp:
                time_str = msg.timestamp.strftime("%Y-%m-%d %H:%M:%S")
                if msg.role != Role.SYSTEM:
                    content = f"[{time_str}] {content}"
            api_messages.append(
                types.Content(
                    role=role,
                    parts=[types.Part.from_text(text=content)]
                )
            )

        # Generate content with system instructions and JSON mode
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=api_messages,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                response_mime_type="application/json",
                temperature=0.9,
            )
        )

        raw = response.text
        return self._parse_response(raw)

    def _parse_response(self, raw: str) -> DualTrackResponse:
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return DualTrackResponse(reply=raw, delay_seconds=1.5)

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
                local_time_str = ft.get("trigger_time", "")
                local_dt = datetime.strptime(local_time_str, "%Y-%m-%d %H:%M:%S")
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
