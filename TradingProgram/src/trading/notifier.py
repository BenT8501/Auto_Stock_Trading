from __future__ import annotations

import os
from typing import Protocol

import requests


class Notifier(Protocol):
    def notify(self, message: str) -> None:
        ...


class ConsoleNotifier:
    def notify(self, message: str) -> None:
        print(message)


class TelegramNotifier:
    def __init__(self, token: str, chat_id: str) -> None:
        self.token = token
        self.chat_id = chat_id

    @classmethod
    def from_config(cls, config: dict) -> "TelegramNotifier | None":
        telegram = config.get("notifications", {}).get("telegram", {})
        if not telegram.get("enabled", False):
            return None
        token = os.getenv(str(telegram.get("bot_token_env", "TELEGRAM_BOT_TOKEN")))
        chat_id = os.getenv(str(telegram.get("chat_id_env", "TELEGRAM_CHAT_ID")))
        if not token or not chat_id:
            return None
        return cls(token, chat_id)

    def notify(self, message: str) -> None:
        response = requests.post(
            f"https://api.telegram.org/bot{self.token}/sendMessage",
            json={"chat_id": self.chat_id, "text": message},
            timeout=10,
        )
        response.raise_for_status()


class CompositeNotifier:
    def __init__(self, notifiers: list[Notifier]) -> None:
        self.notifiers = notifiers

    @classmethod
    def from_config(cls, config: dict) -> "CompositeNotifier":
        notifiers: list[Notifier] = [ConsoleNotifier()]
        telegram = TelegramNotifier.from_config(config)
        if telegram is not None:
            notifiers.append(telegram)
        return cls(notifiers)

    def notify(self, message: str) -> None:
        for notifier in self.notifiers:
            notifier.notify(message)
