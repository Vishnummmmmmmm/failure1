import httpx
from app.ingestors.base import PostSchema
from app.ingestors.seed_data import get_seed_posts
from app.core.config import get_settings

async def scrape_reddit(keywords: list[str], brand_name: str, max_results: int = 25) -> list[PostSchema]:
    settings = get_settings()
    if settings.DEMO_MODE:
        return [p for p in get_seed_posts(keywords, brand_name) if p.source == 'reddit']

    posts = []
    query = '+'.join(keywords[:2])

    # Strategy 1: PRAW OAuth (higher rate limit) — only if keys present
    if settings.REDDIT_CLIENT_ID and settings.REDDIT_CLIENT_SECRET:
        try:
            import praw
            reddit = praw.Reddit(
                client_id=settings.REDDIT_CLIENT_ID,
                client_secret=settings.REDDIT_CLIENT_SECRET,
                user_agent='PulseSphere/1.0 crisis-monitor'
            )
            for sub in reddit.subreddit('all').search(query, sort='new', time_filter='day', limit=max_results):
                text = sub.selftext or sub.title
                if text and len(text) > 20:
                    posts.append(PostSchema(
                        source='reddit',
                        content=f"{sub.title} {text}".strip()[:500],
                        author=f'u/{sub.author}' if sub.author else 'u/deleted',
                        url=f'https://reddit.com{sub.permalink}'
                    ))
            if posts: return posts[:max_results]
        except Exception as e:
            print(f'[Reddit PRAW] Error: {e} — falling back to public API')

    # Strategy 2: Public JSON API (no auth, 10 req/min)
    headers = {'User-Agent': 'PulseSphere/1.0 research bot'}
    endpoints = [
        f'https://www.reddit.com/search.json?q={query}&sort=new&limit=25&t=day',
        f'https://www.reddit.com/r/india/search.json?q={query}&sort=new&limit=15&restrict_sr=false',
    ]
    async with httpx.AsyncClient(headers=headers, timeout=15) as client:
        for url in endpoints:
            try:
                r = await client.get(url)
                data = r.json()
                for child in data.get('data', {}).get('children', []):
                    d = child['data']
                    text = d.get('selftext') or d.get('title', '')
                    if text and len(text) > 20:
                        posts.append(PostSchema(
                            source='reddit',
                            content=f"{d.get('title','')} {text}".strip()[:500],
                            author=f"u/{d.get('author','unknown')}",
                            url=f"https://reddit.com{d.get('permalink','')}"
                        ))
            except Exception as e:
                print(f'[Reddit public] Error on {url}: {e}')

    return posts[:max_results] if posts else get_seed_posts(keywords, brand_name)[:3]
