import math
from collections import deque
from datetime import datetime, timedelta
from app.core.db import get_db

# Rolling baseline window
_velocity_history: dict[str, deque] = {}

def compute_cvi(
    posts_with_enrichment: list[dict],
    brand_id: str
) -> dict:
    """
    posts_with_enrichment: output of run_inference_batch merged with posts
    Returns: {score, level, neg_rate, velocity, spike_factor, bot_penalty, fake_penalty}
    """
    n = len(posts_with_enrichment)
    if n == 0:
        return _cvi_snapshot(0.0, brand_id)

    # --- neg_rate: fraction of posts with dominant negative emotion ---
    negative_posts = sum(
        1 for p in posts_with_enrichment
        if p['neg_score'] > 0.4
    )
    neg_rate = negative_posts / n

    # --- velocity: posts_per_min vs rolling 10-min baseline ---
    global _velocity_history
    if brand_id not in _velocity_history:
        _velocity_history[brand_id] = deque(maxlen=10)
    _velocity_history[brand_id].append(n)
    baseline = sum(_velocity_history[brand_id]) / len(_velocity_history[brand_id])
    velocity = n / max(baseline, 1)

    # --- spike_factor: stddev multiplier ---
    if len(_velocity_history[brand_id]) >= 3:
        import statistics
        hist = list(_velocity_history[brand_id])
        try:
            std = statistics.stdev(hist)
            mean = statistics.mean(hist)
            spike_factor = max(1.0, (n - mean) / max(std, 0.001))
        except Exception:
            spike_factor = 1.0
    else:
        spike_factor = 1.0
    spike_factor = min(spike_factor, 5.0)  # cap at 5x

    # --- penalties ---
    bot_ratio  = sum(1 for p in posts_with_enrichment if p['is_bot_generated']) / n
    fake_ratio = sum(1 for p in posts_with_enrichment if p['is_fake_news']) / n
    bot_penalty  = 1 - (bot_ratio  * 0.30)
    fake_penalty = 1 - (fake_ratio * 0.20)

    # --- CVI formula (from spec) ---
    velocity_factor = min(velocity * 0.5, 1.0)  # normalise velocity to 0-1 range
    raw_cvi = (
        (neg_rate        * 0.45) +
        (velocity_factor * 0.35) +
        (min(spike_factor / 5.0, 1.0) * 0.20)
    )
    score = min(100.0, raw_cvi * 100 * bot_penalty * fake_penalty)
    score = round(score, 2)

    return _cvi_snapshot(score, brand_id, {
        'neg_rate':     round(neg_rate, 4),
        'velocity':     round(velocity, 4),
        'spike_factor': round(spike_factor, 4),
        'bot_penalty':  round(bot_penalty, 4),
        'fake_penalty': round(fake_penalty, 4),
    })

def _cvi_snapshot(score: float, brand_id: str, extras: dict = {}) -> dict:
    if score < 40:  level = 'LOW'
    elif score < 60: level = 'WATCH'
    elif score < 75: level = 'MEDIUM'
    elif score < 90: level = 'HIGH'
    else:            level = 'CRITICAL'

    return {
        'score':        score,
        'level':        level,
        'brand_id':     brand_id,
        'recorded_at':  datetime.utcnow().isoformat(),
        **extras
    }

async def save_cvi_snapshot(snapshot: dict, is_anomaly: bool = False):
    db = get_db()
    row = {
        'brand_id':    snapshot['brand_id'],
        'score':       snapshot['score'],
        'level':       snapshot['level'],
        'neg_rate':    snapshot.get('neg_rate', 0),
        'velocity':    snapshot.get('velocity', 1),
        'spike_factor':snapshot.get('spike_factor', 1),
        'is_anomaly':  is_anomaly,
    }
    db.table('cvi_snapshots').insert(row).execute()
    return row
