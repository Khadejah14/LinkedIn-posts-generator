"""Main competitor tracker module for LinkedIn post tracking."""

import json
import logging
from pathlib import Path
from typing import Any

from openai import OpenAI
import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


from .database import (
    init_db,
    add_competitor,
    get_competitors,
    delete_competitor,
    add_post,
    get_posts,
    get_top_posts,
    add_analysis as db_add_analysis,
    get_all_analysis,
    add_scrape_log,
    get_scrape_logs,
    get_stats,
    get_trends,
    update_trends,
    add_user_topic as db_add_user_topic,
    get_user_topics,
)
from .scraper import LinkedInScraper, MockLinkedInScraper
from .analyzer import PostAnalyzer, HookGenerator
from .gap_analyzer import GapAnalyzer, Gap


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CompetitorTracker:
    DEFAULT_COMPETITORS = [
        {"name": "John Morgan", "profile_url": "https://www.linkedin.com/in/johnmorgan/"},
        {"name": "Sarah Chen", "profile_url": "https://www.linkedin.com/in/sarahchen/"},
        {"name": "Mike Chen", "profile_url": "https://www.linkedin.com/in/mikecode/"},
    ]

    def __init__(self, use_mock: bool = True):
        init_db()
        
        self.use_mock = use_mock
        if use_mock:
            self.scraper = MockLinkedInScraper()
        else:
            session_cookie = os.getenv("LINKEDIN_COOKIE")
            proxy = os.getenv("PROXY")
            self.scraper = LinkedInScraper(session_cookie, proxy)
        
        self.analyzer = PostAnalyzer()
        self.hook_generator = HookGenerator()
        self.gap_analyzer = GapAnalyzer()

    def add_competitor(self, name: str, profile_url: str, industry: str = None) -> int:
        competitor_id = add_competitor(name, profile_url, industry)
        logger.info(f"Added competitor: {name} (ID: {competitor_id})")
        return competitor_id

    def remove_competitor(self, competitor_id: int) -> None:
        delete_competitor(competitor_id)
        logger.info(f"Removed competitor ID: {competitor_id}")

    def scrape_competitor(self, competitor_id: int, limit: int = 10) -> dict[str, Any]:
        competitors = get_competitors()
        competitor = next((c for c in competitors if c["id"] == competitor_id), None)
        
        if not competitor:
            return {"error": "Competitor not found", "posts_fetched": 0}
        
        try:
            profile_url = competitor["profile_url"]
            profile_data = self.scraper.get_profile(profile_url)
            
            logger.info(f"Scraping posts from {competitor['name']}...")
            posts_data = self.scraper.get_posts(profile_url, limit)
            
            posts_stored = 0
            for post_data in posts_data:
                post_id = add_post(competitor_id, post_data)
                posts_stored += 1
                
                try:
                    analysis = self.analyzer.analyze_post(post_data.get("content", ""))
                    db_add_analysis(post_id, analysis.to_dict())
                except Exception as e:
                    logger.warning(f"Analysis failed: {e}")
            
            add_scrape_log(competitor_id, "success", posts_fetched=posts_stored)
            logger.info(f"Stored {posts_stored} posts for {competitor['name']}")
            
            return {
                "competitor": competitor["name"],
                "posts_fetched": posts_stored,
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"Scrape error: {e}")
            add_scrape_log(competitor_id, "error", str(e))
            return {"error": str(e), "posts_fetched": 0}

    def scrape_all_competitors(self, limit: int = 10) -> dict[str, Any]:
        competitors = get_competitors()
        results = {"success": 0, "failed": 0, "total_posts": 0, "details": []}
        
        for competitor in competitors:
            result = self.scrape_competitor(competitor["id"], limit)
            results["details"].append(result)
            
            if result.get("posts_fetched", 0) > 0:
                results["success"] += 1
                results["total_posts"] += result["posts_fetched"]
            else:
                results["failed"] += 1
        
        all_analysis = get_all_analysis()
        update_trends(all_analysis)
        
        return results

    def get_competitors_data(self) -> list[dict[str, Any]]:
        competitors = get_competitors()
        stats = get_stats()
        
        competitor_stats = {c["name"]: c for c in stats.get("competitor_stats", [])}
        
        for comp in competitors:
            comp.update(competitor_stats.get(comp["name"], {}))
        
        return competitors

    def get_posts_data(self, competitor_id: int = None, limit: int = 100) -> list[dict[str, Any]]:
        return get_posts(competitor_id, limit)

    def get_top_posts_data(self, limit: int = 10) -> list[dict[str, Any]]:
        return get_top_posts(limit)

    def get_analysis_data(self, competitor_id: int = None) -> list[dict[str, Any]]:
        return get_all_analysis(competitor_id)

    def get_gap_analysis(self, user_topics: list[str], user_hooks: list[str] = None) -> list[Gap]:
        analysis = get_all_analysis()
        return self.gap_analyzer.analyze_gaps(analysis, user_topics, user_hooks)

    def get_trend_insights(self) -> dict[str, Any]:
        analysis = get_all_analysis()
        return self.gap_analyzer.get_trend_insights(analysis)

    def generate_hook_variation(self, hook: str, tone: str = "Bold", user_hooks: list[str] = None) -> list[dict[str, str]]:
        if user_hooks:
            return [self.hook_generator.adapt_to_voice(hook, user_hooks)]
        return self.hook_generator.generate_variations(hook, tone)

    def get_stats(self) -> dict[str, Any]:
        return get_stats()

    def set_user_topics(self, topics: list[str]) -> None:
        for topic in topics:
            db_add_user_topic(topic)

    def get_user_topics_data(self) -> list[dict[str, Any]]:
        return get_user_topics()

    def get_scrape_logs_data(self, limit: int = 20) -> list[dict[str, Any]]:
        return get_scrape_logs(limit)

    def get_trends_data(self) -> list[dict[str, Any]]:
        return get_trends()