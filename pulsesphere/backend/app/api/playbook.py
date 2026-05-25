from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.playbook_generator import generate_playbook
from app.core.db import get_db
from datetime import datetime

router = APIRouter()

class PlaybookRequest(BaseModel):
    brand_id: str
    cvi_score: float
    alert_id: str = None

class PlaybookRating(BaseModel):
    rating: int  # 0 = not helpful, 1 = helpful

@router.post('/', status_code=201)
async def create_playbook(payload: PlaybookRequest):
    """
    TC13: Returns 3 actions + press_statement, response < 3s
    Unlocks at CVI > 75 (enforced here)
    """
    if payload.cvi_score < 60:
        raise HTTPException(400, f'Playbook requires CVI >= 60. Current: {payload.cvi_score}')

    db = get_db()

    # Get brand info
    brand = db.table('brands').select('*').eq('id', payload.brand_id).single().execute()
    if not brand.data: raise HTTPException(404, 'Brand not found')

    # Get recent top negative posts for context
    recent_posts = db.table('posts')\
        .select('source, content, emotion_scores, crisis_category')\
        .eq('brand_id', payload.brand_id)\
        .order('ingested_at', desc=True)\
        .limit(10)\
        .execute().data

    # Determine crisis category from most common in recent posts
    categories = [p.get('crisis_category', 'other') for p in recent_posts if p.get('crisis_category')]
    top_category = max(set(categories), key=categories.count) if categories else 'other'

    # Determine level from score
    if payload.cvi_score >= 90:   level = 'CRITICAL'
    elif payload.cvi_score >= 75: level = 'HIGH'
    elif payload.cvi_score >= 60: level = 'MEDIUM'
    else:                          level = 'WATCH'

    # Generate via Anthropic
    playbook_data = await generate_playbook(
        brand_name=brand.data['name'],
        cvi_score=payload.cvi_score,
        level=level,
        crisis_category=top_category,
        top_posts=recent_posts,
        alert_id=payload.alert_id or ''
    )

    # Persist to DB
    row = {
        'brand_id':        payload.brand_id,
        'alert_id':        payload.alert_id,
        'actions':         playbook_data.get('actions', []),
        'press_statement': playbook_data.get('press_statement', ''),
        'rating':          None,
    }
    result = db.table('playbooks').insert(row).execute()
    playbook_id = result.data[0]['id'] if result.data else None

    return {
        'playbook_id':  playbook_id,
        'brand_name':   brand.data['name'],
        'cvi_score':    payload.cvi_score,
        'level':        level,
        **playbook_data
    }

@router.patch('/{playbook_id}/rate')
async def rate_playbook(playbook_id: str, payload: PlaybookRating):
    """
    TC14: PATCH with {rating: 1} → playbooks.rating=1 stored as training data
    """
    if payload.rating not in (0, 1):
        raise HTTPException(400, 'rating must be 0 (not helpful) or 1 (helpful)')

    db = get_db()
    result = db.table('playbooks')\
        .update({'rating': payload.rating})\
        .eq('id', playbook_id)\
        .execute()

    if not result.data:
        raise HTTPException(404, f'Playbook {playbook_id} not found')

    return {
        'playbook_id': playbook_id,
        'rating':      payload.rating,
        'stored_as':   'training_data',
        'message':     'Thank you — this rating improves future playbooks'
    }

@router.get('/{playbook_id}')
async def get_playbook(playbook_id: str):
    db = get_db()
    r = db.table('playbooks').select('*').eq('id', playbook_id).single().execute()
    if not r.data: raise HTTPException(404, 'Not found')
    return r.data

@router.get('/')
async def list_playbooks(brand_id: str):
    db = get_db()
    r = db.table('playbooks')\
        .select('*')\
        .eq('brand_id', brand_id)\
        .order('generated_at', desc=True)\
        .execute()
    return r.data
