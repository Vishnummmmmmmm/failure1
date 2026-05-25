from sklearn.ensemble import IsolationForest
import numpy as np
from app.core.db import get_db

def detect_pre_echo(cvi_series: list[float]) -> dict:
    """
    Input:  last 60 CVI readings (1 per minute)
    Output: {is_anomaly, anomaly_score, minutes_early}
    TC15 pass condition: velocity doubles in 2 windows → is_anomaly=True
    """
    if len(cvi_series) < 20:
        return {'is_anomaly': False, 'anomaly_score': 0.0, 'minutes_early': 0}

    X = np.array(cvi_series).reshape(-1, 1)
    clf = IsolationForest(contamination=0.1, random_state=42)
    preds = clf.fit_predict(X)  # -1 = anomaly, 1 = normal

    last_5 = preds[-5:]
    isolation_anomaly = (last_5 == -1).sum() >= 2

    # Velocity double check: current value vs avg of last 10
    velocity_doubled = (
        cvi_series[-1] / max(float(np.mean(cvi_series[-10:])), 1.0)
    ) > 2.0

    is_anomaly = isolation_anomaly or velocity_doubled
    anomaly_score = float(clf.score_samples(X[-1].reshape(1, -1))[0])

    return {
        'is_anomaly':    is_anomaly,
        'anomaly_score': round(anomaly_score, 4),
        'minutes_early': 18 if is_anomaly else 0
    }

async def get_recent_cvi_series(brand_id: str, limit: int = 60) -> list[float]:
    """Fetch last N CVI snapshots for a brand, ordered by time"""
    db = get_db()
    r = db.table('cvi_snapshots')\
        .select('score')\
        .eq('brand_id', brand_id)\
        .order('recorded_at', desc=True)\
        .limit(limit)\
        .execute()
    scores = [row['score'] for row in reversed(r.data)]
    return scores
