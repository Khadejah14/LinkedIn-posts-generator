import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


class Feature(ABC):
    @abstractmethod
    def run(self, *args, **kwargs) -> Any:
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        pass


@dataclass
class PromptVersion:
    name: str
    strategy: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)


class PromptStrategy(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        pass

    @abstractmethod
    def generate_prompt(self, **kwargs: Any) -> str:
        pass


class PromptManager:
    def __init__(self, versions_dir: str | Path | None = None) -> None:
        if versions_dir is None:
            versions_dir = Path(__file__).parent.parent / "versions"
        self.versions_dir = Path(versions_dir)
        self._prompts: dict[str, PromptVersion] = {}
        self._load_prompts()

    def _load_prompts(self) -> None:
        if not self.versions_dir.exists():
            return
        for file_path in self.versions_dir.glob("*.json"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    version = PromptVersion(
                        name=data.get("name", file_path.stem),
                        strategy=data.get("strategy", "unknown"),
                        content=data.get("content", ""),
                        metadata=data.get("metadata", {})
                    )
                    self._prompts[version.name] = version
            except (json.JSONDecodeError, IOError):
                continue

    def get_prompt(self, name: str) -> PromptVersion | None:
        return self._prompts.get(name)

    def list_prompts(self) -> list[str]:
        return list(self._prompts.keys())

    def get_prompts_by_strategy(self, strategy: str) -> list[PromptVersion]:
        return [p for p in self._prompts.values() if p.strategy == strategy]

    def reload(self) -> None:
        self._prompts.clear()
        self._load_prompts()


import json