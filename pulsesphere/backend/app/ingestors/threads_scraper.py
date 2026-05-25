import httpx
from app.ingestors.base import PostSchema
from app.ingestors.seed_data import get_seed_posts
from app.core.config import get_settings
from fake_useragent import UserAgent

ua = UserAgent()

async def scrape_threads(keywords: list[str], brand_name: str, max_results: int = 20) -> list[PostSchema]:
    settings = get_settings()
    if settings.DEMO_MODE:
        return [p for p in get_seed_posts(keywords, brand_name) if p.source == 'threads']

    posts = []
    query = ' '.join(keywords[:2])
    headers = {
        'User-Agent': ua.random,
        'Accept': 'text/html,application/xhtml+xml',
        'Accept-Language': 'en-US,en;q=0.9',
    }

    # Threads search endpoint (unauthenticated public search)
    try:
        async with httpx.AsyncClient(headers=headers, timeout=15, follow_redirects=True) as client:
            r = await client.get(f'https://www.threads.net/search?q={query}&serp_type=default')
            # Parse JSON from embedded __SSR_DATA__ script tag
            if '"text_post_app_thread"' in r.text:
                import re, json
                matches = re.findall(r'"caption":\{"text":"([^"]{20,400})"', r.text)
                for text in matches[:max_results]:
                    posts.append(PostSchema(
                        source='threads',
                        content=text,
                        author='@threads_user',
                        url='https://threads.net'
                    ))
    except Exception as e:
        print(f'[Threads scraper] Error: {e}. Using seed fallback.')

    return posts[:max_results] if posts else get_seed_posts(keywords, brand_name)[:2]
