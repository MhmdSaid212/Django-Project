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

Open http://127.0.0.1:8000/login/ — seed user `owner@tourops.local` / `changeme`.
