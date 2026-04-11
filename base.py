"""Base module for prompt management system."""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class PromptVersion:
    """Represents a single prompt version with metadata.
    
    Attributes:
        name: Unique identifier for this prompt version.
        strategy: The strategy type (e.g., hook_focus, storytelling, contrarian).
        content: The actual prompt text.
        metadata: Additional metadata about this prompt version.
    """
    
    name: str
    strategy: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)


class PromptStrategy(ABC):
    """Abstract base class for prompt strategies."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Return the unique name of this strategy."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Return a human-readable description of this strategy."""
        pass
    
    @abstractmethod
    def generate_prompt(self, **kwargs: Any) -> str:
        """Generate the prompt content based on provided parameters.
        
        Args:
            **kwargs: Strategy-specific parameters for prompt generation.
            
        Returns:
            The generated prompt string.
        """
        pass


class PromptManager:
    """Manages loading and retrieval of prompt versions.
    
    This class handles loading prompts from the versions directory
    and provides utilities for version selection and management.
    """
    
    def __init__(self, versions_dir: str | Path | None = None) -> None:
        """Initialize the PromptManager.
        
        Args:
            versions_dir: Path to the versions directory. Defaults to ./versions.
        """
        if versions_dir is None:
            versions_dir = Path(__file__).parent / "versions"
        self.versions_dir = Path(versions_dir)
        self._prompts: dict[str, PromptVersion] = {}
        self._load_prompts()
    
    def _load_prompts(self) -> None:
        """Load all prompt versions from the versions directory."""
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
            except (json.JSONDecodeError, IOError) as e:
                continue
    
    def get_prompt(self, name: str) -> PromptVersion | None:
        """Retrieve a specific prompt version by name.
        
        Args:
            name: The name of the prompt version to retrieve.
            
        Returns:
            The PromptVersion if found, None otherwise.
        """
        return self._prompts.get(name)
    
    def list_prompts(self) -> list[str]:
        """Get a list of all available prompt names.
        
        Returns:
            List of prompt names currently loaded.
        """
        return list(self._prompts.keys())
    
    def get_prompts_by_strategy(self, strategy: str) -> list[PromptVersion]:
        """Get all prompts matching a specific strategy.
        
        Args:
            strategy: The strategy type to filter by.
            
        Returns:
            List of PromptVersion objects matching the strategy.
        """
        return [p for p in self._prompts.values() if p.strategy == strategy]
    
    def reload(self) -> None:
        """Reload all prompts from the versions directory."""
        self._prompts.clear()
        self._load_prompts()
