# softsoveapi

Softsove FastAPI for jobs, applications, and CV uploads.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

- Public: `GET /jobs`, `GET /jobs/{slug}`, `POST /jobs/{slug}/apply`
- Admin: `POST /admin/login` then Bearer token for jobs CRUD and applications
