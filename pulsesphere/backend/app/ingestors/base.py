from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class PostSchema(BaseModel):
    source: str          # google|reddit|twitter|instagram|facebook|threads
    content: str         # raw text — fed to HF models
    author: str = 'unknown'
    url: str = ''
    ingested_at: datetime = None

    def __init__(self, **data):
        if not data.get('ingested_at'):
            data['ingested_at'] = datetime.utcnow()
        super().__init__(**data)
