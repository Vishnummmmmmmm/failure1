#!/usr/bin/env python3
"""
Usage: python scripts/seed_crisis_arc.py --brand-id <UUID>
Inserts 60 CVI snapshots spanning 2 hours of fake time:
  T-0 to T-30min:  CVI rises 28 → 91 (crisis builds)
  T-30 to T-60min: CVI peaks 91 → 88 (crisis holds)
  T-60 to T-120min: CVI falls 88 → 42 (resolution)
Frontend timeline chart shows this entire arc instantly.
"""
import sys, os, argparse
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))  
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

from app.core.db import get_db
from datetime import datetime, timedelta
import math

ARC_POINTS = []

def _build_arc():
    """
    60 points over 120 minutes of fake time.
    Curve: sigmoid rise → plateau → exponential decay.
    """
    now = datetime.utcnow()
    for i in range(60):
        t = i / 59  # 0.0 → 1.0
        minutes_ago = 120 - (i * 2)  # goes from 120 min ago to now
        ts = now - timedelta(minutes=minutes_ago)

        if t < 0.4:  # rise: 28 → 91
            raw = t / 0.4
            score = 28 + (91 - 28) * (1 / (1 + math.exp(-10 * (raw - 0.5))))
        elif t < 0.55:  # plateau: 88-91
            score = 91 - (t - 0.4) * 20
        else:  # decay: 88 → 42
            decay_t = (t - 0.55) / 0.45
            score = 88 * math.exp(-2.2 * decay_t) + 42 * (1 - math.exp(-2.2 * decay_t))

        score = round(max(28, min(100, score)), 2)
        if score < 40:   level = 'LOW'
        elif score < 60: level = 'WATCH'
        elif score < 75: level = 'MEDIUM'
        elif score < 90: level = 'HIGH'
        else:             level = 'CRITICAL'

        neg_rate   = round(min(score / 100, 0.95), 4)
        velocity   = round(1 + (score / 100) * 3, 4)
        spike      = round(1 + (score / 100) * 4, 4)
        is_anomaly = score > 75 and i > 15

        ARC_POINTS.append({
            'score':        score,
            'level':        level,
            'neg_rate':     neg_rate,
            'velocity':     velocity,
            'spike_factor': spike,
            'is_anomaly':   is_anomaly,
            'recorded_at':  ts.isoformat()
        })

def seed_arc(brand_id: str):
    _build_arc()
    db = get_db()

    # Clear existing snapshots for clean demo
    db.table('cvi_snapshots').delete().eq('brand_id', brand_id).execute()
    print(f'[Seed] Cleared existing snapshots for brand {brand_id}')

    rows = [{'brand_id': brand_id, **pt} for pt in ARC_POINTS]
    db.table('cvi_snapshots').insert(rows).execute()
    print(f'[Seed] Inserted {len(rows)} CVI arc snapshots')
    print(f'[Seed] Arc: {ARC_POINTS[0]["score"]} → {max(p["score"] for p in ARC_POINTS):.1f} → {ARC_POINTS[-1]["score"]:.1f}')

    # Seed crisis_memory row at peak
    peak = max(ARC_POINTS, key=lambda p: p['score'])
    peak_idx = ARC_POINTS.index(peak)
    t_minus_30 = ARC_POINTS[max(0, peak_idx-15)]['score']
    t_minus_15 = ARC_POINTS[max(0, peak_idx-7)]['score']
    t_plus_60  = ARC_POINTS[min(len(ARC_POINTS)-1, peak_idx+30)]['score']

    db.table('crisis_memory').delete().eq('brand_id', brand_id).execute()
    db.table('crisis_memory').insert({
        'brand_id':       brand_id,
        'crisis_label':   f'Crisis arc — peak CVI {peak["score"]}',
        'cvi_t_minus_30': t_minus_30,
        'cvi_t_minus_15': t_minus_15,
        'cvi_t_0':        peak['score'],
        'cvi_t_plus_60':  t_plus_60,
        'peak_at':        peak['recorded_at']
    }).execute()
    print(f'[Seed] Crisis memory seeded: T-30={t_minus_30:.1f}, T-15={t_minus_15:.1f}, T0={peak["score"]:.1f}, T+60={t_plus_60:.1f}')

    # Seed 3 alerts at WATCH / HIGH / CRITICAL thresholds
    db.table('alerts').delete().eq('brand_id', brand_id).execute()
    alert_seeds = [
        {'brand_id': brand_id, 'severity': 'WATCH',    'cvi_score': 41.2, 'channels_notified': ['email'],               'triggered_at': ARC_POINTS[8]['recorded_at']},
        {'brand_id': brand_id, 'severity': 'HIGH',     'cvi_score': 76.5, 'channels_notified': ['email','slack'],        'triggered_at': ARC_POINTS[22]['recorded_at']},
        {'brand_id': brand_id, 'severity': 'CRITICAL', 'cvi_score': 91.0, 'channels_notified': ['email','slack','sms'],  'triggered_at': ARC_POINTS[30]['recorded_at']},
    ]
    db.table('alerts').insert(alert_seeds).execute()
    print('[Seed] 3 alerts seeded: WATCH + HIGH + CRITICAL')
    print('[Seed] Done. Open the dashboard — the full crisis arc is live.')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--brand-id', required=True, help='UUID of the brand to seed')
    args = parser.parse_args()
    seed_arc(args.brand_id)
