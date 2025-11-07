# GitHub Upload & Raspberry Pi Deployment Guide

**Project:** ArmGuard Military Armory Management System  
**Target:** Raspberry Pi with Ubuntu Server OS  
**Date:** November 7, 2025

---

## Part 1: Preparing for GitHub Upload

### Step 1: Verify .gitignore is Correct

Your `.gitignore` file should already exclude sensitive files. Verify it contains:

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
*.egg-info/
dist/
build/

# Django
*.log
db.sqlite3
db.sqlite3-journal
/media/
/staticfiles/
/static/

# Environment
.env
.env.local
.env.*.local
venv/
.venv/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db
```

✅ **This file already exists in your project!**

---

### Step 2: Initialize Git Repository

Open PowerShell in your project directory:

```powershell
# Navigate to project
cd "d:\ GUI projects\3\armguard"

# Initialize Git repository
git init

# Add all files (respects .gitignore)
git add .

# Create initial commit
git commit -m "Initial commit: ArmGuard Military Armory Management System"
```

---

### Step 3: Create GitHub Repository

#### Option A: Using GitHub Website

1. **Go to:** https://github.com/new
2. **Repository name:** `armguard` (or your preferred name)
3. **Description:** "Military Armory Management System with QR Code Integration"
4. **Visibility:** Choose Private or Public
5. **DO NOT** initialize with README, .gitignore, or license (we already have these)
6. **Click:** "Create repository"

#### Option B: Using GitHub CLI (gh)

```powershell
# Install GitHub CLI first (if not installed)
# Download from: https://cli.github.com/

# Login to GitHub
gh auth login

# Create repository
gh repo create armguard --private --source=. --remote=origin --push
```

---

### Step 4: Link Local Repository to GitHub

After creating the GitHub repository, you'll see commands like this:

```powershell
# Add remote repository
git remote add origin https://github.com/YOUR_USERNAME/armguard.git

# Verify remote
git remote -v

# Push to GitHub
git branch -M main
git push -u origin main
```

**Replace `YOUR_USERNAME` with your actual GitHub username!**

---

### Step 5: Verify Upload

```powershell
# Check status
git status

# View commit history
git log --oneline

# Check what's being tracked
git ls-files
```

✅ **Your code is now on GitHub!**

---

## Part 2: Raspberry Pi Ubuntu Server Setup

### Prerequisites on Raspberry Pi

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.12+ and dependencies
sudo apt install -y python3 python3-pip python3-venv git nginx

# Install PostgreSQL (recommended for production)
sudo apt install -y postgresql postgresql-contrib

# Install system dependencies for Pillow
sudo apt install -y libjpeg-dev zlib1g-dev
```

---

### Step 6: Clone Repository on Raspberry Pi

```bash
# Create application directory
sudo mkdir -p /var/www
cd /var/www

# Clone repository
sudo git clone https://github.com/YOUR_USERNAME/armguard.git

# Change ownership
sudo chown -R $USER:$USER /var/www/armguard

# Navigate to project
cd armguard
```

---

### Step 7: Create Virtual Environment

```bash
# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Install production server (Gunicorn)
pip install gunicorn

# Install PostgreSQL adapter (if using PostgreSQL)
pip install psycopg2-binary
```

---

### Step 8: Configure Environment Variables

```bash
# Copy environment template
cp .env.example .env

# Generate new SECRET_KEY
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# Edit .env file
nano .env
```

**Configure for production:**

```env
# Production Settings
DJANGO_SECRET_KEY=YOUR_GENERATED_SECRET_KEY_HERE
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=your-raspberry-pi-ip,your-domain.com,localhost

# Security Settings (HTTPS)
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_HSTS_SECONDS=31536000

# Database (if using PostgreSQL)
DATABASE_ENGINE=django.db.backends.postgresql
DATABASE_NAME=armguard_db
DATABASE_USER=armguard_user
DATABASE_PASSWORD=your_secure_password
DATABASE_HOST=localhost
DATABASE_PORT=5432
```

**Save:** Press `Ctrl+X`, then `Y`, then `Enter`

---

### Step 9: Setup PostgreSQL Database (Recommended)

```bash
# Switch to postgres user
sudo -u postgres psql

# In PostgreSQL shell:
CREATE DATABASE armguard_db;
CREATE USER armguard_user WITH PASSWORD 'your_secure_password';
ALTER ROLE armguard_user SET client_encoding TO 'utf8';
ALTER ROLE armguard_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE armguard_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE armguard_db TO armguard_user;
\q

# Exit PostgreSQL
```

**Update settings.py to use PostgreSQL:**

```bash
nano core/settings.py
```

Add this section (replace SQLite configuration):

```python
# Database Configuration
if config('DATABASE_ENGINE', default='') == 'django.db.backends.postgresql':
    DATABASES = {
        'default': {
            'ENGINE': config('DATABASE_ENGINE'),
            'NAME': config('DATABASE_NAME'),
            'USER': config('DATABASE_USER'),
            'PASSWORD': config('DATABASE_PASSWORD'),
            'HOST': config('DATABASE_HOST', default='localhost'),
            'PORT': config('DATABASE_PORT', default='5432'),
        }
    }
else:
    # SQLite (default for development)
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
```

---

### Step 10: Run Django Migrations

```bash
# Activate virtual environment (if not already active)
source .venv/bin/activate

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Create user groups
python assign_user_groups.py

# Collect static files
python manage.py collectstatic --noinput

# Test configuration
python manage.py check --deploy
```

---

### Step 11: Setup Gunicorn Service

```bash
# Create Gunicorn systemd service
sudo nano /etc/systemd/system/gunicorn.service
```

**Add this content:**

```ini
[Unit]
Description=Gunicorn daemon for ArmGuard
After=network.target

[Service]
User=YOUR_USERNAME
Group=www-data
WorkingDirectory=/var/www/armguard
Environment="PATH=/var/www/armguard/.venv/bin"
ExecStart=/var/www/armguard/.venv/bin/gunicorn \
    --workers 3 \
    --bind unix:/var/www/armguard/gunicorn.sock \
    core.wsgi:application

[Install]
WantedBy=multi-user.target
```

**Replace `YOUR_USERNAME` with your Ubuntu username!**

**Save and enable:**

```bash
# Reload systemd
sudo systemctl daemon-reload

# Start Gunicorn
sudo systemctl start gunicorn

# Enable auto-start on boot
sudo systemctl enable gunicorn

# Check status
sudo systemctl status gunicorn
```

---

### Step 12: Configure Nginx

```bash
# Create Nginx configuration
sudo nano /etc/nginx/sites-available/armguard
```

**Add this content:**

```nginx
server {
    listen 80;
    server_name your-raspberry-pi-ip your-domain.com;

    client_max_body_size 10M;

    location = /favicon.ico { 
        access_log off; 
        log_not_found off; 
    }

    location /static/ {
        alias /var/www/armguard/staticfiles/;
    }

    location /media/ {
        alias /var/www/armguard/core/media/;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/var/www/armguard/gunicorn.sock;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header Host $host;
        proxy_redirect off;
    }
}
```

**Enable site:**

```bash
# Create symbolic link
sudo ln -s /etc/nginx/sites-available/armguard /etc/nginx/sites-enabled/

# Test Nginx configuration
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx

# Enable Nginx auto-start
sudo systemctl enable nginx
```

---

### Step 13: Setup Firewall

```bash
# Allow SSH
sudo ufw allow OpenSSH

# Allow HTTP
sudo ufw allow 'Nginx HTTP'

# Allow HTTPS (for later)
sudo ufw allow 'Nginx HTTPS'

# Enable firewall
sudo ufw enable

# Check status
sudo ufw status
```

---

### Step 14: Setup SSL Certificate (HTTPS)

```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Obtain SSL certificate
sudo certbot --nginx -d your-domain.com

# Test auto-renewal
sudo certbot renew --dry-run
```

**Follow the prompts to configure HTTPS.**

---

### Step 15: Set Permissions

```bash
# Set proper ownership
sudo chown -R $USER:www-data /var/www/armguard

# Set directory permissions
sudo find /var/www/armguard -type d -exec chmod 755 {} \;

# Set file permissions
sudo find /var/www/armguard -type f -exec chmod 644 {} \;

# Make manage.py executable
chmod +x /var/www/armguard/manage.py

# Media folder permissions (for uploads)
sudo chmod -R 775 /var/www/armguard/core/media
```

---

## Part 3: Updating Deployment

### When You Make Changes on Windows

```powershell
# On Windows (your development machine)
cd "d:\ GUI projects\3\armguard"

# Add changes
git add .

# Commit changes
git commit -m "Description of changes"

# Push to GitHub
git push origin main
```

### Pull Changes on Raspberry Pi

```bash
# On Raspberry Pi
cd /var/www/armguard

# Pull latest changes
git pull origin main

# Activate virtual environment
source .venv/bin/activate

# Install new dependencies (if any)
pip install -r requirements.txt

# Run migrations (if models changed)
python manage.py migrate

# Collect static files (if CSS/JS changed)
python manage.py collectstatic --noinput

# Restart Gunicorn
sudo systemctl restart gunicorn

# Restart Nginx
sudo systemctl restart nginx
```

---

## Part 4: Troubleshooting

### Check Logs

```bash
# Gunicorn logs
sudo journalctl -u gunicorn -f

# Nginx error logs
sudo tail -f /var/log/nginx/error.log

# Nginx access logs
sudo tail -f /var/log/nginx/access.log

# Django logs (if configured)
tail -f /var/www/armguard/django.log
```

### Common Issues

#### 1. Gunicorn Not Starting

```bash
# Check socket file
ls -l /var/www/armguard/gunicorn.sock

# Check service status
sudo systemctl status gunicorn

# Restart service
sudo systemctl restart gunicorn
```

#### 2. Static Files Not Loading

```bash
# Collect static files again
python manage.py collectstatic --noinput --clear

# Check permissions
ls -l /var/www/armguard/staticfiles/
```

#### 3. Database Connection Errors

```bash
# Test PostgreSQL connection
psql -U armguard_user -d armguard_db -h localhost

# Check .env file
cat /var/www/armguard/.env
```

#### 4. Permission Denied Errors

```bash
# Fix ownership
sudo chown -R $USER:www-data /var/www/armguard

# Fix media folder
sudo chmod -R 775 /var/www/armguard/core/media
```

---

## Part 5: Backup & Maintenance

### Backup Script

```bash
# Create backup script
nano /var/www/armguard/backup.sh
```

**Add this content:**

```bash
#!/bin/bash
BACKUP_DIR="/home/$USER/armguard_backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup database
pg_dump -U armguard_user armguard_db > $BACKUP_DIR/db_$DATE.sql

# Backup media files
tar -czf $BACKUP_DIR/media_$DATE.tar.gz -C /var/www/armguard/core media/

# Keep only last 7 days of backups
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "Backup completed: $DATE"
```

**Make executable:**

```bash
chmod +x /var/www/armguard/backup.sh
```

### Schedule Daily Backups

```bash
# Edit crontab
crontab -e

# Add this line (daily at 2 AM)
0 2 * * * /var/www/armguard/backup.sh >> /var/log/armguard_backup.log 2>&1
```

---

## Part 6: Quick Reference Commands

### Raspberry Pi Commands

```bash
# Check service status
sudo systemctl status gunicorn
sudo systemctl status nginx

# Restart services
sudo systemctl restart gunicorn
sudo systemctl restart nginx

# View logs
sudo journalctl -u gunicorn -f
sudo tail -f /var/log/nginx/error.log

# Pull latest code
cd /var/www/armguard && git pull origin main

# Django management
source .venv/bin/activate
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
```

### Windows (Development) Commands

```powershell
# Git operations
git status
git add .
git commit -m "Your message"
git push origin main

# Django operations
cd "d:\ GUI projects\3\armguard"
.venv\Scripts\Activate.ps1
python manage.py runserver
python manage.py check --deploy
```

---

## Part 7: Security Checklist

### Before Going Live

- [ ] **Change all default passwords**
  - PostgreSQL database password
  - Django superuser password
  - Ubuntu user password

- [ ] **Environment configuration**
  - [ ] DEBUG=False in production
  - [ ] Strong SECRET_KEY generated
  - [ ] ALLOWED_HOSTS configured
  - [ ] SSL/HTTPS enabled

- [ ] **Database security**
  - [ ] PostgreSQL password authentication
  - [ ] Database backups configured
  - [ ] Regular backup testing

- [ ] **System security**
  - [ ] Firewall enabled (UFW)
  - [ ] Only necessary ports open
  - [ ] SSH key authentication (recommended)
  - [ ] Fail2ban installed (optional)

- [ ] **Django security**
  - [ ] CSRF protection enabled
  - [ ] SECURE_SSL_REDIRECT=True
  - [ ] SESSION_COOKIE_SECURE=True
  - [ ] CSRF_COOKIE_SECURE=True
  - [ ] SECURE_HSTS_SECONDS=31536000

- [ ] **File permissions**
  - [ ] .env file not in git
  - [ ] Media folder writable
  - [ ] Static files readable
  - [ ] Sensitive files not world-readable

---

## Part 8: Finding Your Raspberry Pi IP

### On Raspberry Pi

```bash
# Find IP address
hostname -I

# Or
ip addr show

# Or
ifconfig
```

### On Windows (same network)

```powershell
# Scan network for Raspberry Pi
arp -a

# Or use Advanced IP Scanner
# Download: https://www.advanced-ip-scanner.com/
```

### Access Points

- **HTTP:** `http://RASPBERRY_PI_IP`
- **HTTPS:** `https://your-domain.com` (after SSL setup)
- **Admin:** `http://RASPBERRY_PI_IP/admin/`

---

## Part 9: Complete Deployment Timeline

### Day 1: Preparation (Windows)
1. ✅ Verify .gitignore
2. ✅ Initialize Git repository
3. ✅ Create GitHub repository
4. ✅ Push code to GitHub
5. ✅ Test code locally

### Day 2: Raspberry Pi Setup
1. ✅ Install Ubuntu Server on Raspberry Pi
2. ✅ Update system packages
3. ✅ Install Python, PostgreSQL, Nginx
4. ✅ Clone repository from GitHub
5. ✅ Setup virtual environment

### Day 3: Django Configuration
1. ✅ Create .env file
2. ✅ Setup PostgreSQL database
3. ✅ Run migrations
4. ✅ Create superuser
5. ✅ Test Django application

### Day 4: Web Server Setup
1. ✅ Configure Gunicorn
2. ✅ Configure Nginx
3. ✅ Setup firewall
4. ✅ Test HTTP access
5. ✅ Setup SSL/HTTPS

### Day 5: Final Testing
1. ✅ Test all features
2. ✅ Setup backups
3. ✅ Configure monitoring
4. ✅ Security audit
5. ✅ Go live!

---

## Part 10: GitHub Repository Best Practices

### README.md for GitHub

Your repository should have a good README. Update `README.md`:

```markdown
# ArmGuard - Military Armory Management System

QR Code-based military armory management system built with Django.

## Features
- Personnel & Item Management
- QR Code Generation & Scanning
- Transaction Tracking (Take/Return)
- Role-based Access Control
- PDF Printing for Reports

## Tech Stack
- Django 5.1.1
- Python 3.12+
- PostgreSQL (Production)
- Nginx + Gunicorn
- QR Code Generation

## Quick Start
See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)

## License
MIT License
```

### Add License File

```bash
# On Windows
cd "d:\ GUI projects\3\armguard"
# Create LICENSE file (MIT License example)
```

---

## ✅ Deployment Complete!

Your ArmGuard system is now:
- ✅ Hosted on GitHub (version controlled)
- ✅ Deployed on Raspberry Pi Ubuntu Server
- ✅ Accessible via web browser
- ✅ Secured with HTTPS
- ✅ Auto-starting on boot
- ✅ Backed up daily

---

## 📞 Support

**Documentation:**
- DEPLOYMENT_GUIDE.md - Detailed deployment instructions
- CODE_REVIEW_REPORT.md - Technical documentation
- SECURITY_FIXES_APPLIED.md - Security configuration
- TESTING_GUIDE.md - Testing procedures

**Resources:**
- Django: https://docs.djangoproject.com/
- Nginx: https://nginx.org/en/docs/
- Gunicorn: https://docs.gunicorn.org/
- Let's Encrypt: https://letsencrypt.org/

---

**Last Updated:** November 7, 2025  
**Guide Version:** 1.0  
**Status:** Production Ready ✅
