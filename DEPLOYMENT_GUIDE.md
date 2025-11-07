# ArmGuard Deployment Guide

## Quick Start (Development)

### 1. Prerequisites
- Python 3.12+ installed
- pip package manager
- Git (optional)

### 2. Installation

```bash
# Navigate to project directory
cd "d:\ GUI projects\3\armguard"

# Create virtual environment
python -m venv .venv

# Activate virtual environment (Windows PowerShell)
.venv\Scripts\Activate.ps1

# Activate virtual environment (Windows Command Prompt)
.venv\Scripts\activate.bat

# Activate virtual environment (Linux/Mac)
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Database Setup

```bash
# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser
```

### 4. Create Admin Groups

```bash
# Run utility script to create groups
python assign_user_groups.py
```

### 5. Run Development Server

```bash
python manage.py runserver
```

Access the application at: `http://127.0.0.1:8000/`

---

## Production Deployment

### Option A: Windows Server (IIS + wfastcgi)

#### 1. Install Dependencies

```powershell
# Install Python 3.12+
# Download from https://www.python.org/downloads/

# Install IIS with CGI
Install-WindowsFeature -name Web-Server -IncludeManagementTools
Install-WindowsFeature -name Web-CGI

# Install wfastcgi
pip install wfastcgi
wfastcgi-enable
```

#### 2. Configure Environment

```powershell
# Create .env file from template
copy .env.example .env

# Edit .env with production values
notepad .env
```

Required `.env` changes:
```
DJANGO_SECRET_KEY=<generate-new-random-key>
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=your-server-ip,your-domain.com
```

#### 3. Collect Static Files

```powershell
python manage.py collectstatic --noinput
```

#### 4. Configure IIS

Create `web.config` in project root:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<configuration>
  <system.webServer>
    <handlers>
      <add name="Python FastCGI" path="*" verb="*" modules="FastCgiModule" scriptProcessor="C:\Path\To\Python\python.exe|C:\Path\To\Python\Scripts\wfastcgi.py" resourceType="Unspecified" requireAccess="Script" />
    </handlers>
  </system.webServer>
  <appSettings>
    <add key="PYTHONPATH" value="D:\GUI projects\3\armguard" />
    <add key="WSGI_HANDLER" value="core.wsgi.application" />
    <add key="DJANGO_SETTINGS_MODULE" value="core.settings" />
  </appSettings>
</configuration>
```

#### 5. Set File Permissions

- Give IIS_IUSRS read/write access to:
  - `db.sqlite3`
  - `media/` folder
  - `logs/` folder (create if needed)

---

### Option B: Linux Server (Nginx + Gunicorn)

#### 1. Install System Dependencies

```bash
sudo apt update
sudo apt install python3.12 python3-pip python3-venv nginx
```

#### 2. Setup Application

```bash
# Create application directory
sudo mkdir -p /var/www/armguard
sudo chown $USER:$USER /var/www/armguard
cd /var/www/armguard

# Copy application files
# (Use git clone or scp to transfer files)

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install gunicorn
```

#### 3. Configure Environment

```bash
# Create .env file
cp .env.example .env
nano .env
```

Set production values:
```
DJANGO_SECRET_KEY=<generate-new-random-key>
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=your-server-ip,your-domain.com
```

#### 4. Configure settings.py for Production

Create `core/settings_production.py`:
```python
from .settings import *
from decouple import config

DEBUG = False
ALLOWED_HOSTS = config('DJANGO_ALLOWED_HOSTS').split(',')

# Security
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Static files
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Database (consider PostgreSQL)
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': config('DB_NAME'),
#         'USER': config('DB_USER'),
#         'PASSWORD': config('DB_PASSWORD'),
#         'HOST': config('DB_HOST'),
#         'PORT': config('DB_PORT'),
#     }
# }
```

#### 5. Collect Static Files & Migrate

```bash
export DJANGO_SETTINGS_MODULE=core.settings_production
python manage.py collectstatic --noinput
python manage.py migrate
```

#### 6. Create Systemd Service

Create `/etc/systemd/system/armguard.service`:
```ini
[Unit]
Description=ArmGuard Gunicorn daemon
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/armguard
Environment="PATH=/var/www/armguard/.venv/bin"
Environment="DJANGO_SETTINGS_MODULE=core.settings_production"
EnvironmentFile=/var/www/armguard/.env
ExecStart=/var/www/armguard/.venv/bin/gunicorn \
    --workers 3 \
    --bind unix:/var/www/armguard/armguard.sock \
    core.wsgi:application

[Install]
WantedBy=multi-user.target
```

Start service:
```bash
sudo systemctl start armguard
sudo systemctl enable armguard
sudo systemctl status armguard
```

#### 7. Configure Nginx

Create `/etc/nginx/sites-available/armguard`:
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location = /favicon.ico { access_log off; log_not_found off; }
    
    location /static/ {
        alias /var/www/armguard/staticfiles/;
    }

    location /media/ {
        alias /var/www/armguard/core/media/;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/var/www/armguard/armguard.sock;
    }
}
```

Enable site:
```bash
sudo ln -s /etc/nginx/sites-available/armguard /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

#### 8. SSL Certificate (Let's Encrypt)

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

---

## Database Migration (SQLite to PostgreSQL)

### 1. Install PostgreSQL

**Windows:**
- Download from https://www.postgresql.org/download/windows/

**Linux:**
```bash
sudo apt install postgresql postgresql-contrib
```

### 2. Create Database

```bash
sudo -u postgres psql
```

```sql
CREATE DATABASE armguard_db;
CREATE USER armguard_user WITH PASSWORD 'secure_password_here';
ALTER ROLE armguard_user SET client_encoding TO 'utf8';
ALTER ROLE armguard_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE armguard_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE armguard_db TO armguard_user;
\q
```

### 3. Update settings.py

```python
pip install psycopg2-binary

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'armguard_db',
        'USER': 'armguard_user',
        'PASSWORD': 'secure_password_here',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

### 4. Migrate Data

```bash
# Backup SQLite database
python manage.py dumpdata > backup.json

# Switch to PostgreSQL in settings.py

# Run migrations
python manage.py migrate

# Load data
python manage.py loaddata backup.json
```

---

## Security Checklist

Before going live, ensure:

- [ ] SECRET_KEY is randomized and in .env file
- [ ] DEBUG=False
- [ ] ALLOWED_HOSTS configured
- [ ] HTTPS/SSL certificate installed
- [ ] SECURE_* settings enabled in production
- [ ] Database backups configured
- [ ] Static files collected
- [ ] Media files folder has proper permissions
- [ ] .env file is NOT in version control
- [ ] Strong database passwords
- [ ] Firewall configured (allow only HTTP/HTTPS)
- [ ] Regular security updates scheduled

---

## Maintenance

### Backup Database

```bash
# SQLite
cp db.sqlite3 db.sqlite3.backup.$(date +%Y%m%d)

# PostgreSQL
pg_dump -U armguard_user armguard_db > backup_$(date +%Y%m%d).sql
```

### Update Application

```bash
# Pull latest code
git pull origin main

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Restart service (Linux)
sudo systemctl restart armguard

# Restart IIS (Windows)
iisreset
```

### Monitor Logs

```bash
# Gunicorn logs
sudo journalctl -u armguard -f

# Nginx logs
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/access.log

# Django logs
tail -f logs/django_errors.log
```

---

## Troubleshooting

### Issue: Static files not loading
**Solution:**
```bash
python manage.py collectstatic --noinput
# Check STATIC_ROOT and STATIC_URL in settings
```

### Issue: Database connection error
**Solution:**
- Check database credentials in .env
- Ensure PostgreSQL service is running
- Check pg_hba.conf for connection permissions

### Issue: Permission denied errors
**Solution:**
```bash
# Linux
sudo chown -R www-data:www-data /var/www/armguard
sudo chmod -R 755 /var/www/armguard

# Windows
# Give IIS_IUSRS appropriate permissions
```

### Issue: 500 Internal Server Error
**Solution:**
- Check DEBUG=True temporarily to see error
- Check logs in logs/django_errors.log
- Verify all migrations are applied
- Check ALLOWED_HOSTS configuration

---

## Support

For issues or questions:
1. Check the CODE_REVIEW_REPORT.md
2. Review Django logs
3. Consult Django documentation: https://docs.djangoproject.com/

---

**Last Updated:** November 5, 2025
