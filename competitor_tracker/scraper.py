"""LinkedIn scraper with rate limiting and error handling."""

import time
import random
import re
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class RateLimiter:
    min_delay: float = 3.0
    max_delay: float = 7.0
    max_retries: int = 3
    retry_delay: float = 60.0

    def __post_init__(self):
        self.last_request_time = 0.0
        self.retry_count = 0

    def wait(self) -> None:
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_delay:
            sleep_time = self.min_delay - elapsed + random.uniform(0, self.max_delay - self.min_delay)
            logger.info(f"Rate limiting: sleeping {sleep_time:.1f}s")
            time.sleep(sleep_time)
        self.last_request_time = time.time()

    def record_retry(self) -> bool:
        self.retry_count += 1
        if self.retry_count >= self.max_retries:
            self.retry_count = 0
            return False
        delay = self.retry_delay * self.retry_count
        logger.warning(f"Retry attempt {self.retry_count}/{self.max_retries}, waiting {delay:.1f}s")
        time.sleep(delay)
        return True


class LinkedInScraper:
    BASE_URL = "https://www.linkedin.com"
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    ]

    def __init__(self, session_cookie: str = None, proxy: str = None):
        self.session_cookie = session_cookie
        self.proxy = proxy
        self.rate_limiter = RateLimiter()
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": random.choice(self.USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        })
        if session_cookie:
            self.session.cookies.set("li_at", session_cookie)
        if proxy:
            self.session.proxies = {"http": proxy, "https": proxy}

    def _make_request(self, url: str, timeout: int = 10) -> requests.Response:
        self.rate_limiter.wait()
        
        for attempt in range(self.rate_limiter.max_retries):
            try:
                response = self.session.get(url, timeout=timeout)
                
                if response.status_code == 429:
                    logger.warning("Rate limited (429), backing off")
                    time.sleep(self.rate_limiter.retry_delay * 2)
                    continue
                
                if response.status_code == 403:
                    raise PermissionError(f"Access forbidden (403): {url}")
                
                if response.status_code == 999:
                    logger.warning("LinkedIn security block (999)")
                    if not self.rate_limiter.record_retry():
                        raise RuntimeError("LinkedIn security block: too many retries")
                    continue
                
                if response.status_code == 999:
                    raise ConnectionRefusedError(f"Connection rejected (999): {url}")
                
                return response
                
            except requests.exceptions.Timeout:
                logger.warning(f"Timeout for {url}")
                if not self.rate_limiter.record_retry():
                    raise
            except requests.exceptions.RequestException as e:
                logger.error(f"Request error: {e}")
                if not self.rate_limiter.record_retry():
                    raise RuntimeError(f"Request failed: {e}")
        
        raise RuntimeError(f"Failed after {self.rate_limiter.max_retries} retries")

    def get_profile(self, profile_url: str) -> dict[str, Any]:
        url = profile_url if profile_url.startswith("http") else f"{self.BASE_URL}/in/{profile_url}/"
        
        try:
            response = self._make_request(url)
            soup = BeautifulSoup(response.text, "html.parser")
            
            name_elem = soup.select_one(".top-card-layout__title, .profile-top-card__title")
            headline_elem = soup.select_one(".top-card-layout__headline, .profile-top-card__headline")
            followers_elem = soup.select_one(".top-card-layout__current-location, .profile-top-card__follower-count")
            
            followers_text = followers_elem.get_text() if followers_elem else "0"
            followers = self._parse_number(followers_text)
            
            return {
                "name": name_elem.get_text(strip=True) if name_elem else "Unknown",
                "headline": headline_elem.get_text(strip=True) if headline_elem else "",
                "followers": followers,
                "url": url,
            }
        except Exception as e:
            logger.error(f"Profile fetch error: {e}")
            return {"name": "Unknown", "headline": "", "followers": 0, "url": url, "error": str(e)}

    def get_posts(self, profile_url: str, limit: int = 10) -> list[dict[str, Any]]:
        url = profile_url if profile_url.startswith("http") else f"{self.BASE_URL}/in/{profile_url}/"
        
        try:
            response = self._make_request(url)
            soup = BeautifulSoup(response.text, "html.parser")
            
            posts = []
            post_containers = soup.select(".feed-shared-update-v2, .occludable-update")
            
            for container in post_containers[:limit]:
                try:
                    post_data = self._extract_post(container)
                    if post_data:
                        posts.append(post_data)
                except Exception as e:
                    logger.warning(f"Post extraction error: {e}")
                    continue
            
            if not posts:
                logger.info("No posts found via HTML parsing, attempting fallback")
                posts = self._extract_from_js(response.text, limit)
            
            return posts
            
        except Exception as e:
            logger.error(f"Posts fetch error: {e}")
            return []

    def _extract_post(self, container: BeautifulSoup) -> dict[str, Any]:
        content_elem = container.select_one(".feed-shared-text, .update-components-text")
        hook_elem = container.select_one("span[aria-level='2'], .feed-shared-heading")
        
        content = ""
        if content_elem:
            content = content_elem.get_text(strip=True)
        elif hook_elem:
            content = hook_elem.get_text(strip=True)
        
        if not content:
            return None
        
        hook = content[:150] if len(content) > 150 else content
        
        text_elem = container.select_one(".feed-shared-update-v2__description, .update-components-text")
        post_content = text_elem.get_text(strip=True) if text_elem else content
        
        stats = container.select_one(".social-details-social-activity, .feed-shared-social-counts")
        likes = comments = shares = 0
        
        if stats:
            like_elem = stats.select_one(".social-details-social-activity__likes, .feed-shared-likes")
            comment_elem = stats.select_one(".social-details-social-activity__comments, .feed-shared-comments")
            
            if like_elem:
                likes = self._parse_number(like_elem.get_text(strip=True))
            if comment_elem:
                comments = self._parse_number(comment_elem.get_text(strip=True))
        
        return {
            "post_id": container.get("data-id", ""),
            "content": post_content,
            "hook": hook,
            "likes": likes,
            "comments": comments,
            "shares": shares,
            "posted_at": datetime.now().isoformat(),
            "url": "",
        }

    def _extract_from_js(self, html: str, limit: int) -> list[dict[str, Any]]:
        posts = []
        data_pattern = r'"postUrn":"([^"]+)".*?"text":"([^"]*?)"'
        
        matches = re.findall(data_pattern, html)
        for i, (post_id, text) in enumerate(matches[:limit]):
            text = text.replace("\\u0026", "&").replace("\\n", "\n").strip()
            if text and len(text) > 20:
                posts.append({
                    "post_id": post_id,
                    "content": text,
                    "hook": text[:150],
                    "likes": 0,
                    "comments": 0,
                    "shares": 0,
                    "posted_at": "",
                    "url": "",
                })
        
        return posts

    def _parse_number(self, text: str) -> int:
        text = text.strip()
        multipliers = {"K": 1000, "M": 1000000, "B": 1000000000}
        
        for suffix, mult in multipliers.items():
            if suffix in text:
                try:
                    return int(float(text.replace(suffix, "").strip()) * mult)
                except ValueError:
                    return 0
        
        try:
            return int(text.replace(",", "").replace(" ", ""))
        except ValueError:
            return 0


class MockLinkedInScraper(LinkedInScraper):
    """Mock scraper for demo/testing when LinkedIn is blocked."""

    SAMPLE_POSTS = [
        {"hook": "I just turned down a $300K salary. Here's why...", "topic": "Career", "tone": "Bold", "likes": 2500},
        {"hook": "The biggest mistake I made in my 20s", "topic": "Personal Growth", "tone": "Vulnerable", "likes": 3200},
        {"hook": "3 lessons from hiring 100 people", "topic": "Leadership", "tone": "Educational", "likes": 1800},
        {"hook": "Why I fired my best friend", "topic": "Leadership", "tone": "Honest", "likes": 4500},
        {"hook": "My $50K mistake", "topic": "Entrepreneurship", "tone": "Storytelling", "likes": 2100},
        {"hook": "The truth about startup life", "topic": "Startups", "tone": "Raw", "likes": 2800},
        {"hook": "How I lost $1M in 6 months", "topic": "Failure", "tone": "Vulnerable", "likes": 5100},
        {"hook": "5 habits that changed my career", "topic": "Productivity", "tone": "Actionable", "likes": 1500},
        {"hook": "I招聘错了人. Here's what I learned", "topic": "Hiring", "tone": "Learning", "likes": 1900},
        {"hook": "Why remote work is here to stay", "topic": "Future of Work", "tone": "Opinion", "likes": 2200},
    ]

    def __init__(self, session_cookie: str = None, proxy: str = None):
        super().__init__(session_cookie, proxy)

    def get_profile(self, profile_url: str) -> dict[str, Any]:
        time.sleep(0.5)
        name = profile_url.split("/in/")[-1].rstrip("/").replace("-", " ").title()
        return {
            "name": name,
            "headline": "Industry Leader",
            "followers": random.randint(5000, 100000),
            "url": profile_url,
        }

    def get_posts(self, profile_url: str, limit: int = 10) -> list[dict[str, Any]]:
        time.sleep(1)
        
        num_posts = min(limit, len(self.SAMPLE_POSTS))
        selected = random.sample(self.SAMPLE_POSTS, num_posts)
        
        posts = []
        for i, sample in enumerate(selected):
            posts.append({
                "post_id": f"post_{i}_{int(time.time())}",
                "content": sample["hook"] + " This is the full post content with valuable insights and storytelling...",
                "hook": sample["hook"],
                "likes": sample["likes"] + random.randint(-200, 500),
                "comments": random.randint(20, 150),
                "shares": random.randint(10, 80),
                "posted_at": f"2024-{(i%12)+1:02d}-{(i%28)+1:02d}T10:00:00Z",
                "url": f"{profile_url}/feed/{i}",
            })
        
        return posts