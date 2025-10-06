import requests
import os
import sys
from dotenv import load_dotenv
from src.logger import get_logger
from src.custom_exception import CustomException

load_dotenv()
logger = get_logger(__name__)

# -----------------------------------------------------------------------------
# 🔍 1. Tavily Search Summary
# -----------------------------------------------------------------------------
def tavily_search_summary(query: str, max_results: int = 3) -> str:
    """
    Use Tavily Search API to get factual web summaries for a given query.
    Returns a clean, readable string combining top results.
    """
    try:
        logger.info(f"🔎 Tavily Search for query: {query}")

        TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
        if not TAVILY_API_KEY:
            raise CustomException("TAVILY_API_KEY missing from environment variables", None)

        url = "https://api.tavily.com/search"
        headers = {"Content-Type": "application/json"}
        payload = {
            "api_key": TAVILY_API_KEY,
            "query": query,
            "max_results": max_results
        }

        resp = requests.post(url, json=payload, headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        results = data.get("results", [])
        if not results:
            return f"No results found for '{query}'."

        output_lines = []
        for i, item in enumerate(results[:max_results], start=1):
            title = item.get("title", "Untitled")
            content = item.get("content", "")
            url_link = item.get("url", "")
            output_lines.append(f"{i}. **{title}**\n{content}\n🔗 {url_link}")

        summary = "\n\n".join(output_lines)
        logger.info("✅ Tavily Search completed successfully.")
        return summary

    except Exception as e:
        logger.error(f"Tavily search error for '{query}': {e}")
        raise CustomException(f"Tavily search error for query '{query}'", e)


# -----------------------------------------------------------------------------
# 💻 2. GitHub Code Search
# -----------------------------------------------------------------------------
def search_github_code(query: str, language: str = "python", per_page: int = 3) -> str:
    """
    Search GitHub for code snippets matching a query.
    Returns top results with repo + file path.
    """
    try:
        logger.info(f"Searching GitHub code for query: {query}")

        GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
        headers = {"Accept": "application/vnd.github.v3+json"}
        if GITHUB_TOKEN:
            headers["Authorization"] = f"token {GITHUB_TOKEN}"

        url = "https://api.github.com/search/code"
        params = {"q": f"{query} language:{language}", "per_page": per_page}

        resp = requests.get(url, headers=headers, params=params, timeout=10)
        resp.raise_for_status()
        results = resp.json().get("items", [])

        if not results:
            return f"No code found for query '{query}'."

        output_lines = []
        for item in results:
            repo = item["repository"]["full_name"]
            path = item["path"]
            html_url = item["html_url"]
            output_lines.append(f"📂 {repo}/{path}\n🔗 {html_url}")

        logger.info("✅ GitHub code search completed successfully.")
        return "\n\n".join(output_lines)

    except Exception as e:
        logger.error(f"GitHub code search error for '{query}': {e}")
        raise CustomException(f"GitHub code search error for query '{query}'", e)


# -----------------------------------------------------------------------------
# 🌦️ 3. Weather Info
# -----------------------------------------------------------------------------
def get_weather(lat: float, lon: float) -> str:
    """Fetch current weather from Open-Meteo API."""
    try:
        logger.info(f"Fetching weather for lat={lat}, lon={lon}")
        url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={lat}&longitude={lon}&current_weather=true"
        )
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()

        data = resp.json().get("current_weather")
        if not data:
            return "Weather data not available."

        temp = data.get("temperature")
        wind = data.get("windspeed")
        return f"Temperature: {temp}°C, Windspeed: {wind} km/h"

    except Exception as e:
        logger.error(f"Weather fetch error at lat={lat}, lon={lon}: {e}")
        raise CustomException(f"Weather fetch error for lat={lat}, lon={lon}", sys)
