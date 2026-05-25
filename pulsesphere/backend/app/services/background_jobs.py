from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime, timedelta
from app.core.db import get_db
from app.core.config import get_settings
import asyncio

scheduler = AsyncIOScheduler()

def start_background_jobs():
    """Call this from main.py startup event."""
    scheduler.add_job(
        _fill_crisis_memory_t_plus_60,
        IntervalTrigger(minutes=5),
        id='fill_crisis_memory',
        replace_existing=True
    )
    settings = get_settings()
    if not settings.DEMO_MODE:
        scheduler.add_job(
            _auto_scan_all_brands,
            IntervalTrigger(minutes=5),
            id='auto_scan',
            replace_existing=True
        )
    scheduler.start()
    print('[Jobs] Background scheduler started.')

async def _fill_crisis_memory_t_plus_60():
    """
    TC18: Finds crisis_memory rows where cvi_t_plus_60 is null
    and peak_at was >= 60 min ago. Fills with latest CVI snapshot score.
    """
    db = get_db()
    cutoff = (datetime.utcnow() - timedelta(minutes=60)).isoformat()

    unfilled = db.table('crisis_memory')\
        .select('id, brand_id, peak_at')\
        .is_('cvi_t_plus_60', 'null')\
        .lt('peak_at', cutoff)\
        .execute().data

    for row in unfilled:
        latest = db.table('cvi_snapshots')\
            .select('score')\
            .eq('brand_id', row['brand_id'])\
            .order('recorded_at', desc=True)\
            .limit(1)\
            .execute().data
        if latest:
            db.table('crisis_memory')\
                .update({'cvi_t_plus_60': latest[0]['score']})\
                .eq('id', row['id'])\
                .execute()
            print(f"[Jobs] Filled crisis_memory {row['id']} cvi_t_plus_60={latest[0]['score']}")

async def _auto_scan_all_brands():
    """Every 5 min in live mode: re-scan all brands and write new CVI snapshot."""
    from app.ingestors.orchestrator import ingest_all
    from app.ml.inference import run_inference_batch
    from app.services.cvi_engine import compute_cvi, save_cvi_snapshot
    from app.services.alert_engine import evaluate_and_fire_alert

    db = get_db()
    brands = db.table('brands').select('*').execute().data
    for brand in brands:
        try:
            posts = await ingest_all(brand['keywords'], brand['name'])
            if not posts:
                continue
            enrichments = run_inference_batch(posts)
            merged = [{**p.dict(), **enrichments[i]} for i, p in enumerate(posts)]
            snapshot = compute_cvi(merged, brand['id'])
            await save_cvi_snapshot(snapshot)
            await evaluate_and_fire_alert(brand['id'], snapshot['score'])
            print(f"[Jobs] Auto-scan {brand['name']} → CVI {snapshot['score']}")
        except Exception as e:
            print(f"[Jobs] Auto-scan failed for {brand['name']}: {e}")
