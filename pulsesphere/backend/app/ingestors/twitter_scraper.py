import httpx
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from app.ingestors.base import PostSchema
from app.ingestors.seed_data import get_seed_posts
from app.core.config import get_settings

NITTER_MIRRORS = [
    'https://nitter.privacydev.net',
    'https://nitter.poast.org',
    'https://nitter.1d4.us',
]
ua = UserAgent()

async def scrape_twitter(keywords: list[str], brand_name: str, max_results: int = 30) -> list[PostSchema]:
    settings = get_settings()
    if settings.DEMO_MODE:
        return [p for p in get_seed_posts(keywords, brand_name) if p.source == 'twitter']

    query = '+'.join(keywords[:2]).replace(' ', '+') + '+complaint+OR+angry+OR+scam'
    posts = []

    for mirror in NITTER_MIRRORS:
        if posts: break
        try:
            headers = {'User-Agent': ua.random}
            async with httpx.AsyncClient(headers=headers, timeout=12, follow_redirects=True) as client:
                r = await client.get(f'{mirror}/search?f=tweets&q={query}')
                if r.status_code != 200: continue
                soup = BeautifulSoup(r.text, 'html.parser')
                for tweet_div in soup.select('div.tweet-content.media-body')[:max_results]:
                    text = tweet_div.get_text(strip=True)
                    author_tag = tweet_div.find_previous('a', class_='username')
                    author = author_tag.get_text(strip=True) if author_tag else '@unknown'
                    if len(text) > 20:
                        posts.append(PostSchema(
                            source='twitter',
                            content=text[:500],
                            author=author,
                            url=mirror
                        ))
        except Exception as e:
            print(f'[Twitter/Nitter] Mirror {mirror} failed: {e}')
            continue

    return posts[:max_results] if posts else get_seed_posts(keywords, brand_name)[:4]
