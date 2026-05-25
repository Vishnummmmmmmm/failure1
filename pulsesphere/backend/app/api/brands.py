from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.core.db import get_db
import uuid

router = APIRouter()

class BrandCreate(BaseModel):
    name: str
    keywords: list[str]
    org_id: str = '00000000-0000-0000-0000-000000000001'

@router.post('/', status_code=201)
def create_brand(payload: BrandCreate):
    db = get_db()
    result = db.table('brands').insert({
        'name': payload.name,
        'keywords': payload.keywords,
        'org_id': payload.org_id
    }).execute()
    if not result.data:
        raise HTTPException(500, 'Insert failed')
    return {'brand_id': result.data[0]['id'], 'name': result.data[0]['name']}

@router.get('/')
def list_brands():
    db = get_db()
    return db.table('brands').select('*').execute().data

@router.get('/{brand_id}')
def get_brand(brand_id: str):
    db = get_db()
    r = db.table('brands').select('*').eq('id', brand_id).single().execute()
    if not r.data: raise HTTPException(404, 'Not found')
    return r.data
