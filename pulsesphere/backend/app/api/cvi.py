from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.ingestors.orchestrator import ingest_all
from app.ml.inference import run_inference_batch
from app.services.cvi_engine import compute_cvi, save_cvi_snapshot
from app.services.pre_echo import detect_pre_echo, get_recent_cvi_series
from app.services.alert_engine import evaluate_and_fire_alert
from app.core.db import get_db

router = APIRouter()

@router.get('/')
async def get_cvi(brand_id: str):
    """
    Full pipeline: scrape → infer → CVI → pre-echo → alert
    TC03: returns score float 0-100 + level string
    TC10: 50 high-neg posts → CVI > 75 within this call
    """
    db = get_db()

    # Get brand keywords
    brand = db.table('brands').select('*').eq('id', brand_id).single().execute()
    if not brand.data:
        raise HTTPException(404, 'Brand not found')

    keywords   = brand.data['keywords']
    brand_name = brand.data['name']

    # Step 1: Ingest
    posts = await ingest_all(keywords, brand_name)
    if not posts:
        raise HTTPException(422, 'No posts found')

    # Step 2: ML Inference on all posts
    enrichments = run_inference_batch(posts)

    # Step 3: Merge posts + enrichments
    merged = []
    for i, post in enumerate(posts):
        merged.append({
            **post.dict(),
            **enrichments[i]
        })

    # Step 4: CVI formula
    snapshot = compute_cvi(merged, brand_id)

    # Step 5: Pre-echo detection
    series = await get_recent_cvi_series(brand_id, limit=60)
    series.append(snapshot['score'])
    echo   = detect_pre_echo(series)
    snapshot['is_anomaly']    = echo['is_anomaly']
    snapshot['minutes_early'] = echo['minutes_early']

    # Step 6: Save snapshot
    await save_cvi_snapshot(snapshot, is_anomaly=echo['is_anomaly'])

    # Step 7: Fire alert if threshold crossed
    alert = await evaluate_and_fire_alert(brand_id, snapshot['score'])

    # Step 8: Save enriched posts to DB
    rows = [{
        'brand_id':        brand_id,
        'source':          p['source'],
        'content':         p['content'],
        'author':          p['author'],
        'emotion_scores':  p['emotion_scores'],
        'is_fake_news':    p['is_fake_news'],
        'is_bot_generated':p['is_bot_generated'],
        'crisis_category': p['crisis_category'],
        'cvi_contribution':p['neg_score'],
    } for p in merged]
    db.table('posts').insert(rows).execute()

    return {
        **snapshot,
        'alert':      alert,
        'pre_echo':   echo,
        'post_count': len(posts),
        'sources':    list(set(p['source'] for p in merged))
    }

@router.get('/latest')
async def get_latest_cvi(brand_id: str):
    """Returns most recent stored CVI snapshot — for frontend realtime gauge polling"""
    db = get_db()
    r  = db.table('cvi_snapshots')\
        .select('*')\
        .eq('brand_id', brand_id)\
        .order('recorded_at', desc=True)\
        .limit(1)\
        .execute()
    if not r.data: raise HTTPException(404, 'No snapshots yet — call /cvi first')
    return r.data[0]

@router.get('/history')
async def get_cvi_history(brand_id: str, limit: int = 30):
    """Returns last N CVI snapshots for timeline chart (Recharts)"""
    db = get_db()
    r  = db.table('cvi_snapshots')\
        .select('score, level, is_anomaly, recorded_at')\
        .eq('brand_id', brand_id)\
        .order('recorded_at', desc=True)\
        .limit(limit)\
        .execute()
    return list(reversed(r.data))

class EmotionTestRequest(BaseModel):
    text: str

@router.post('/test-emotion')
def test_emotion(payload: EmotionTestRequest):
    """TC04 helper — direct emotion inference on single text"""
    from app.ml.inference import run_inference_batch
    from app.ingestors.base import PostSchema
    result = run_inference_batch([PostSchema(source='test', content=payload.text)])
    return {
        'emotion_scores':  result[0]['emotion_scores'],
        'is_fake_news':    result[0]['is_fake_news'],
        'is_bot_generated':result[0]['is_bot_generated'],
        'crisis_category': result[0]['crisis_category'],
        'neg_score':       result[0]['neg_score']
    }
