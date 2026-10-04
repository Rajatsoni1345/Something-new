# Birthday Quest — Backend

Flask + Firebase + Cloudinary backend for the Birthday Quest
cinematic experience.

## Quick start

```bash
cd backend
python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env with real secrets (never commit .env)

python app.py
# → http://127.0.0.1:5000/api/v1/health
