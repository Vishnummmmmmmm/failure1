from app.ingestors.base import PostSchema
from datetime import datetime

ZOMATO_CRISIS_SEED = [
  PostSchema(source='twitter', content='Zomato delivery guy crashed my order AND was rude. Never using this app again. #ZomatoFail', author='@angry_user1', url=''),
  PostSchema(source='reddit', content='Has anyone else noticed Zomato prices jumped 40% overnight? This is straight up price gouging during a holiday.', author='u/bangalore_foodie', url=''),
  PostSchema(source='google', content='Zomato customer support is completely useless. Been waiting 3 hours for a refund. Absolute disaster.', author='Google Review', url=''),
  PostSchema(source='threads', content='Zomato overcharged me AGAIN. Third time this month. Disgusting business practice.', author='@threads_user9', url=''),
  PostSchema(source='instagram', content='Just found out Zomato has been collecting my location data even when app is closed. Privacy nightmare. #DataBreach', author='@foodblogger22', url=''),
  PostSchema(source='facebook', content='Zomato delivered WRONG food for my diabetic father. This could have been dangerous. Filing a consumer complaint.', author='Priya Sharma', url=''),
  PostSchema(source='twitter', content='Zomato app keeps crashing mid-order and charges my card anyway. Three failed transactions today.', author='@techfrustratedguy', url=''),
  PostSchema(source='reddit', content='Massive thread: Zomato secretly increased platform fees from 5% to 18% for restaurants. Multiple restaurant owners confirming.', author='u/restaurant_owner_blr', url=''),
  PostSchema(source='google', content='Food arrived 2 hours late, stone cold, wrong items. Zomato refused refund. This company has zero accountability.', author='Rahul M', url=''),
  PostSchema(source='twitter', content='I HATE ZOMATO. They ruined my anniversary dinner. Customer care just copy-pastes responses. FURIOUS. #BoycottZomato', author='@upset_customer88', url=''),
  PostSchema(source='threads', content='Zomato Gold membership is a scam. Benefits keep getting removed silently. Cancelled immediately.', author='@threads_foodie', url=''),
  PostSchema(source='instagram', content='Multiple delivery partners on strike outside Zomato HQ Bangalore right now. This is getting serious.', author='@bnews_live', url=''),
  PostSchema(source='facebook', content='Zomato charged me twice for a cancelled order. Bank confirms double debit. This is fraud.', author='Ankit Verma', url=''),
  PostSchema(source='twitter', content='Just saw Zomato CEO interview where he laughed off delivery partner complaints. Absolutely tone-deaf. Uninstalling.', author='@social_watchdog', url=''),
  PostSchema(source='reddit', content='Breaking: Food Safety dept reportedly investigating Zomato cloud kitchen hygiene standards in Mumbai.', author='u/food_safety_news', url=''),
  PostSchema(source='google', content='Worst food delivery experience ever. Wrong restaurant, wrong food, no refund. Zomato is in complete chaos.', author='Sneha K', url=''),
  PostSchema(source='twitter', content='My Zomato order showed delivered but never arrived. GPS shows rider never came near my building. Clear fraud.', author='@bengaluru_eats', url=''),
  PostSchema(source='threads', content='Zomato just emailed saying they lost my payment data in a breach. How is this not bigger news??', author='@privacy_hawk', url=''),
  PostSchema(source='facebook', content='Sharing because everyone should know: Zomato has been fined by consumer court. Details in comments.', author='Consumer Rights India', url=''),
  PostSchema(source='reddit', content='CVI is going to explode today. Zomato trending on every platform simultaneously. Classic crisis spiral.', author='u/pr_crisis_watcher', url='')
]

def get_seed_posts(keywords: list[str], brand_name: str) -> list:
    """Returns seed posts filtered/adapted to brand keywords."""
    posts = []
    for p in ZOMATO_CRISIS_SEED:
        adapted = PostSchema(
            source=p.source,
            content=p.content.replace('Zomato', brand_name).replace('zomato', brand_name.lower()),
            author=p.author,
            url=p.url
        )
        posts.append(adapted)
    return posts
