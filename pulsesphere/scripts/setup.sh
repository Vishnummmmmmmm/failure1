#!/bin/bash
# One-shot PulseSphere setup
set -e
echo '=== PulseSphere Setup ==='
cd backend
pip install -r requirements.txt
playwright install chromium
cp .env.example .env
echo 'Edit backend/.env with your Supabase + Anthropic keys'
echo 'Then run: cd backend && uvicorn app.main:app --reload --port 8000'
cd ../frontend
npm install
echo 'Frontend ready. Run: npm run dev'
