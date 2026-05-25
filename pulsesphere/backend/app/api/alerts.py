from fastapi import APIRouter, HTTPException
from app.core.db import get_db

router = APIRouter()

@router.get('/')
async def list_alerts(brand_id: str, active_only: bool = True):
    db = get_db()
    q  = db.table('alerts').select('*').eq('brand_id', brand_id)
    if active_only: q = q.is_('resolved_at', 'null')
    r  = q.order('triggered_at', desc=True).execute()
    return r.data

@router.patch('/{alert_id}/resolve')
async def resolve_alert(alert_id: str):
    db = get_db()
    from datetime import datetime
    db.table('alerts').update({'resolved_at': datetime.utcnow().isoformat()})\
        .eq('id', alert_id).execute()
    return {'resolved': True, 'alert_id': alert_id}
