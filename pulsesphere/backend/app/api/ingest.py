from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.ingestors.orchestrator import ingest_all
from app.core.db import get_db
import json

router = APIRouter()

class IngestRequest(BaseModel):
    brand_id: str
    keywords: list[str]
    brand_name: str

@router.post('/')
async def run_ingest(payload: IngestRequest):
    posts = await ingest_all(payload.keywords, payload.brand_name)
    if not posts:
        raise HTTPException(422, 'No posts collected')

    db = get_db()
    rows = [{
        'brand_id': payload.brand_id,
        'source': p.source,
        'content': p.content,
        'author': p.author,
        'url': p.url,
    } for p in posts]

    db.table('posts').insert(rows).execute()
    return {'inserted': len(rows), 'sources': list(set(p.source for p in posts))}
