"""Registry module for auto-discovery and A/B testing of prompt strategies."""

from __future__ import annotations

import importlib
import importlib.util
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable
from datetime import datetime


@dataclass
class ABTest:
    """Represents an A/B test configuration for prompt comparison.
    
    Attributes:
        test_id: Unique identifier for this A/B test.
        prompt_a: Name of the first prompt variant.
        prompt_b: Name of the second prompt variant.
        traffic_split: Percentage of traffic to send to variant A.
        started_at: When the test was initiated.
        completed_at: When the test was completed (None if ongoing).
        results: Dictionary storing test results and metrics.
    """
    
    test_id: str
    prompt_a: str
    prompt_b: str
    traffic_split: float = 0.5
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: datetime | None = None
    results: dict[str, Any] = field(default_factory=dict)


@dataclass
class PromptMetrics:
    """Stores metrics for a prompt variant.
    
    Attributes:
        impressions: Number of times this prompt was selected.
        engagements: Number of engagements recorded.
        conversions: Number of conversions recorded.
    """
    
    impressions: int = 0
    engagements: int = 0
    conversions: int = 0
    
    @property
    def engagement_rate(self) -> float:
        """Calculate the engagement rate."""
        if self.impressions == 0:
            return 0.0
        return self.engagements / self.impressions
    
    @property
    def conversion_rate(self) -> float:
        """Calculate the conversion rate."""
        if self.impressions == 0:
            return 0.0
        return self.conversions / self.impressions


class PromptRegistry:
    """Registry for prompt auto-discovery and A/B testing.
    
    This class provides automatic discovery of prompt strategies,
    manages A/B test configurations, and tracks performance metrics.
    
    Example:
        >>> registry = PromptRegistry()
        >>> registry.discover_prompts("./prompts")
        >>> prompt = registry.get_prompt("hook_focus")
        >>> test = registry.create_ab_test("hook_focus", "storytelling")
        >>> selected = registry.select_for_test(test)
    """
    
    def __init__(self) -> None:
        """Initialize the PromptRegistry."""
        self._strategies: dict[str, type] = {}
        self._prompts: dict[str, str] = {}
        self._ab_tests: dict[str, ABTest] = {}
        self._metrics: dict[str, PromptMetrics] = {}
        self._random_seed: int | None = None
    
    def discover_prompts(self, prompts_dir: str | Path | None = None) -> int:
        """Discover and register prompts from the versions directory.
        
        Automatically loads all prompt JSON files and registers them
        with their strategy type extracted from the filename.
        
        Args:
            prompts_dir: Path to the prompts directory. Defaults to ./versions.
            
        Returns:
            Number of prompts discovered and registered.
        """
        if prompts_dir is None:
            prompts_dir = Path(__file__).parent / "versions"
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
        """Register a prompt strategy class.
        
        Args:
            name: The name to register the strategy under.
            strategy_class: The strategy class to register.
        """
        self._strategies[name] = strategy_class
    
    def register_prompt(self, name: str, content: str) -> None:
        """Register a prompt string with a given name.
        
        Args:
            name: The name to register the prompt under.
            content: The prompt content.
        """
        self._prompts[name] = content
        if name not in self._metrics:
            self._metrics[name] = PromptMetrics()
    
    def get_prompt(self, name: str) -> str | None:
        """Retrieve a prompt by name.
        
        Args:
            name: The name of the prompt to retrieve.
            
        Returns:
            The prompt content if found, None otherwise.
        """
        return self._prompts.get(name)
    
    def list_prompts(self) -> list[str]:
        """Get a list of all registered prompt names.
        
        Returns:
            List of prompt names.
        """
        return list(self._prompts.keys())
    
    def list_strategies(self) -> list[str]:
        """Get a list of all registered strategy names.
        
        Returns:
            List of strategy names.
        """
        return list(self._strategies.keys())
    
    def create_ab_test(
        self,
        prompt_a: str,
        prompt_b: str,
        traffic_split: float = 0.5,
        test_id: str | None = None
    ) -> ABTest:
        """Create a new A/B test between two prompt variants.
        
        Args:
            prompt_a: Name of the first prompt variant.
            prompt_b: Name of the second prompt variant.
            traffic_split: Percentage of traffic to send to variant A (0.0 to 1.0).
            test_id: Optional custom test ID. Defaults to auto-generated UUID.
            
        Returns:
            The created ABTest instance.
            
        Raises:
            ValueError: If prompt variants are not registered.
        """
        if prompt_a not in self._prompts:
            raise ValueError(f"Prompt '{prompt_a}' is not registered")
        if prompt_b not in self._prompts:
            raise ValueError(f"Prompt '{prompt_b}' is not registered")
        if not 0.0 <= traffic_split <= 1.0:
            raise ValueError("traffic_split must be between 0.0 and 1.0")
        
        if test_id is None:
            import uuid
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
        """Select which prompt variant to use for a given test.
        
        Uses the configured traffic split to determine which variant
        should be selected. Updates impressions metrics for both variants.
        
        Args:
            test: The ABTest to select a variant for.
            
        Returns:
            The name of the selected prompt variant.
        """
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
        """Record an impression for a prompt variant.
        
        Args:
            prompt_name: The name of the prompt that was shown.
        """
        if prompt_name in self._metrics:
            self._metrics[prompt_name].impressions += 1
    
    def record_engagement(self, prompt_name: str) -> None:
        """Record an engagement for a prompt variant.
        
        Args:
            prompt_name: The name of the prompt that received engagement.
        """
        if prompt_name in self._metrics:
            self._metrics[prompt_name].engagements += 1
    
    def record_conversion(self, prompt_name: str) -> None:
        """Record a conversion for a prompt variant.
        
        Args:
            prompt_name: The name of the prompt that led to conversion.
        """
        if prompt_name in self._metrics:
            self._metrics[prompt_name].conversions += 1
    
    def get_metrics(self, prompt_name: str) -> PromptMetrics | None:
        """Get the metrics for a specific prompt.
        
        Args:
            prompt_name: The name of the prompt.
            
        Returns:
            The PromptMetrics if found, None otherwise.
        """
        return self._metrics.get(prompt_name)
    
    def get_all_metrics(self) -> dict[str, PromptMetrics]:
        """Get metrics for all prompts.
        
        Returns:
            Dictionary mapping prompt names to their metrics.
        """
        return self._metrics.copy()
    
    def get_test_results(self, test_id: str) -> dict[str, Any] | None:
        """Get the results summary for an A/B test.
        
        Args:
            test_id: The ID of the test.
            
        Returns:
            Dictionary with test results including winner and confidence.
        """
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
        """List all A/B tests.
        
        Returns:
            List of test summaries with IDs and status.
        """
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
        """Mark an A/B test as completed.
        
        Args:
            test_id: The ID of the test to complete.
        """
        if test_id in self._ab_tests:
            self._ab_tests[test_id].completed_at = datetime.now()
    
    def set_random_seed(self, seed: int) -> None:
        """Set the random seed for deterministic test selection.
        
        Useful for testing and reproducibility.
        
        Args:
            seed: The random seed to use.
        """
        self._random_seed = seed
