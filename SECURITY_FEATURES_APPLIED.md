# Security Features Applied

## ✅ Security Measures Implemented

This document outlines all security features that have been applied to ArmGuard, making it production-ready for both local and online deployments.

---

## 1. Application Security

### ✅ Django Axes (Brute-Force Protection)
- **Status:** Installed and configured
- **Feature:** Blocks accounts after 5 failed login attempts
- **Cooloff Time:** 1 hour (configurable via `.env`)
- **Tracking:** Locks by username AND IP address combination
- **Template:** Custom "Account Locked" page created

**Configuration:**
```python
AXES_ENABLED = True
AXES_FAILURE_LIMIT = 5  # Configurable in .env
AXES_COOLOFF_TIME = 1   # Hours
```

### ✅ Rate Limiting
- **Status:** Custom middleware implemented
- **Feature:** Limits requests per IP address to prevent abuse
- **Default:** 60 requests per minute per IP
- **Scope:** Global rate limiting with exemptions for admin users

**Configuration:**
```python
RATELIMIT_ENABLE = True
RATELIMIT_REQUESTS_PER_MINUTE = 60  # Configurable in .env
```

### ✅ Admin URL Obfuscation
- **Status:** Implemented with environment variable
- **Default:** `/superadmin/`
- **Production:** Set custom random URL in `.env` (e.g., `/secret-portal-x7k2m/`)
- **Security Benefit:** Prevents automated bot attacks on `/admin/`

**Configuration:**
```env
DJANGO_ADMIN_URL=your-random-string-here
```

### ✅ Enhanced Password Validation
- **Minimum Length:** 8 characters (configurable, recommended 12+ for production)
- **Validators:**
  - User attribute similarity check
  - Common password check
  - Numeric-only password prevention
  
**Configuration:**
```env
PASSWORD_MIN_LENGTH=12  # Set higher for production
```

### ✅ Security Headers
Multiple security headers implemented via custom middleware:

- `X-Frame-Options: DENY` - Clickjacking protection
- `X-Content-Type-Options: nosniff` - MIME type sniffing prevention
- `X-XSS-Protection: 1; mode=block` - XSS filter
- `Referrer-Policy: same-origin` - Referrer control
- `Permissions-Policy` - Feature restrictions (camera, microphone, geolocation, etc.)
- `Content-Security-Policy` - Script execution control
- `Strict-Transport-Security` - HTTPS enforcement (when DEBUG=False)

### ✅ File Upload Security
- **Maximum file size:** 5MB (configurable)
- **Permissions:** Files: 644, Directories: 755
- **Restrictions:** Prevents execution of uploaded scripts in media directory

**Configuration:**
```env
FILE_UPLOAD_MAX_MEMORY_SIZE=5242880  # 5MB in bytes
DATA_UPLOAD_MAX_MEMORY_SIZE=5242880
```

### ✅ Session Security
- **Cookie Security:** HTTPOnly, Secure (in production), SameSite
- **Session Timeout:** 1 hour (configurable)
- **Auto-logout:** Session expires on browser close
- **CSRF Protection:** Enhanced with SameSite cookies

**Configuration:**
```env
SESSION_COOKIE_AGE=3600  # 1 hour in seconds
```

### ✅ CSRF Protection
- **Status:** Enhanced with stricter settings
- **HTTPOnly Cookies:** Enabled
- **SameSite:** Set to 'Lax' (upgrade to 'Strict' for higher security)
- **Trusted Origins:** Configurable for cross-domain requests

**Configuration:**
```env
CSRF_TRUSTED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

---

## 2. Database Security

### ✅ PostgreSQL Support
- **Status:** Configured (optional, recommended for production)
- **Connection Pooling:** Enabled (CONN_MAX_AGE=600)
- **Default:** SQLite for development, PostgreSQL for production

**Configuration:**
```env
USE_POSTGRESQL=True  # Enable for production
DB_NAME=armguard_db
DB_USER=armguard_user
DB_PASSWORD=your-strong-password
DB_HOST=localhost
DB_PORT=5432
```

---

## 3. Logging & Monitoring

### ✅ Comprehensive Logging
- **Security Log:** Tracks authentication failures, suspicious activity
- **Error Log:** Application errors and exceptions
- **Django Log:** General application activity
- **Rotation:** 10MB max size, 5 backup files

**Log Files:**
- `logs/security.log` - Security events (Django Axes, failed logins)
- `logs/errors.log` - Application errors
- `logs/django.log` - General Django logs

### ✅ Log Monitoring
- Failed login attempts tracked
- IP addresses logged
- User agent strings captured
- Automatic log rotation to prevent disk space issues

---

## 4. Production Settings

### ✅ `settings_production.py` Created
- **Purpose:** Complete production configuration
- **Inherits:** Base settings from `settings.py`
- **Overrides:** Security-critical settings for production

**Key Features:**
- `DEBUG = False` enforced
- All HTTPS/SSL settings enabled
- Enhanced logging configuration
- Email notifications (optional)
- Rate limiting and Axes configuration
- Content Security Policy

**Usage:**
```bash
export DJANGO_SETTINGS_MODULE=core.settings_production
# or in .env
DJANGO_SETTINGS_MODULE=core.settings_production
```

---

## 5. Middleware Stack

### ✅ Custom Security Middleware
Four custom middleware classes implemented:

1. **RateLimitMiddleware**
   - Global rate limiting
   - Exempts authenticated staff users
   - Returns 429 Too Many Requests on limit

2. **SecurityHeadersMiddleware**
   - Adds additional security headers
   - Permissions Policy
   - Expect-CT header
   - Removes server fingerprinting

3. **AdminIPWhitelistMiddleware** (Optional)
   - Restricts admin access to specific IPs
   - Configurable via `ADMIN_ALLOWED_IPS`
   - Disabled by default

4. **StripSensitiveHeadersMiddleware**
   - Removes potentially sensitive headers
   - Prevents information disclosure

---

## 6. Additional Security Files

### ✅ robots.txt
- **Location:** `core/static/robots.txt`
- **Purpose:** Prevents search engine indexing
- **Content:** Disallows all crawlers

### ✅ Account Locked Template
- **Location:** `core/templates/registration/account_locked.html`
- **Purpose:** User-friendly lockout notification
- **Features:** Explains lockout reason, duration, next steps

---

## 7. Environment Variables

### ✅ Updated `.env.example`
Comprehensive configuration file with 50+ settings organized by category:

- **Django Core Settings**
- **Security Settings**
- **Database Configuration**
- **Logging Configuration**
- **Email Configuration**
- **Admin Customization**
- **Advanced Security Options**

**To Use:**
```bash
cp .env.example .env
nano .env  # Edit with your values
```

---

## 8. Package Dependencies

### ✅ Security Packages Added to `requirements.txt`
- `django-ratelimit>=4.1.0` - View-level rate limiting
- `django-axes>=6.1.1` - Failed login tracking and blocking
- `psycopg2-binary>=2.9.9` - PostgreSQL adapter

---

## How to Use These Features

### For Local Development (Current Setup)
All security features are **enabled but lenient**:
- DEBUG=True (development mode)
- Rate limiting: 60 req/min (comfortable for testing)
- Password minimum: 8 characters
- Axes enabled but with 5 attempts before lockout
- SQLite database (no PostgreSQL needed)

**No changes needed** - your app is already secure for local use!

### For Online Testing/Production

**1. Update `.env` file:**
```env
# Core settings
DJANGO_DEBUG=False
DJANGO_SETTINGS_MODULE=core.settings_production
DJANGO_ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Security
DJANGO_ADMIN_URL=secret-portal-abc123xyz
PASSWORD_MIN_LENGTH=12
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_HSTS_SECONDS=31536000

# Database (recommended for production)
USE_POSTGRESQL=True
DB_NAME=armguard_db
DB_USER=armguard_user
DB_PASSWORD=your-strong-random-password

# Generate new secret key
DJANGO_SECRET_KEY=<paste-generated-key-here>
```

**2. Generate a new SECRET_KEY:**
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

**3. Run with production settings:**
```bash
python manage.py check --deploy --settings=core.settings_production
python manage.py migrate --settings=core.settings_production
python manage.py collectstatic --noinput --settings=core.settings_production
```

**4. Follow server hardening guide:**
See `SECURITY_ONLINE_TESTING.md` for:
- Nginx configuration
- UFW firewall setup
- Fail2Ban installation
- SSH hardening
- SSL/HTTPS setup

---

## Security Testing

### Test Django Axes
1. Go to login page
2. Enter wrong password 5 times
3. Account should be locked for 1 hour
4. See custom "Account Locked" page

### Test Rate Limiting
1. Make 61+ requests in 1 minute from same IP
2. Should receive "429 Too Many Requests" error
3. Wait 1 minute, rate limit resets

### Test Admin URL Obfuscation
1. Try accessing `/admin/` → Should get 404
2. Access your configured URL (e.g., `/superadmin/`)
3. In production, set random URL in `.env`

### Test Security Headers
```bash
curl -I https://yourdomain.com
# Check for X-Frame-Options, X-Content-Type-Options, etc.
```

---

## Deployment Checklist

Before going online:

- [ ] `DEBUG = False` in `.env`
- [ ] New `SECRET_KEY` generated
- [ ] `ALLOWED_HOSTS` configured
- [ ] Admin URL changed to random string
- [ ] Password minimum set to 12+
- [ ] PostgreSQL configured (not SQLite)
- [ ] HTTPS/SSL enabled
- [ ] All security headers verified
- [ ] Firewall configured (UFW)
- [ ] Fail2Ban installed
- [ ] SSH hardened
- [ ] Logs directory created and writable
- [ ] `robots.txt` in place
- [ ] Backup system configured

---

## Documentation References

- **Complete Security Guide:** `SECURITY_ONLINE_TESTING.md`
- **Server Setup:** `UBUNTU_MKCERT_SSL_SETUP.md`
- **Deployment Guide:** `DEPLOYMENT_GUIDE.md`
- **Quick Install:** `UBUNTU_INSTALL.md`

---

## Summary

✅ **Your app is now production-ready with enterprise-level security:**

- **Authentication:** Brute-force protection, account lockouts
- **Network:** Rate limiting, DDoS mitigation
- **Headers:** 10+ security headers configured
- **Data:** File upload restrictions, CSRF protection
- **Monitoring:** Comprehensive logging system
- **Obfuscation:** Hidden admin URLs
- **Sessions:** Secure, timeout-based
- **Database:** PostgreSQL support for production

**All features work seamlessly for both:**
- Local development (lenient, developer-friendly)
- Online production (strict, maximum security)

---

**Last Updated:** November 8, 2025
