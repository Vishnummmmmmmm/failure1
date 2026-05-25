from app.ingestors.base import PostSchema
from app.ingestors.seed_data import get_seed_posts
from app.core.config import get_settings

async def scrape_instagram(keywords: list[str], brand_name: str, max_results: int = 15) -> list[PostSchema]:
    settings = get_settings()
    if settings.DEMO_MODE:
        return [p for p in get_seed_posts(keywords, brand_name) if p.source == 'instagram']

    posts = []
    tag = keywords[0].replace(' ', '').lower()

    try:
        from playwright.async_api import async_playwright
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.set_extra_http_headers({'Accept-Language': 'en-US,en;q=0.9'})
            await page.goto(f'https://www.instagram.com/explore/tags/{tag}/', timeout=20000)
            await page.wait_for_timeout(3000)

            # Extract alt text from post images (public metadata)
            elements = await page.query_selector_all('article img')
            for el in elements[:max_results]:
                alt = await el.get_attribute('alt')
                if alt and len(alt) > 30:
                    posts.append(PostSchema(
                        source='instagram',
                        content=alt[:400],
                        author='@instagram_user',
                        url=f'https://instagram.com/explore/tags/{tag}'
                    ))
            await browser.close()
    except Exception as e:
        print(f'[Instagram scraper] Error: {e}. Using seed fallback.')

    return posts[:max_results] if posts else get_seed_posts(keywords, brand_name)[:2]
