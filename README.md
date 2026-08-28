# softsoveapi

Softsove FastAPI for jobs, applications, CV uploads, and the contact form.

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
python -m app.bootstrap
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

On the server, from the API root (the folder that contains `alembic.ini`):

```bash
cd /www/wwwroot/api-v8.softsove.com
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
python -m app.bootstrap
```

Then restart the API process.

- Public: `GET /jobs`, `GET /jobs/{slug}`, `POST /jobs/{slug}/apply`, `POST /contact`
- Admin: `POST /admin/login` then Bearer token for jobs CRUD and applications
- Health: `GET /health` (shows `database` and `admins` count)

Seeded admin: `care@softsove.com` / `Softsove@2026@@$` (change it from the panel after login).
