from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from app.services.pdf_generator import generate_weekly_pdf
from app.core.db import get_db

router = APIRouter()

@router.get('/pdf')
async def export_pdf(brand_id: str):
    """
    TC17: HTTP 200, Content-Type application/pdf, valid PDF bytes
    """
    db = get_db()

    brand = db.table('brands').select('*').eq('id', brand_id).single().execute()
    if not brand.data: raise HTTPException(404, 'Brand not found')
    brand_name = brand.data['name']

    # Fetch data for report
    cvi_history = db.table('cvi_snapshots')\
        .select('score, level, recorded_at')\
        .eq('brand_id', brand_id)\
        .order('recorded_at', desc=False)\
        .limit(200)\
        .execute().data

    alerts = db.table('alerts')\
        .select('severity, cvi_score, triggered_at')\
        .eq('brand_id', brand_id)\
        .order('triggered_at', desc=True)\
        .limit(20)\
        .execute().data

    playbooks = db.table('playbooks')\
        .select('actions, press_statement, rating, generated_at')\
        .eq('brand_id', brand_id)\
        .order('generated_at', desc=True)\
        .limit(3)\
        .execute().data

    pdf_bytes = generate_weekly_pdf(
        brand_name=brand_name,
        cvi_history=cvi_history,
        alerts=alerts,
        playbooks=playbooks
    )

    return Response(
        content=pdf_bytes,
        media_type='application/pdf',
        headers={
            'Content-Disposition': f'attachment; filename="pulsesphere_{brand_name.lower().replace(" ","_")}_weekly.pdf"'
        }
    )
