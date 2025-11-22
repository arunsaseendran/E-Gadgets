# Setup Guide

## Prerequisites
- Python 3.11
- pip
- Git

## Local Development
- Create and activate a virtual environment (optional but recommended)
  - Windows (PowerShell):
    - `python -m venv .venv`
    - `.\.venv\Scripts\Activate.ps1`
- Install dependencies
  - `pip install -r requirements.txt`
- Create a `.env` file (do NOT commit this file)
  - `SECRET_KEY=<generate one: python -c "import secrets; print(secrets.token_urlsafe(50))">`
  - `DEBUG=True`
  - `ALLOWED_HOSTS=127.0.0.1,localhost`
  - `CSRF_TRUSTED_ORIGINS=http://127.0.0.1:8000,http://localhost:8000`
  - `EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend`
  - `EMAIL_HOST=smtp.gmail.com`
  - `EMAIL_PORT=587`
  - `EMAIL_USE_TLS=True`
  - `EMAIL_HOST_USER=<your email>`
  - `EMAIL_HOST_PASSWORD=<your app password>`
  - `RAZORPAY_KEY_ID=<your key>`
  - `RAZORPAY_KEY_SECRET=<your secret>`
- Run migrations and start server
  - `python manage.py migrate`
  - `python manage.py runserver`

## Production on Render

### 1) Prepare the repo
- Ensure `.env` is in `.gitignore` and not tracked
- Commit all changes and push to GitHub

### 2) Create a Render Web Service
- On Render Dashboard → New → Web Service → Connect your GitHub repo
- Environment: `Python 3`

### 3) Add a managed Postgres (recommended)
- Render Dashboard → New → PostgreSQL
- Copy the provided `DATABASE_URL`

### 4) Configure Environment Variables (Render → Project → Settings → Environment)
- `SECRET_KEY` = a strong secret (do not reuse local one)
- `DEBUG` = `False`
- `ALLOWED_HOSTS` = `<your-service>.onrender.com`
- `CSRF_TRUSTED_ORIGINS` = `https://<your-service>.onrender.com`
- `DATABASE_URL` = value from Render Postgres
- `EMAIL_BACKEND` = `django.core.mail.backends.smtp.EmailBackend`
- `EMAIL_HOST` = `smtp.gmail.com`
- `EMAIL_PORT` = `587`
- `EMAIL_USE_TLS` = `True`
- `EMAIL_HOST_USER` = `<your email>`
- `EMAIL_HOST_PASSWORD` = `<your app password>`
- `RAZORPAY_KEY_ID` = `<key>`
- `RAZORPAY_KEY_SECRET` = `<secret>`

### 5) Build/Start Commands
- Build Command:
  - `pip install -r requirements.txt && python manage.py collectstatic --noinput`
- Start Command:
  - `gunicorn e_gadgets.wsgi:application --preload`
- Post-deploy Command (recommended):
  - `python manage.py migrate`

### 6) Static and media
- Static files served by WhiteNoise (already configured)
- User uploads (media): use an external storage (e.g., S3/Cloudinary) for production

### 7) Optional
- Pin Python: add `runtime.txt` with `python-3.11.9` for deterministic builds

## Security Checklist
- Rotate any secrets that were ever committed
- Keep `.env` out of Git; provide `.env.example` with placeholders only
- Set `DEBUG=False` in production
