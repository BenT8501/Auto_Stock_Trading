from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ChatMemory:
    max_messages: int = 20
    messages: list[dict[str, str]] = field(default_factory=list)

    def add(self, role: str, content: str) -> None:
        self.messages.append({"role": role, "content": content})
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages :]

    def history(self) -> list[dict[str, str]]:
        return list(self.messages)
