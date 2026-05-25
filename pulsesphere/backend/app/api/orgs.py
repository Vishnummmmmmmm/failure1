from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from app.core.db import get_db
from app.core.config import get_settings
import uuid, httpx

router = APIRouter()

class OrgUpdate(BaseModel):
    org_display_name: str = None
    accent_color: str = None  # hex e.g. '#FF5500'

@router.get('/{org_id}')
def get_org(org_id: str):
    db = get_db()
    r = db.table('orgs').select('*').eq('id', org_id).single().execute()
    if not r.data: raise HTTPException(404, 'Org not found')
    return r.data

@router.patch('/{org_id}')
def update_org(org_id: str, payload: OrgUpdate):
    db = get_db()
    update = {k: v for k, v in payload.dict().items() if v is not None}
    if not update: raise HTTPException(400, 'Nothing to update')
    r = db.table('orgs').update(update).eq('id', org_id).execute()
    return r.data[0] if r.data else {'updated': True}

@router.post('/{org_id}/logo')
async def upload_logo(org_id: str, file: UploadFile = File(...)):
    """
    TC21: Upload PNG/JPG → stored in Supabase Storage org-logos bucket
    → URL saved to orgs.white_label_logo_url
    Returns: {logo_url: 'https://...'}
    """
    if file.content_type not in ('image/png', 'image/jpeg', 'image/svg+xml', 'image/webp'):
        raise HTTPException(400, 'Only PNG, JPG, SVG, WebP allowed')

    settings = get_settings()
    db = get_db()

    # Verify org exists
    org = db.table('orgs').select('id').eq('id', org_id).single().execute()
    if not org.data: raise HTTPException(404, 'Org not found')

    content   = await file.read()
    ext       = file.filename.rsplit('.', 1)[-1].lower() if file.filename else 'png'
    filename  = f'{org_id}/logo.{ext}'

    # Upload to Supabase Storage via REST API
    storage_url = f"{settings.SUPABASE_URL}/storage/v1/object/org-logos/{filename}"
    headers = {
        'Authorization': f'Bearer {settings.SUPABASE_SERVICE_KEY}',
        'Content-Type':  file.content_type,
        'x-upsert':      'true'
    }
    async with httpx.AsyncClient() as client:
        r = await client.post(storage_url, content=content, headers=headers)
        if r.status_code not in (200, 201):
            raise HTTPException(500, f'Storage upload failed: {r.text}')

    # Public URL
    logo_url = f"{settings.SUPABASE_URL}/storage/v1/object/public/org-logos/{filename}"

    # Save to orgs table
    db.table('orgs').update({'white_label_logo_url': logo_url}).eq('id', org_id).execute()

    return {'logo_url': logo_url, 'org_id': org_id}

@router.post('/{org_id}/invite')
async def invite_member(org_id: str, email: str):
    """
    Sends Supabase magic link invite. New user auto-added to org_members on first login
    via the after-login flow in the frontend useAuth hook.
    """
    settings = get_settings()
    # Generate invite token — Supabase Admin API
    invite_url = f"{settings.SUPABASE_URL}/auth/v1/admin/users"
    headers = {
        'Authorization': f'Bearer {settings.SUPABASE_SERVICE_KEY}',
        'apikey':        settings.SUPABASE_SERVICE_KEY,
        'Content-Type':  'application/json'
    }
    payload = {
        'email':           email,
        'email_confirm':   True,
        'user_metadata':   {'invited_to_org': org_id}
    }
    async with httpx.AsyncClient() as client:
        r = await client.post(invite_url, json=payload, headers=headers)
        if r.status_code not in (200, 201):
            raise HTTPException(500, f'Invite failed: {r.text}')
        user_id = r.json().get('id')

    # Pre-add to org_members
    db = get_db()
    db.table('org_members').insert({
        'org_id':  org_id,
        'user_id': user_id,
        'role':    'member'
    }).execute()

    return {'invited': email, 'org_id': org_id, 'user_id': user_id}
