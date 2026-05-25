from app.ingestors.base import PostSchema
from app.ingestors.seed_data import get_seed_posts
from app.core.config import get_settings

async def scrape_facebook(keywords: list[str], brand_name: str, max_results: int = 15) -> list[PostSchema]:
    settings = get_settings()
    if settings.DEMO_MODE:
        return [p for p in get_seed_posts(keywords, brand_name) if p.source == 'facebook']

    posts = []
    brand_slug = brand_name.lower().replace(' ', '')

    try:
        from playwright.async_api import async_playwright
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            # Facebook public search (no login for public posts)
            search_query = '+'.join(keywords[:2])
            await page.goto(f'https://www.facebook.com/public/{brand_slug}', timeout=20000)
            await page.wait_for_timeout(3000)
            elements = await page.query_selector_all('div[data-ad-preview="message"], div.kvgmc6g5')
            for el in elements[:max_results]:
                text = await el.inner_text()
                if text and len(text) > 30:
                    posts.append(PostSchema(
                        source='facebook',
                        content=text[:500],
                        author='Facebook User',
                        url=f'https://facebook.com/{brand_slug}'
                    ))
            await browser.close()
    except Exception as e:
        print(f'[Facebook scraper] Error: {e}. Using seed fallback.')

    return posts[:max_results] if posts else get_seed_posts(keywords, brand_name)[:2]
