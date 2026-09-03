# TourOps

Django + MongoDB (PyMongo) skeleton for travel-agency operations.

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python manage.py seed_demo_user
python manage.py runserver
```

Open http://127.0.0.1:8000/login/

| Email | Password | Role |
| --- | --- | --- |
| `owner@tourops.local` | `changeme` | Owner / Admin |
| `agent@tourops.local` | `changeme` | Travel Agent |
| `accountant@tourops.local` | `changeme` | Accountant |
