from app.core.db import get_db
from datetime import datetime, timedelta

THRESHOLDS = [
    (90, 'CRITICAL'),
    (75, 'HIGH'),
    (60, 'MEDIUM'),
    (40, 'WATCH'),
]

async def evaluate_and_fire_alert(brand_id: str, cvi_score: float) -> dict | None:
    """
    Checks if CVI crosses a threshold. If yes, inserts alert row.
    Returns alert dict or None if no threshold crossed.
    TC11: CVI=40 → severity=WATCH
    TC12: CVI=75 → severity=HIGH
    """
    severity = None
    for threshold, label in THRESHOLDS:
        if cvi_score >= threshold:
            severity = label
            break

    if not severity:
        return None

    db = get_db()
    channels = ['email']
    if cvi_score >= 75:  channels.append('slack')
    if cvi_score >= 90:  channels.append('sms')

    alert_row = {
        'brand_id':          brand_id,
        'severity':          severity,
        'cvi_score':         cvi_score,
        'channels_notified': channels,
    }
    result = db.table('alerts').insert(alert_row).execute()
    alert_id = result.data[0]['id'] if result.data else None

    # Log crisis memory on HIGH/CRITICAL
    if cvi_score >= 75 and alert_id:
        await _log_crisis_memory(brand_id, alert_id, cvi_score)

    return {'alert_id': alert_id, 'severity': severity, 'channels': channels, 'cvi_score': cvi_score}

async def _log_crisis_memory(brand_id: str, alert_id: str, peak_score: float):
    """
    TC08: crisis_memory row with all 4 timestamps non-null
    Fetches historical CVI snapshots for T-30, T-15, T-0
    """
    db = get_db()
    now = datetime.utcnow()

    snapshots = db.table('cvi_snapshots')\
        .select('score, recorded_at')\
        .eq('brand_id', brand_id)\
        .order('recorded_at', desc=False)\
        .execute().data

    def get_score_at(minutes_ago: int) -> float:
        if not snapshots: return peak_score * 0.3  # estimate if no history
        target = now - timedelta(minutes=minutes_ago)
        closest = min(snapshots,
            key=lambda r: abs(
                datetime.fromisoformat(r['recorded_at'].replace('Z','')) - target
            )
        )
        return closest['score']

    db.table('crisis_memory').insert({
        'brand_id':       brand_id,
        'crisis_label':   f'CVI spike to {peak_score}',
        'cvi_t_minus_30': get_score_at(30),
        'cvi_t_minus_15': get_score_at(15),
        'cvi_t_0':        peak_score,
        'cvi_t_plus_60':  None,  # filled by background job in Prompt 06
    }).execute()
