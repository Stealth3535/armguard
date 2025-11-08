# Security Guide: Testing LAN App Online

This guide covers securing your Django app and Ubuntu server when temporarily exposing it to the internet for development testing.

---

## ⚠️ Important Warning

**This app was designed for LOCAL NETWORK use only.** Exposing it to the internet, even temporarily, introduces security risks. Follow ALL steps in this guide to minimize vulnerabilities.

**Recommended approach:** Use a VPN (like Tailscale) instead of direct internet exposure for remote testing.

---

## Part 1: Django Application Security

### 1. Update Django Settings for Production Testing

Create or update `core/settings_production.py`:

```python
from .settings import *
from decouple import config
import os

# CRITICAL: Never use DEBUG=True in production
DEBUG = False

# Set your domain/IP (comma-separated, no spaces)
ALLOWED_HOSTS = config('DJANGO_ALLOWED_HOSTS', default='').split(',')

# Security Headers
SECURE_SSL_REDIRECT = True  # Force HTTPS
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# CSRF Protection
CSRF_COOKIE_HTTPONLY = True
CSRF_USE_SESSIONS = False
CSRF_COOKIE_SAMESITE = 'Strict'
SESSION_COOKIE_SAMESITE = 'Strict'

# Additional Security
SECURE_REFERRER_POLICY = 'same-origin'
SECURE_CROSS_ORIGIN_OPENER_POLICY = 'same-origin'

# Rate limiting (requires django-ratelimit)
RATELIMIT_ENABLE = True
RATELIMIT_USE_CACHE = 'default'

# Password validation (already in settings.py, but verify)
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 12}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Session Security
SESSION_COOKIE_AGE = 3600  # 1 hour (adjust as needed)
SESSION_SAVE_EVERY_REQUEST = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# File Upload Security
FILE_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB
FILE_UPLOAD_PERMISSIONS = 0o644
FILE_UPLOAD_DIRECTORY_PERMISSIONS = 0o755

# Admin URL obfuscation (change in urls.py)
# Don't use /admin/ - use something random like /secure-portal-x7k2m/

# Logging for security events
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'security_file': {
            'level': 'WARNING',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/armguard/security.log',
            'maxBytes': 1024 * 1024 * 10,  # 10MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'error_file': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/armguard/errors.log',
            'maxBytes': 1024 * 1024 * 10,
            'backupCount': 5,
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django.security': {
            'handlers': ['security_file'],
            'level': 'WARNING',
            'propagate': False,
        },
        'django': {
            'handlers': ['error_file'],
            'level': 'ERROR',
            'propagate': False,
        },
    },
}

# Database connection pooling (if using PostgreSQL)
DATABASES['default']['CONN_MAX_AGE'] = 600  # 10 minutes

# Static/Media files (served by Nginx, not Django)
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_ROOT = BASE_DIR / 'media'
```

### 2. Update `.env` File

```bash
# Generate a new secret key (NEVER use the default!)
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Update `.env`:
```env
# Django Core
DJANGO_SECRET_KEY=<paste-generated-key-here>
DJANGO_DEBUG=False
DJANGO_SETTINGS_MODULE=core.settings_production
DJANGO_ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com,your-server-ip

# Database (use PostgreSQL, not SQLite for production)
DB_ENGINE=django.db.backends.postgresql
DB_NAME=armguard_db
DB_USER=armguard_user
DB_PASSWORD=<strong-random-password>
DB_HOST=localhost
DB_PORT=5432

# Admin Email (for error notifications)
ADMIN_EMAIL=your-email@example.com
```

### 3. Obfuscate Admin URL

Edit `core/urls.py`:

```python
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
import os

# Use environment variable for admin URL (default to random string)
ADMIN_URL = os.getenv('DJANGO_ADMIN_URL', 'secure-portal-x7k2m')

urlpatterns = [
    path(f'{ADMIN_URL}/', admin.site.urls),  # Changed from 'admin/'
    # ... rest of your URLs
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

Add to `.env`:
```env
DJANGO_ADMIN_URL=your-random-secure-string-here
```

### 4. Install Additional Security Packages

Add to `requirements.txt`:
```
# Security
django-ratelimit>=4.1.0      # Rate limiting
django-defender>=0.9.7       # Brute-force protection
django-axes>=6.1.1           # Failed login tracking
```

Install:
```bash
source .venv/bin/activate
pip install django-ratelimit django-defender django-axes
```

### 5. Configure Rate Limiting

Create `core/middleware.py`:
```python
from django.core.cache import cache
from django.http import HttpResponseForbidden
from django.utils.deprecation import MiddlewareMixin
import time

class RateLimitMiddleware(MiddlewareMixin):
    """Simple rate limiting middleware"""
    
    def process_request(self, request):
        if request.user.is_authenticated:
            return None  # Skip for authenticated users
            
        ip = self.get_client_ip(request)
        cache_key = f'ratelimit_{ip}'
        
        requests = cache.get(cache_key, [])
        now = time.time()
        
        # Remove requests older than 1 minute
        requests = [req_time for req_time in requests if now - req_time < 60]
        
        # Allow 30 requests per minute per IP
        if len(requests) >= 30:
            return HttpResponseForbidden('Rate limit exceeded. Try again later.')
        
        requests.append(now)
        cache.set(cache_key, requests, 60)
        
        return None
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
```

Add to `settings_production.py`:
```python
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'core.middleware.RateLimitMiddleware',  # Add this
    'django.contrib.sessions.middleware.SessionMiddleware',
    # ... rest of middleware
]
```

### 6. Enable Django Axes (Failed Login Protection)

Add to `settings_production.py`:
```python
INSTALLED_APPS = [
    # ... existing apps
    'axes',
]

MIDDLEWARE = [
    # ... existing middleware
    'axes.middleware.AxesMiddleware',  # Add after AuthenticationMiddleware
]

AUTHENTICATION_BACKENDS = [
    'axes.backends.AxesStandaloneBackend',  # Axes backend
    'django.contrib.auth.backends.ModelBackend',
]

# Axes Configuration
AXES_FAILURE_LIMIT = 5  # Lock after 5 failed attempts
AXES_COOLOFF_TIME = 1  # 1 hour lockout
AXES_LOCK_OUT_BY_COMBINATION_USER_AND_IP = True
AXES_RESET_ON_SUCCESS = True
```

Run migrations:
```bash
python manage.py migrate axes
```

### 7. Create Log Directories

```bash
sudo mkdir -p /var/log/armguard
sudo chown www-data:www-data /var/log/armguard
sudo chmod 755 /var/log/armguard
```

---

## Part 2: Server Security (Ubuntu)

### 1. Update and Harden the System

```bash
# Update all packages
sudo apt update && sudo apt upgrade -y

# Install security tools
sudo apt install -y ufw fail2ban unattended-upgrades apt-listchanges

# Enable automatic security updates
sudo dpkg-reconfigure -plow unattended-upgrades
```

### 2. Configure Firewall (UFW)

```bash
# Reset firewall rules
sudo ufw --force reset

# Default policies
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Allow SSH (IMPORTANT: Do this first!)
sudo ufw allow 22/tcp
# Or limit SSH to specific IP (recommended if you have static IP)
# sudo ufw allow from YOUR_HOME_IP to any port 22

# Allow HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Enable firewall
sudo ufw enable

# Check status
sudo ufw status verbose
```

### 3. Secure SSH Access

Edit SSH config:
```bash
sudo nano /etc/ssh/sshd_config
```

Make these changes:
```bash
# Change default port (optional but recommended)
Port 2222  # Use a random high port

# Disable root login
PermitRootLogin no

# Use SSH keys only (disable password authentication)
PasswordAuthentication no
PubkeyAuthentication yes

# Disable empty passwords
PermitEmptyPasswords no

# Limit authentication attempts
MaxAuthTries 3

# Allow only specific users (optional)
AllowUsers your-username

# Disable X11 forwarding
X11Forwarding no

# Set login grace time
LoginGraceTime 60
```

Restart SSH:
```bash
sudo systemctl restart sshd
```

**If you changed SSH port**, update firewall:
```bash
sudo ufw delete allow 22/tcp
sudo ufw allow 2222/tcp
```

### 4. Install and Configure Fail2Ban

```bash
sudo apt install fail2ban -y
```

Create custom config:
```bash
sudo nano /etc/fail2ban/jail.local
```

Add:
```ini
[DEFAULT]
bantime = 3600        # 1 hour ban
findtime = 600        # 10 minutes
maxretry = 3          # 3 attempts

[sshd]
enabled = true
port = 2222           # Use your SSH port
logpath = /var/log/auth.log

[nginx-http-auth]
enabled = true
port = http,https
logpath = /var/log/nginx/error.log

[nginx-limit-req]
enabled = true
port = http,https
filter = nginx-limit-req
logpath = /var/log/nginx/error.log
maxretry = 5

[nginx-botsearch]
enabled = true
port = http,https
filter = nginx-botsearch
logpath = /var/log/nginx/access.log
maxretry = 2

# Django axes integration (optional)
[django-axes]
enabled = true
port = http,https
filter = django-axes
logpath = /var/log/armguard/security.log
maxretry = 3
```

Create Django Axes filter:
```bash
sudo nano /etc/fail2ban/filter.d/django-axes.conf
```

Add:
```ini
[Definition]
failregex = AXES: Repeated login failure.*\[<HOST>\]
ignoreregex =
```

Start Fail2Ban:
```bash
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
sudo fail2ban-client status
```

### 5. Harden Nginx Configuration

Edit `/etc/nginx/nginx.conf`:

```nginx
user www-data;
worker_processes auto;
pid /run/nginx.pid;

events {
    worker_connections 1024;
    use epoll;
}

http {
    # Basic Settings
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 15;
    types_hash_max_size 2048;
    server_tokens off;  # Hide Nginx version
    
    # Buffer Size Limits (prevent buffer overflow attacks)
    client_body_buffer_size 1K;
    client_header_buffer_size 1k;
    client_max_body_size 5m;  # Max upload size
    large_client_header_buffers 2 1k;
    
    # Timeouts
    client_body_timeout 10;
    client_header_timeout 10;
    send_timeout 10;
    
    # Rate Limiting
    limit_req_zone $binary_remote_addr zone=one:10m rate=10r/s;
    limit_req_status 429;
    limit_conn_zone $binary_remote_addr zone=addr:10m;
    
    # Security Headers (global)
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
    
    # SSL Settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    ssl_stapling on;
    ssl_stapling_verify on;
    
    # Gzip Compression
    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css text/xml text/javascript application/json application/javascript application/xml+rss application/rss+xml font/truetype font/opentype application/vnd.ms-fontobject image/svg+xml;
    
    include /etc/nginx/mime.types;
    default_type application/octet-stream;
    
    # Logging
    access_log /var/log/nginx/access.log;
    error_log /var/log/nginx/error.log warn;
    
    # Virtual Host Configs
    include /etc/nginx/conf.d/*.conf;
    include /etc/nginx/sites-enabled/*;
}
```

### 6. Update App-Specific Nginx Config

Edit `/etc/nginx/sites-available/armguard`:

```nginx
# Rate limiting zones (defined in nginx.conf or here)
limit_req_zone $binary_remote_addr zone=login:10m rate=5r/m;  # 5 logins per minute

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

# HTTPS Server
server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;
    
    # SSL Certificates (Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    
    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    
    # Block access to hidden files
    location ~ /\. {
        deny all;
        access_log off;
        log_not_found off;
    }
    
    # Block access to sensitive files
    location ~* \.(ini|conf|bak|sql|old|save)$ {
        deny all;
    }
    
    # Static files (cached)
    location /static/ {
        alias /var/www/armguard/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
        access_log off;
    }
    
    # Media files (with restrictions)
    location /media/ {
        alias /var/www/armguard/media/;
        expires 7d;
        add_header Cache-Control "public";
        
        # Prevent execution of uploaded scripts
        location ~* \.(php|py|pl|sh|cgi)$ {
            deny all;
        }
    }
    
    # Rate limit admin/login pages
    location ~* ^/(admin|secure-portal-x7k2m)/ {
        limit_req zone=login burst=3 nodelay;
        limit_conn addr 5;
        
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_pass http://unix:/run/gunicorn-armguard.sock;
    }
    
    # Main application
    location / {
        limit_req zone=one burst=20 nodelay;
        limit_conn addr 10;
        
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_pass http://unix:/run/gunicorn-armguard.sock;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # Deny access to robots for private app
    location = /robots.txt {
        return 200 "User-agent: *\nDisallow: /\n";
    }
}
```

Test and reload:
```bash
sudo nginx -t
sudo systemctl reload nginx
```

### 7. Set Up SSL with Let's Encrypt

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# Obtain certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Test auto-renewal
sudo certbot renew --dry-run
```

### 8. Enable PostgreSQL (Don't Use SQLite in Production)

```bash
# Install PostgreSQL
sudo apt install postgresql postgresql-contrib -y

# Secure PostgreSQL
sudo -u postgres psql

# In PostgreSQL console:
CREATE DATABASE armguard_db;
CREATE USER armguard_user WITH PASSWORD 'your-strong-random-password';
ALTER ROLE armguard_user SET client_encoding TO 'utf8';
ALTER ROLE armguard_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE armguard_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE armguard_db TO armguard_user;
\q
```

Configure PostgreSQL to only listen locally:
```bash
sudo nano /etc/postgresql/*/main/postgresql.conf
```

Ensure:
```
listen_addresses = 'localhost'
```

Restart PostgreSQL:
```bash
sudo systemctl restart postgresql
```

### 9. Harden File Permissions

```bash
# Application files
sudo chown -R www-data:www-data /var/www/armguard
sudo chmod -R 755 /var/www/armguard

# Restrict .env file
sudo chmod 600 /var/www/armguard/.env
sudo chown www-data:www-data /var/www/armguard/.env

# Database file (if still using SQLite)
sudo chmod 600 /var/www/armguard/db.sqlite3
sudo chown www-data:www-data /var/www/armguard/db.sqlite3

# Media directory (writable but no execution)
sudo chmod 755 /var/www/armguard/media
sudo find /var/www/armguard/media -type f -exec chmod 644 {} \;
sudo find /var/www/armguard/media -type d -exec chmod 755 {} \;

# Static files (read-only)
sudo chmod -R 755 /var/www/armguard/staticfiles
sudo find /var/www/armguard/staticfiles -type f -exec chmod 644 {} \;

# Logs
sudo chmod 750 /var/log/armguard
```

### 10. Configure System Monitoring

Install monitoring tools:
```bash
sudo apt install logwatch aide -y

# Initialize AIDE (file integrity monitoring)
sudo aideinit
sudo mv /var/lib/aide/aide.db.new /var/lib/aide/aide.db

# Configure daily email reports
sudo nano /etc/cron.daily/logwatch
```

Add:
```bash
#!/bin/bash
/usr/sbin/logwatch --output mail --mailto your-email@example.com --detail high
```

Make executable:
```bash
sudo chmod +x /etc/cron.daily/logwatch
```

### 11. Disable Unnecessary Services

```bash
# List running services
systemctl list-units --type=service --state=running

# Disable unused services (examples)
sudo systemctl disable bluetooth
sudo systemctl disable avahi-daemon
sudo systemctl disable cups

# Check open ports
sudo ss -tulpn
```

---

## Part 3: Monitoring and Maintenance

### 1. Set Up Log Monitoring

Create monitoring script `/usr/local/bin/security-check.sh`:
```bash
#!/bin/bash

echo "=== Security Check $(date) ===" >> /var/log/security-check.log

# Check for failed login attempts
echo "Failed SSH logins:" >> /var/log/security-check.log
grep "Failed password" /var/log/auth.log | tail -10 >> /var/log/security-check.log

# Check Fail2Ban status
echo "Fail2Ban banned IPs:" >> /var/log/security-check.log
sudo fail2ban-client status sshd >> /var/log/security-check.log

# Check for suspicious Nginx access
echo "Suspicious Nginx requests:" >> /var/log/security-check.log
grep -E "(\.php|\.asp|\.jsp|sql|script|eval)" /var/log/nginx/access.log | tail -10 >> /var/log/security-check.log

# Check disk usage
echo "Disk usage:" >> /var/log/security-check.log
df -h >> /var/log/security-check.log

echo "===========================" >> /var/log/security-check.log
```

Make executable and schedule:
```bash
sudo chmod +x /usr/local/bin/security-check.sh
sudo crontab -e
```

Add:
```
0 */6 * * * /usr/local/bin/security-check.sh
```

### 2. Regular Backups

Create backup script `/usr/local/bin/backup-armguard.sh`:
```bash
#!/bin/bash

BACKUP_DIR="/backup/armguard"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup database
sudo -u postgres pg_dump armguard_db > $BACKUP_DIR/db_$DATE.sql

# Backup media files
tar -czf $BACKUP_DIR/media_$DATE.tar.gz /var/www/armguard/media/

# Backup .env
cp /var/www/armguard/.env $BACKUP_DIR/env_$DATE

# Keep only last 7 days of backups
find $BACKUP_DIR -type f -mtime +7 -delete

echo "Backup completed: $DATE" >> /var/log/backup.log
```

Schedule daily backups:
```bash
sudo chmod +x /usr/local/bin/backup-armguard.sh
sudo crontab -e
```

Add:
```
0 2 * * * /usr/local/bin/backup-armguard.sh
```

### 3. Monitor Service Health

```bash
# Check all services
sudo systemctl status nginx
sudo systemctl status gunicorn-armguard
sudo systemctl status postgresql
sudo systemctl status fail2ban

# Check logs in real-time
sudo journalctl -u gunicorn-armguard -f
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/armguard/security.log

# Check firewall status
sudo ufw status verbose

# Check Fail2Ban status
sudo fail2ban-client status
```

---

## Part 4: Testing Checklist

Before exposing your app to the internet:

### Application Security
- [ ] `DEBUG = False` in production settings
- [ ] New `SECRET_KEY` generated and set
- [ ] `ALLOWED_HOSTS` configured with your domain
- [ ] All security headers enabled
- [ ] Admin URL obfuscated
- [ ] Rate limiting configured
- [ ] Django Axes installed and configured
- [ ] HTTPS/SSL certificate installed
- [ ] PostgreSQL configured (not SQLite)
- [ ] Static/media files served by Nginx
- [ ] File upload size limits set
- [ ] Session timeouts configured
- [ ] Strong password requirements enforced
- [ ] All dependencies updated (`pip list --outdated`)

### Server Security
- [ ] UFW firewall enabled and configured
- [ ] SSH hardened (key-only, non-standard port)
- [ ] Fail2Ban installed and active
- [ ] Nginx security headers configured
- [ ] Rate limiting enabled in Nginx
- [ ] PostgreSQL listening only on localhost
- [ ] File permissions correctly set
- [ ] Unnecessary services disabled
- [ ] Automatic security updates enabled
- [ ] Log monitoring configured
- [ ] Backup system in place
- [ ] System fully updated

### Monitoring
- [ ] Error logging working
- [ ] Security event logging enabled
- [ ] Log rotation configured
- [ ] Email alerts set up
- [ ] Backup tested and verified
- [ ] Monitoring scripts scheduled

---

## Part 5: Alternative: Use VPN Instead (Recommended)

**Safer option:** Instead of exposing your server to the internet, use a VPN like **Tailscale** for secure remote access.

### Why VPN is Better:
- ✅ No public exposure (zero attack surface)
- ✅ Encrypted tunnel (like being on the same LAN)
- ✅ No port forwarding needed
- ✅ Easy setup (5 minutes)
- ✅ Works from anywhere
- ✅ Free for personal use

### Tailscale Setup:

**On Ubuntu Server:**
```bash
# Install Tailscale
curl -fsSL https://tailscale.com/install.sh | sh

# Authenticate
sudo tailscale up

# Get server's Tailscale IP
tailscale ip -4
```

**On your development machine:**
```bash
# Install Tailscale (Windows/Mac/Linux)
# Download from https://tailscale.com/download

# Sign in with the same account
# Access your server at: http://100.x.x.x (Tailscale IP)
```

**Benefits:**
- Access your LAN app from anywhere securely
- No need for public domain or SSL certificates
- No firewall rule changes needed
- All traffic encrypted automatically

---

## Emergency Response

### If You Detect a Breach:

1. **Immediately block access:**
   ```bash
   sudo ufw deny from <ATTACKER_IP>
   sudo systemctl stop nginx
   ```

2. **Check for unauthorized access:**
   ```bash
   sudo lastlog
   sudo last -a
   grep "Accepted" /var/log/auth.log
   ```

3. **Review application logs:**
   ```bash
   sudo tail -100 /var/log/armguard/security.log
   sudo tail -100 /var/log/nginx/access.log
   ```

4. **Change all passwords:**
   ```bash
   # Django superuser
   python manage.py changepassword admin
   
   # Database password
   sudo -u postgres psql
   ALTER USER armguard_user WITH PASSWORD 'new-password';
   
   # Server user password
   sudo passwd your-username
   ```

5. **Regenerate SECRET_KEY:**
   ```bash
   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   ```

6. **Check for malicious files:**
   ```bash
   sudo find /var/www/armguard -type f -mtime -1  # Files modified in last 24h
   sudo find /var/www/armguard/media -name "*.php" -o -name "*.sh"  # Suspicious uploads
   ```

7. **Restore from backup if needed:**
   ```bash
   sudo systemctl stop gunicorn-armguard
   # Restore database and files from backup
   sudo systemctl start gunicorn-armguard
   ```

---

## Summary

**For temporary online testing:**
1. Follow ALL security steps in this guide
2. Use a non-production domain/subdomain
3. Limit testing period (days, not months)
4. Monitor logs actively during testing
5. Take down when testing is complete

**For long-term online deployment:**
- Consider a complete security audit
- Implement additional layers (CDN, WAF)
- Use managed database service
- Set up proper monitoring and alerting
- Purchase commercial security tools

**Best practice:**
- Use **Tailscale VPN** for remote testing instead of public exposure
- Keep the app on LAN for production use
- Only expose to internet if absolutely necessary

---

**Last Updated:** November 8, 2025
