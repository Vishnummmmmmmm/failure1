from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import brands, ingest, cvi, alerts, playbook, export, competitor, competitor_ws, orgs
from app.core.config import get_settings

app = FastAPI(title='PulseSphere API', version='1.0.0')

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_methods=['*'],
    allow_headers=['*'],
)

@app.on_event('startup')
async def startup_event():
    settings = get_settings()
    if not settings.DEMO_MODE:
        from app.ml.model_loader import warmup_all_models
        import asyncio
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, warmup_all_models)
    from app.services.background_jobs import start_background_jobs
    start_background_jobs()
    print('[PulseSphere] API ready.')

app.include_router(brands.router,        prefix='/brands',      tags=['brands'])
app.include_router(ingest.router,        prefix='/ingest',      tags=['ingest'])
app.include_router(cvi.router,           prefix='/cvi',         tags=['cvi'])
app.include_router(alerts.router,        prefix='/alerts',      tags=['alerts'])
app.include_router(playbook.router,      prefix='/playbook',    tags=['playbook'])
app.include_router(export.router,        prefix='/export',      tags=['export'])
app.include_router(competitor.router,    prefix='/competitor',  tags=['competitor'])
app.include_router(competitor_ws.router, prefix='/competitor',  tags=['competitor-ws'])
app.include_router(orgs.router,          prefix='/orgs',        tags=['orgs'])

@app.get('/health')
def health(): return {'status': 'ok', 'version': '1.0.0'}
