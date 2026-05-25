from app.ml.model_loader import (
    get_emotion_model, get_fake_news_model,
    get_bot_detector_model, get_zero_shot_model,
    CRISIS_CATEGORIES
)
from app.ingestors.base import PostSchema

BATCH_SIZE = 32

def run_inference_batch(posts: list[PostSchema]) -> list[dict]:
    """
    Input : list of PostSchema
    Output: list of enrichment dicts — one per post
    {
      emotion_scores: {anger, disgust, fear, joy, neutral, sadness, surprise},
      is_fake_news: bool,
      is_bot_generated: bool,
      crisis_category: str,
      neg_score: float  # anger+disgust+fear combined
    }
    """
    texts = [p.content[:512] for p in posts]
    results = []

    emotion_pipe   = get_emotion_model()
    fake_pipe      = get_fake_news_model()
    bot_pipe       = get_bot_detector_model()
    zeroshot_pipe  = get_zero_shot_model()

    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i:i + BATCH_SIZE]

        # Model 1 — Emotion (returns list of label/score dicts per text)
        emotion_results = emotion_pipe(batch, batch_size=BATCH_SIZE)

        # Model 2 — Fake news
        fake_results = fake_pipe(batch, batch_size=BATCH_SIZE)

        # Model 3 — Bot detection
        bot_results = bot_pipe(batch, batch_size=BATCH_SIZE)

        # Model 4 — Zero-shot crisis category (smaller batch — heavy model)
        zs_results = zeroshot_pipe(batch, candidate_labels=CRISIS_CATEGORIES, batch_size=8)

        for j in range(len(batch)):
            # Emotion scores dict
            emotion_dict = {item['label']: round(item['score'], 4) for item in emotion_results[j]}
            neg_score = (
                emotion_dict.get('anger', 0) +
                emotion_dict.get('disgust', 0) +
                emotion_dict.get('fear', 0)
            )

            # Fake news — label is 'REAL' or 'FAKE'
            fake_label = fake_results[j]['label'].upper()
            is_fake = fake_label in ('FAKE', 'LABEL_1', '1')

            # Bot detection — label varies by model version
            bot_label = bot_results[j]['label'].upper()
            is_bot = bot_label in ('CHATGPT', 'MACHINE', 'LABEL_1', '1', 'AI')

            # Zero-shot — top label
            top_category = zs_results[j]['labels'][0].replace(' ', '_')

            results.append({
                'emotion_scores': emotion_dict,
                'is_fake_news': is_fake,
                'is_bot_generated': is_bot,
                'crisis_category': top_category,
                'neg_score': round(neg_score, 4)
            })

    return results
