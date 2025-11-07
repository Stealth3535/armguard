## Ubuntu SSL setup (Nginx + Let's Encrypt)

This guide walks you through enabling HTTPS for your Django app on an Ubuntu Server using Nginx as a reverse proxy and Certbot (Let's Encrypt) for certificates.

Prerequisites
- You have a domain name pointing to your server's public IP (A record).
- Ubuntu Server (20.04 / 22.04 / 24.04 or similar) with sudo access.
- Your Django app is running behind Gunicorn (systemd service) and served by Nginx as a reverse proxy (socket or port).
- Ports 80 and 443 are open in the cloud provider and on the server firewall (ufw) if used.

Overview
1. Install Nginx and Certbot.
2. Create an Nginx server block for your site (HTTP).
3. Obtain and install a certificate with Certbot (automatically updates Nginx to HTTPS).
4. Harden Nginx and enable auto-renewal.
5. Verify Django settings for secure operation behind HTTPS.

1) Install/upate packages

Run on the Ubuntu server:

```bash
sudo apt update
sudo apt install -y nginx python3-certbot-nginx
```

2) Open firewall ports (ufw)

If you use ufw, allow Nginx Full (80 and 443):

```bash
sudo ufw allow 'Nginx Full'
sudo ufw allow OpenSSH
sudo ufw enable
sudo ufw status
```

3) Create or verify your Nginx server block

Create an Nginx config at `/etc/nginx/sites-available/yourdomain.com` (replace `yourdomain.com`). A minimal HTTP config that proxies to Gunicorn on socket or port looks like this:

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    # Redirect all HTTP to HTTPS (Certbot will modify this when enabling SSL)
    location / {
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_pass http://unix:/run/gunicorn.sock; # or http://127.0.0.1:8000
    }

    # Static/media (optional) if served by Nginx
    # location /static/ {
    #     alias /path/to/your/project/static/;
    # }
}
```

Enable and test the config:

```bash
sudo ln -s /etc/nginx/sites-available/yourdomain.com /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

4) Obtain and install a Let's Encrypt certificate (Certbot)

Use Certbot's Nginx plugin to request and automatically configure SSL:

```bash
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

Follow the prompts. Certbot will:
- Obtain the certificate from Let's Encrypt.
- Update your Nginx configuration to serve HTTPS and optionally redirect HTTP to HTTPS.

Notes:
- If Certbot complains about DNS or port 0 not reachable, ensure your domain resolves to the server IP and port 80 is reachable.
- If you're using a non-standard setup (no public DNS or local testing), use `certbot certonly --standalone` or an ACME client like `acme.sh` — but production should use publicly verifiable DNS.

5) Automatic renewal

Certbot installs a cron/systemd timer to renew certificates automatically. Verify with:

```bash
sudo systemctl status certbot.timer
sudo certbot renew --dry-run
```

6) Harden Nginx and security headers (recommended)

Edit your SSL server block (Certbot created a copy in `/etc/nginx/sites-enabled/`) and add headers and HSTS. Example HTTPS server block additions:

```nginx
server {
    listen 443 ssl;
    server_name yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header Referrer-Policy no-referrer-when-downgrade;

    location / {
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_pass http://unix:/run/gunicorn.sock;
    }
}
```

Reload Nginx after changes:

```bash
sudo nginx -t
sudo systemctl reload nginx
```

7) Django production settings checklist (already mostly done in your repo, but confirm):

- In `core/settings.py`:
  - `DEBUG = False`
  - `ALLOWED_HOSTS` includes your domain(s).
  - `SECURE_SSL_REDIRECT = True` (redirect HTTP->HTTPS).
  - `SESSION_COOKIE_SECURE = True`
  - `CSRF_COOKIE_SECURE = True`
  - `SECURE_HSTS_SECONDS = 31536000` (set after initial testing)
  - `SECURE_HSTS_INCLUDE_SUBDOMAINS = True` (optional)
  - `SECURE_HSTS_PRELOAD = True` (only after you understand preload implications)

- Ensure static files are collected and served by Nginx (or a CDN):

```bash
python manage.py collectstatic --noinput
```

8) Gunicorn systemd service (example)

Create `/etc/systemd/system/gunicorn.service` for your project:

```ini
[Unit]
Description=gunicorn daemon
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/path/to/your/project
ExecStart=/path/to/venv/bin/gunicorn --workers 3 --bind unix:/run/gunicorn.sock core.wsgi:application

[Install]
WantedBy=multi-user.target
```

Start and enable:

```bash
sudo systemctl daemon-reload
sudo systemctl start gunicorn
sudo systemctl enable gunicorn
sudo systemctl status gunicorn
```

9) Testing and verification

- Browse to `https://yourdomain.com` and confirm the site loads with a valid certificate.
- Use SSL Labs to test: https://www.ssllabs.com/ssltest/ (enter your domain).
- Check `sudo certbot renew --dry-run` to verify renewal.

Troubleshooting
- "Connection refused" or port 80 issues: ensure Nginx is running and firewall/cloud provider rules allow 80/443.
- DNS not resolving: verify your A record points to the server IP.
- Certbot fails due to another service on port 80: stop the conflicting service temporarily or use `--http-01-port`/`--standalone`.

Advanced options
- Use `--nginx` plugin for automated Nginx edits (recommended).
- Use DNS challenge for wildcard certificates (requires API access to DNS provider): `certbot -d "*.example.com" --dns-cloudflare`.
- For private/internal deployments without public DNS, consider a trusted internal CA or a reverse proxy on a public host.

Notes & safety
- Let's Encrypt certificates last 90 days. Certbot auto-renewal should handle this. Monitor renewal via logs/alerts.
- Do not enable HSTS preload until you fully control all subdomains and understand effects.

If you want, I can:
- Create a ready-to-use Nginx server block file with placeholders filled from your `core/settings.py` (ALLOWED_HOSTS).
- Add a `deploy/` folder with systemd service examples, scripts to obtain certs, and a small checklist for you or your server operator.

--
Created: automated helper
