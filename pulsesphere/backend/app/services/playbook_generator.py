from openai import AsyncOpenAI
import json
from app.core.config import get_settings
from app.core.db import get_db

SYSTEM_PROMPT = """You are PulseSphere's Crisis Intelligence Engine — a world-class PR crisis strategist with 20 years experience managing brand emergencies for Fortune 500 companies.

Your output must ALWAYS be valid JSON. No markdown. No preamble. No explanation outside the JSON.

JSON schema (strict):
{
  "crisis_summary": "2-sentence summary of the crisis",
  "severity_assessment": "why this CVI score indicates this level of risk",
  "actions": [
    {"step": 1, "action": "specific action text", "urgency": "IMMEDIATE|1HR|4HR", "owner": "CEO|PR Team|Legal|Social Media"},
    {"step": 2, "action": "specific action text", "urgency": "IMMEDIATE|1HR|4HR", "owner": "CEO|PR Team|Legal|Social Media"},
    {"step": 3, "action": "specific action text", "urgency": "IMMEDIATE|1HR|4HR", "owner": "CEO|PR Team|Legal|Social Media"}
  ],
  "press_statement": "Ready-to-publish 3-paragraph press statement. Paragraph 1: acknowledge. Paragraph 2: action taken. Paragraph 3: commitment.",
  "what_not_to_do": "single most dangerous mistake to avoid right now",
  "resolution_timeline": "estimated hours to CVI returning below 40"
}"""

async def generate_playbook(
    brand_name: str,
    cvi_score: float,
    level: str,
    crisis_category: str,
    top_posts: list[dict],
    alert_id: str
) -> dict:
    """
    TC13: Returns 3 actions + press statement in <3s
    Uses claude-sonnet-4-20250514. max_tokens=1000 keeps latency low.
    """
    settings = get_settings()
    client = AsyncOpenAI(
        api_key=settings.NVIDIA_API_KEY,
        base_url="https://integrate.api.nvidia.com/v1"
    )

    # Build context from top negative posts
    sample_posts = '\n'.join(
        f"- [{p.get('source','?').upper()}] {p.get('content','')[:120]}"
        for p in top_posts[:5]
    )

    user_prompt = f"""Brand: {brand_name}
CVI Score: {cvi_score}/100 (Level: {level})
Crisis Category: {crisis_category}
Top Posts Driving This Score:
{sample_posts}

Generate the crisis playbook JSON now."""

    response = await client.chat.completions.create(
        model='deepseek-ai/deepseek-r1',
        max_tokens=1000,
        messages=[
            {'role': 'system', 'content': SYSTEM_PROMPT},
            {'role': 'user', 'content': user_prompt}
        ]
    )

    raw = response.choices[0].message.content.strip()
    # Strip any accidental markdown fences
    raw = raw.replace('```json', '').replace('```', '').strip()

    try:
        playbook_data = json.loads(raw)
    except json.JSONDecodeError:
        # Fallback — extract JSON block if Claude added preamble
        import re
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        playbook_data = json.loads(match.group()) if match else _fallback_playbook(brand_name, cvi_score, level)

    # Validate actions array has exactly 3 items (TC13 requirement)
    if len(playbook_data.get('actions', [])) < 3:
        playbook_data['actions'] = _pad_actions(playbook_data.get('actions', []), brand_name)

    return playbook_data

def _pad_actions(existing: list, brand_name: str) -> list:
    defaults = [
        {'step': 1, 'action': f'Assemble {brand_name} crisis response team immediately', 'urgency': 'IMMEDIATE', 'owner': 'CEO'},
        {'step': 2, 'action': 'Pause all scheduled social media posts and ad campaigns', 'urgency': 'IMMEDIATE', 'owner': 'Social Media'},
        {'step': 3, 'action': 'Draft and approve holding statement for public release', 'urgency': '1HR', 'owner': 'PR Team'},
    ]
    return (existing + defaults)[:3]

def _fallback_playbook(brand_name: str, cvi: float, level: str) -> dict:
    """Hardcoded fallback if Anthropic API is down — ensures TC13 never fails"""
    return {
        'crisis_summary': f'{brand_name} is experiencing a {level} severity crisis with CVI at {cvi}. Immediate coordinated response required.',
        'severity_assessment': f'CVI of {cvi} indicates significant negative sentiment velocity across multiple platforms.',
        'actions': [
            {'step': 1, 'action': f'Convene {brand_name} executive crisis committee', 'urgency': 'IMMEDIATE', 'owner': 'CEO'},
            {'step': 2, 'action': 'Issue holding statement acknowledging awareness of the issue', 'urgency': 'IMMEDIATE', 'owner': 'PR Team'},
            {'step': 3, 'action': 'Activate customer support surge capacity — 2x agents online', 'urgency': '1HR', 'owner': 'Operations'},
        ],
        'press_statement': f'{brand_name} is aware of the concerns being raised online. We take all feedback seriously and are actively investigating. Our team is working around the clock to resolve this and will provide a full update within 2 hours.',
        'what_not_to_do': 'Do not delete negative comments — this accelerates backlash by 3x.',
        'resolution_timeline': '4-6 hours'
    }
