"""
Huiyin - CLI Channel
Terminal-based channel for local development and testing.
"""
import threading
from datetime import datetime
from typing import Callable, Optional
from core.models import Message, Role
from channels.base import Channel


class CLIChannel(Channel):

    def __init__(self):
        self._callback: Optional[Callable[[Message], None]] = None
        self._running = False

    def send(self, text: str) -> None:
        print(f"\n  Huiyin: {text}\n")

    def on_receive(self, callback: Callable[[Message], None]) -> None:
        self._callback = callback

    def start(self) -> None:
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running = False

    def _loop(self) -> None:
        print("\n" + "=" * 40)
        print("  Huiyin CLI  |  type 'quit' to exit")
        print("=" * 40 + "\n")
        while self._running:
            try:
                text = input("You: ").strip()
            except (EOFError, KeyboardInterrupt):
                break
            if text.lower() in ("quit", "exit", "q"):
                self._running = False
                break
            if not text or not self._callback:
                continue
            msg = Message(role=Role.USER, content=text, timestamp=datetime.now())
            self._callback(msg)
