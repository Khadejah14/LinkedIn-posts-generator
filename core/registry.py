"""Registry module for auto-discovery and A/B testing of prompt strategies."""

from __future__ import annotations

import random
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class ABTest:
    test_id: str
    prompt_a: str
    prompt_b: str
    traffic_split: float = 0.5
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: datetime | None = None
    results: dict[str, Any] = field(default_factory=dict)


@dataclass
class PromptMetrics:
    impressions: int = 0
    engagements: int = 0
    conversions: int = 0

    @property
    def engagement_rate(self) -> float:
        if self.impressions == 0:
            return 0.0
        return self.engagements / self.impressions

    @property
    def conversion_rate(self) -> float:
        if self.impressions == 0:
            return 0.0
        return self.conversions / self.impressions


class PromptRegistry:
    def __init__(self) -> None:
        self._strategies: dict[str, type] = {}
        self._prompts: dict[str, str] = {}
        self._ab_tests: dict[str, ABTest] = {}
        self._metrics: dict[str, PromptMetrics] = {}
        self._random_seed: int | None = None

    def discover_prompts(self, prompts_dir: str | Path | None = None) -> int:
        if prompts_dir is None:
            prompts_dir = Path(__file__).parent.parent / "versions"
        prompts_path = Path(prompts_dir)
        if not prompts_path.exists():
            return 0
        count = 0
        for file_path in prompts_path.glob("*.json"):
            try:
                from .base import PromptManager
                manager = PromptManager(prompts_dir)
                for name in manager.list_prompts():
                    if name not in self._prompts:
                        self._prompts[name] = name
                        self._metrics[name] = PromptMetrics()
                        count += 1
                break
            except Exception:
                pass
        return count

    def register_strategy(self, name: str, strategy_class: type) -> None:
        self._strategies[name] = strategy_class

    def register_prompt(self, name: str, content: str) -> None:
        self._prompts[name] = content
        if name not in self._metrics:
            self._metrics[name] = PromptMetrics()

    def get_prompt(self, name: str) -> str | None:
        return self._prompts.get(name)

    def list_prompts(self) -> list[str]:
        return list(self._prompts.keys())

    def list_strategies(self) -> list[str]:
        return list(self._strategies.keys())

    def create_ab_test(
        self,
        prompt_a: str,
        prompt_b: str,
        traffic_split: float = 0.5,
        test_id: str | None = None
    ) -> ABTest:
        if prompt_a not in self._prompts:
            raise ValueError(f"Prompt '{prompt_a}' is not registered")
        if prompt_b not in self._prompts:
            raise ValueError(f"Prompt '{prompt_b}' is not registered")
        if not 0.0 <= traffic_split <= 1.0:
            raise ValueError("traffic_split must be between 0.0 and 1.0")
        if test_id is None:
            test_id = str(uuid.uuid4())[:8]
        test = ABTest(
            test_id=test_id,
            prompt_a=prompt_a,
            prompt_b=prompt_b,
            traffic_split=traffic_split
        )
        self._ab_tests[test_id] = test
        return test

    def select_for_test(self, test: ABTest) -> str:
        if self._random_seed is not None:
            random.seed(self._random_seed)
        selected = random.choices(
            [test.prompt_a, test.prompt_b],
            weights=[test.traffic_split, 1 - test.traffic_split]
        )[0]
        self.record_impression(test.prompt_a)
        self.record_impression(test.prompt_b)
        return selected

    def record_impression(self, prompt_name: str) -> None:
        if prompt_name in self._metrics:
            self._metrics[prompt_name].impressions += 1

    def record_engagement(self, prompt_name: str) -> None:
        if prompt_name in self._metrics:
            self._metrics[prompt_name].engagements += 1

    def record_conversion(self, prompt_name: str) -> None:
        if prompt_name in self._metrics:
            self._metrics[prompt_name].conversions += 1

    def get_metrics(self, prompt_name: str) -> PromptMetrics | None:
        return self._metrics.get(prompt_name)

    def get_all_metrics(self) -> dict[str, PromptMetrics]:
        return self._metrics.copy()

    def get_test_results(self, test_id: str) -> dict[str, Any] | None:
        test = self._ab_tests.get(test_id)
        if test is None:
            return None
        metrics_a = self._metrics.get(test.prompt_a, PromptMetrics())
        metrics_b = self._metrics.get(test.prompt_b, PromptMetrics())
        return {
            "test_id": test_id,
            "variant_a": {
                "name": test.prompt_a,
                "impressions": metrics_a.impressions,
                "engagement_rate": metrics_a.engagement_rate,
                "conversion_rate": metrics_a.conversion_rate
            },
            "variant_b": {
                "name": test.prompt_b,
                "impressions": metrics_b.impressions,
                "engagement_rate": metrics_b.engagement_rate,
                "conversion_rate": metrics_b.conversion_rate
            },
            "traffic_split": test.traffic_split,
            "started_at": test.started_at.isoformat(),
            "completed_at": test.completed_at.isoformat() if test.completed_at else None
        }

    def list_tests(self) -> list[dict[str, str]]:
        return [
            {
                "test_id": test.test_id,
                "variant_a": test.prompt_a,
                "variant_b": test.prompt_b,
                "status": "completed" if test.completed_at else "active"
            }
            for test in self._ab_tests.values()
        ]

    def complete_test(self, test_id: str) -> None:
        if test_id in self._ab_tests:
            self._ab_tests[test_id].completed_at = datetime.now()

    def set_random_seed(self, seed: int) -> None:
        self._random_seed = seed
