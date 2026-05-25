from fastapi import APIRouter, HTTPException
from app.core.db import get_db
from app.ingestors.orchestrator import ingest_all
from app.ml.inference import run_inference_batch
from app.services.cvi_engine import compute_cvi, save_cvi_snapshot
from app.services.alert_engine import evaluate_and_fire_alert
import asyncio

router = APIRouter()

async def _get_cvi_for_brand(brand: dict) -> dict:
    """Run full pipeline for one brand. Returns CVI snapshot dict."""
    brand_id = brand['id']
    keywords = brand['keywords']
    brand_name = brand['name']

    try:
        posts = await ingest_all(keywords, brand_name)
        if not posts:
            return {'brand_id': brand_id, 'brand_name': brand_name, 'score': 0, 'level': 'LOW', 'error': 'no_posts'}

        enrichments = run_inference_batch(posts)
        merged = [{**p.dict(), **enrichments[i]} for i, p in enumerate(posts)]
        snapshot = compute_cvi(merged, brand_id)
        snapshot['brand_name'] = brand_name
        snapshot['post_count'] = len(posts)
        snapshot['sources'] = list(set(p['source'] for p in merged))

        await save_cvi_snapshot(snapshot)
        alert = await evaluate_and_fire_alert(brand_id, snapshot['score'])
        snapshot['alert'] = alert
        return snapshot
    except Exception as e:
        return {'brand_id': brand_id, 'brand_name': brand_name, 'score': 0, 'level': 'LOW', 'error': str(e)}

@router.get('/')
async def get_competitor_panel(brand_ids: str):
    """
    TC16: Pass comma-separated brand_ids. Returns all CVIs in parallel.
    Example: GET /competitor/?brand_ids=uuid1,uuid2,uuid3
    Pass condition: list of 3 dicts each with score + level + brand_name
    """
    ids = [b.strip() for b in brand_ids.split(',') if b.strip()][:3]
    if not ids:
        raise HTTPException(400, 'Provide at least 1 brand_id')

    db = get_db()
    brands = []
    for bid in ids:
        r = db.table('brands').select('*').eq('id', bid).single().execute()
        if r.data:
            brands.append(r.data)

    if not brands:
        raise HTTPException(404, 'No brands found for given IDs')

    results = await asyncio.gather(*[_get_cvi_for_brand(b) for b in brands])

    return {
        'panel': list(results),
        'count': len(results),
        'leader': max(results, key=lambda x: x.get('score', 0)).get('brand_name')
    }

@router.get('/history')
async def competitor_history(brand_ids: str, limit: int = 30):
    """
    Returns CVI history for all brands — feeds the multi-line Recharts chart on frontend.
    """
    db = get_db()
    ids = [b.strip() for b in brand_ids.split(',') if b.strip()][:3]
    out = {}
    for bid in ids:
        brand = db.table('brands').select('name').eq('id', bid).single().execute()
        name = brand.data['name'] if brand.data else bid[:8]
        snaps = db.table('cvi_snapshots')\
            .select('score, level, is_anomaly, recorded_at')\
            .eq('brand_id', bid)\
            .order('recorded_at', desc=True)\
            .limit(limit)\
            .execute().data
        out[name] = list(reversed(snaps))
    return out
