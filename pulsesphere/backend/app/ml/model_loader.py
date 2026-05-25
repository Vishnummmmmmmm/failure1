from transformers import pipeline
from functools import lru_cache
import torch
from app.core.config import get_settings

def _set_hf_token():
    settings = get_settings()
    if settings.HUGGINGFACE_HUB_TOKEN:
        import huggingface_hub
        huggingface_hub.login(token=settings.HUGGINGFACE_HUB_TOKEN, add_to_git_credential=False)
        print('[ML] HuggingFace token set.')

DEVICE = 0 if torch.cuda.is_available() else -1

@lru_cache(maxsize=1)
def get_emotion_model():
    _set_hf_token()
    print('[ML] Loading emotion model...')
    return pipeline('text-classification', model='j-hartmann/emotion-english-distilroberta-base',
        top_k=None, device=DEVICE, truncation=True, max_length=512)

@lru_cache(maxsize=1)
def get_fake_news_model():
    _set_hf_token()
    print('[ML] Loading fake news model...')
    return pipeline('text-classification', model='mrm8488/bert-tiny-finetuned-fake-news',
        device=DEVICE, truncation=True, max_length=512)

@lru_cache(maxsize=1)
def get_bot_detector_model():
    _set_hf_token()
    print('[ML] Loading bot detector model...')
    return pipeline('text-classification', model='Hello-SimpleAI/chatgpt-detector-roberta',
        device=DEVICE, truncation=True, max_length=512)

@lru_cache(maxsize=1)
def get_zero_shot_model():
    _set_hf_token()
    print('[ML] Loading zero-shot model (~1.6GB)...')
    return pipeline('zero-shot-classification', model='facebook/bart-large-mnli', device=DEVICE)

CRISIS_CATEGORIES = ['product defect','executive scandal','data breach','pricing controversy','service outage','other']

def warmup_all_models():
    print('[ML] Warming up all 4 HuggingFace models...')
    dummy = ['This product is terrible and I am very angry about it.']
    get_emotion_model()(dummy)
    get_fake_news_model()(dummy)
    get_bot_detector_model()(dummy)
    get_zero_shot_model()(dummy, candidate_labels=CRISIS_CATEGORIES)
    print('[ML] All 4 models warm.')
