"""
Huiyin - Xiaomi MiMo Adapter
"""
import json
from typing import List, Optional

import httpx

from core.llm.openai_compat import OpenAICompatAdapter
from core.models import DualTrackResponse, Message, Role


class MimoAdapter(OpenAICompatAdapter):
    """MiMo supports the OpenAI chat schema, but its docs prefer the api-key header."""

    def __init__(self, api_key: str, base_url: str, model_name: str):
        super().__init__(api_key=api_key, base_url=base_url, model_name=model_name)
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.fallback_base_url = "https://api.xiaomimimo.com/v1"

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

        api_messages = [{"role": "system", "content": system_prompt}]
        for msg in messages:
            role = "user" if msg.role == Role.USER else "assistant"
            content = msg.content
            if msg.timestamp:
                time_str = msg.timestamp.strftime("%Y-%m-%d %H:%M:%S")
                if msg.role != Role.SYSTEM:
                    content = f"[{time_str}] {content}"
            api_messages.append({"role": role, "content": content})

        payload = {
            "model": self.model,
            "messages": api_messages,
            "response_format": {"type": "json_object"},
            "max_completion_tokens": 1024,
            "temperature": 0.9,
            "top_p": 0.95,
            "stream": False,
        }

        response = self._post_chat_completion(payload)
        if response.is_error:
            raise RuntimeError(
                f"MiMo API error {response.status_code}: {response.text}"
            )

        data = response.json()
        raw = data["choices"][0]["message"]["content"]
        return self._parse_response(raw)

    def _post_chat_completion(self, payload: dict) -> httpx.Response:
        headers = {
            "api-key": self.api_key,
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        body = json.dumps(payload)
        urls = [self.base_url]
        if self.base_url != self.fallback_base_url:
            urls.append(self.fallback_base_url)

        last_error = None
        for base_url in urls:
            try:
                return httpx.post(
                    f"{base_url}/chat/completions",
                    headers=headers,
                    content=body,
                    timeout=60,
                )
            except httpx.ConnectError as exc:
                last_error = exc

        raise RuntimeError(f"MiMo API connection failed: {last_error}")
