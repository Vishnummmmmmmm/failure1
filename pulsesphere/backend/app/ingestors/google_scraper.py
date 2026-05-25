import httpx
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from app.ingestors.base import PostSchema
from app.core.config import get_settings
from app.ingestors.seed_data import get_seed_posts
import asyncio

ua = UserAgent()

async def scrape_google(keywords: list[str], brand_name: str, max_results: int = 20) -> list[PostSchema]:
    settings = get_settings()
    if settings.DEMO_MODE:
        return [p for p in get_seed_posts(keywords, brand_name) if p.source == 'google']

    query = ' OR '.join(f'"{k}"' for k in keywords[:3]) + ' complaint OR crisis OR issue'
    posts = []

    # --- Strategy 1: Google Custom Search API (if keys present) ---
    if settings.GOOGLE_CSE_API_KEY and settings.GOOGLE_CSE_ID:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.get(
                    'https://www.googleapis.com/customsearch/v1',
                    params={'key': settings.GOOGLE_CSE_API_KEY, 'cx': settings.GOOGLE_CSE_ID, 'q': query, 'num': 10}
                )
                for item in r.json().get('items', []):
                    posts.append(PostSchema(
                        source='google',
                        content=item.get('snippet', ''),
                        author='Google Result',
                        url=item.get('link', '')
                    ))
            if posts: return posts[:max_results]
        except Exception:
            pass  # fall through to scrape

    # --- Strategy 2: Direct scrape ---
    headers = {'User-Agent': ua.random, 'Accept-Language': 'en-US,en;q=0.9'}
    try:
        async with httpx.AsyncClient(headers=headers, timeout=15, follow_redirects=True) as client:
            r = await client.get(f'https://www.google.com/search?q={query}&num=20&hl=en')
            soup = BeautifulSoup(r.text, 'html.parser')
            for div in soup.select('div.BNeawe.s3v9rd.AP7Wnd')[:max_results]:
                text = div.get_text(strip=True)
                if len(text) > 40:
                    posts.append(PostSchema(source='google', content=text, author='Google Result', url=''))
    except Exception as e:
        print(f'[Google scraper] Error: {e}')

    return posts[:max_results] if posts else get_seed_posts(keywords, brand_name)[:3]
