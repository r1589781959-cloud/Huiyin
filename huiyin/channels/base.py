"""
Huiyin - Channel Base Class
All message channels must implement this interface.
"""
import time
from abc import ABC, abstractmethod
from typing import Callable
from core.models import Message


class Channel(ABC):

    @abstractmethod
    def send(self, text: str) -> None:
        raise NotImplementedError

    def send_split(self, messages: list, delays: list) -> None:
        for text, delay in zip(messages, delays):
            time.sleep(max(0, delay))
            self.send(text)

    @abstractmethod
    def on_receive(self, callback: Callable[[Message], None]) -> None:
        raise NotImplementedError

    @abstractmethod
    def start(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def stop(self) -> None:
        raise NotImplementedError
