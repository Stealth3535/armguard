# Ubuntu SSL Setup with mkcert (for LAN/Local Deployments)

This guide shows you how to set up **secure HTTPS** for your Django app on a **local network (LAN)** using **mkcert**, a tool that creates locally-trusted SSL certificates. Perfect for accessing your app via private IPs (e.g., `192.168.1.100` or `armguard.local`) without needing a public domain.

---

## Why mkcert for LAN?

| Feature | mkcert | Let's Encrypt |
|---------|--------|---------------|
| Works on LAN/private IPs | ✅ Yes | ❌ No (requires public domain) |
| HTTPS encryption | ✅ Full TLS 1.2/1.3 | ✅ Full TLS 1.2/1.3 |
| Browser trust | One-time CA install per device | Automatic (globally trusted) |
| Setup complexity | Low | Medium |
| Best for | LAN, dev, internal networks | Public internet deployments |

---

## Prerequisites

- **Ubuntu Server** (20.04/22.04/24.04) with sudo access
- **Django app** code deployed (follow [UBUNTU_INSTALL.md](./UBUNTU_INSTALL.md) for initial setup)
- **Python virtual environment** with dependencies installed
- Devices on the same network that will access the app (Windows PCs, Android/iOS devices)

---

## Part 1: Server Setup (Ubuntu)

### 1) Install Nginx and dependencies

```bash
# Update package list
sudo apt update

# Install Nginx, Python, and required tools
sudo apt install -y nginx python3-pip python3-venv wget libnss3-tools

# Start and enable Nginx
sudo systemctl start nginx
sudo systemctl enable nginx

# Check status
sudo systemctl status nginx
```

### 2) Install Gunicorn in your virtual environment

```bash
# Navigate to your project directory
cd /path/to/your/project

# Activate virtual environment
source venv/bin/activate

# Install Gunicorn
pip install gunicorn

# Test Gunicorn (optional - stop with Ctrl+C)
gunicorn --bind 0.0.0.0:8000 core.wsgi:application
```

### 3) Create Gunicorn systemd service

Create `/etc/systemd/system/gunicorn.service`:

```bash
sudo nano /etc/systemd/system/gunicorn.service
```

Add the following content (adjust paths to match your setup):

```ini
[Unit]
Description=gunicorn daemon for armguard
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/home/your-username/armguard
Environment="PATH=/home/your-username/armguard/venv/bin"
ExecStart=/home/your-username/armguard/venv/bin/gunicorn \
          --workers 3 \
          --bind unix:/run/gunicorn.sock \
          core.wsgi:application

[Install]
WantedBy=multi-user.target
```

**Important**: Replace `/home/your-username/armguard` with your actual project path.

Create the socket directory and set permissions:

```bash
# Create socket directory
sudo mkdir -p /run/gunicorn

# Set ownership
sudo chown www-data:www-data /run/gunicorn

# Give project directory access to www-data
sudo chown -R www-data:www-data /path/to/your/project

# Start and enable Gunicorn
sudo systemctl daemon-reload
sudo systemctl start gunicorn
sudo systemctl enable gunicorn

# Check status
sudo systemctl status gunicorn

# Verify socket created
ls -l /run/gunicorn.sock
```

### 4) Install mkcert

```bash
# Download and install mkcert (latest version - check GitHub for updates)
wget https://github.com/FiloSottile/mkcert/releases/download/v1.4.4/mkcert-v1.4.4-linux-amd64
sudo mv mkcert-v1.4.4-linux-amd64 /usr/local/bin/mkcert
sudo chmod +x /usr/local/bin/mkcert

# Verify installation
mkcert -version
```

### 5) Create a local Certificate Authority (CA)

```bash
# Generate the local CA (creates rootCA.pem and rootCA-key.pem in ~/.local/share/mkcert)
mkcert -install

# Show the CA certificate location (you'll need this file for client devices)
mkcert -CAROOT
```

**Important**: The CA certificate file is located at `~/.local/share/mkcert/rootCA.pem`. You will copy this file to client devices later.

### 6) Generate SSL certificate for your LAN IP or hostname

Choose **one** of the following based on how you'll access the app:

**Option A: Using LAN IP address** (e.g., `192.168.1.100`)
```bash
# Replace 192.168.1.100 with your server's actual LAN IP
mkcert 192.168.1.100 localhost 127.0.0.1
```

**Option B: Using local hostname** (e.g., `armguard.local`)
```bash
# If you set up .local mDNS or a local DNS entry
mkcert armguard.local localhost 127.0.0.1
```

**Option C: Both IP and hostname**
```bash
mkcert 192.168.1.100 armguard.local localhost 127.0.0.1
```

This creates two files in the current directory:
- `192.168.1.100+2.pem` (or similar name) - the certificate
- `192.168.1.100+2-key.pem` - the private key

### 7) Move certificates to a secure location

```bash
# Create SSL directory
sudo mkdir -p /etc/ssl/armguard

# Move certificates (adjust filenames if different)
sudo mv 192.168.1.100+*.pem /etc/ssl/armguard/
sudo mv 192.168.1.100+*-key.pem /etc/ssl/armguard/

# Set proper permissions
sudo chmod 644 /etc/ssl/armguard/*.pem
sudo chmod 600 /etc/ssl/armguard/*-key.pem
sudo chown root:root /etc/ssl/armguard/*

# Verify files
ls -lh /etc/ssl/armguard/
```

### 8) Configure Nginx for HTTPS

Edit your Nginx server block (e.g., `/etc/nginx/sites-available/armguard`):

```bash
sudo nano /etc/nginx/sites-available/armguard
```

Add the following configuration (replace IP/hostname and paths as needed):

```nginx
# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name 192.168.1.100;  # Replace with your IP or hostname
    return 301 https://$server_name$request_uri;
}

# HTTPS server block
server {
    listen 443 ssl http2;
    server_name 192.168.1.100;  # Replace with your IP or hostname

    # SSL certificate paths (adjust filenames to match your generated files)
    ssl_certificate /etc/ssl/armguard/192.168.1.100+2.pem;
    ssl_certificate_key /etc/ssl/armguard/192.168.1.100+2-key.pem;

    # Modern SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384';
    ssl_prefer_server_ciphers off;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header Referrer-Policy no-referrer-when-downgrade;

    # Proxy to Gunicorn
    location / {
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_pass http://unix:/run/gunicorn.sock;  # or http://127.0.0.1:8000
    }

    # Static files (optional - if served by Nginx)
    location /static/ {
        alias /path/to/your/project/staticfiles/;
        expires 30d;
    }

    # Media files (optional)
    location /media/ {
        alias /path/to/your/project/media/;
        expires 30d;
    }
}
```

Enable the site and test:

```bash
# Remove default site (optional)
sudo rm /etc/nginx/sites-enabled/default

# Enable your site
sudo ln -sf /etc/nginx/sites-available/armguard /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx
```

### 9) Configure firewall (ufw)

```bash
# Allow HTTP and HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow OpenSSH

# Enable firewall
sudo ufw enable

# Check status
sudo ufw status
```

### 10) Update Django settings

In `core/settings.py`, ensure these are set:

```python
# In production .env:
DEBUG=False
ALLOWED_HOSTS=192.168.1.100,armguard.local,localhost

# Security settings (already in your settings.py)
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000  # 1 year
```

Collect static files and restart Gunicorn:

```bash
# Activate virtual environment
source /path/to/your/project/venv/bin/activate

# Collect static files
python manage.py collectstatic --noinput

# Restart Gunicorn
sudo systemctl restart gunicorn

# Check logs if issues occur
sudo journalctl -u gunicorn -f
```

### 11) Verify the deployment

```bash
# Check all services are running
sudo systemctl status nginx
sudo systemctl status gunicorn

# Test HTTPS locally from the server
curl -I https://192.168.1.100

# Check Nginx logs if needed
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/access.log
```

---

## Part 2: Client Setup (Install CA Certificate)

To avoid browser security warnings, install the mkcert CA certificate on **every device** that will access the app.

### Copy the CA certificate from the server

On the Ubuntu server, copy the CA file to a location accessible to clients:

```bash
# Option 1: Copy to a USB drive
cp ~/.local/share/mkcert/rootCA.pem /media/usb/armguard-ca.pem

# Option 2: Serve temporarily via Python HTTP server
cd ~/.local/share/mkcert/
python3 -m http.server 8888
# Access from client: http://192.168.1.100:8888/rootCA.pem
# Stop server with Ctrl+C after downloading
```

---

### Windows 10/11

1. **Download** `rootCA.pem` from the server (rename to `armguard-ca.crt` if desired)

2. **Install the certificate**:
   - Double-click `rootCA.pem` (or `armguard-ca.crt`)
   - Click **Install Certificate**
   - Select **Local Machine** → **Next**
   - Select **Place all certificates in the following store** → **Browse**
   - Choose **Trusted Root Certification Authorities** → **OK**
   - Click **Next** → **Finish**
   - Confirm the security warning

3. **Verify**: Open Chrome/Edge and navigate to `https://192.168.1.100` (or your hostname). You should see a green padlock.

**Alternative (PowerShell - Run as Administrator)**:
```powershell
# Import the CA certificate
Import-Certificate -FilePath "C:\path\to\rootCA.pem" -CertStoreLocation Cert:\LocalMachine\Root
```

---

### Android

1. **Download** `rootCA.pem` to your Android device (via browser or USB transfer)

2. **Install the CA**:
   - Go to **Settings** → **Security** (or **Biometrics and Security**)
   - Scroll down to **Encryption & credentials** → **Install a certificate**
   - Select **CA certificate**
   - Tap **Install anyway** (warning appears)
   - Browse and select `rootCA.pem`
   - Enter your PIN/password if prompted

3. **Verify**:
   - Open Chrome and navigate to `https://192.168.1.100`
   - You should see a secure connection (padlock)

**Note**: On Android 11+, user-installed CAs may not be trusted by all apps. For full system trust, you may need root access or use Chrome/Firefox which respect user CAs.

---

### iOS (iPhone/iPad)

1. **Download** `rootCA.pem` to your iOS device (via AirDrop, email, or Safari from the server)

2. **Install the profile**:
   - When you download the file, iOS prompts "Profile Downloaded"
   - Go to **Settings** → **General** → **VPN & Device Management** (or **Profiles**)
   - Tap **armguard CA** (or the profile name)
   - Tap **Install** (upper right)
   - Enter your passcode
   - Tap **Install** again (warning appears) → **Install** (confirm)

3. **Enable full trust**:
   - Go to **Settings** → **General** → **About** → **Certificate Trust Settings**
   - Enable the switch for **mkcert** CA
   - Tap **Continue** on the warning

4. **Verify**:
   - Open Safari and navigate to `https://192.168.1.100`
   - You should see a secure connection

---

### macOS

1. **Download** `rootCA.pem` to your Mac

2. **Install via Keychain Access**:
   - Double-click `rootCA.pem`
   - Select **System** keychain → **Add**
   - Open **Keychain Access** app
   - Find the certificate (search for "mkcert")
   - Double-click → **Trust** section
   - Set **When using this certificate** to **Always Trust**
   - Close and enter your password

3. **Verify**: Open Safari/Chrome and navigate to `https://192.168.1.100`

---

### Linux (Ubuntu/Debian Desktop)

```bash
# Copy CA certificate
sudo cp rootCA.pem /usr/local/share/ca-certificates/armguard-ca.crt

# Update CA trust store
sudo update-ca-certificates

# Restart browser or system
```

For Firefox specifically:
1. Open Firefox → **Settings** → **Privacy & Security**
2. Scroll to **Certificates** → **View Certificates**
3. **Authorities** tab → **Import**
4. Select `rootCA.pem` → Check **Trust this CA to identify websites**

---

## Troubleshooting

### "Your connection is not private" warning
- **Cause**: CA certificate not installed on the client device
- **Fix**: Follow the client setup instructions above

### Certificate name mismatch
- **Cause**: Accessing via a different IP/hostname than the one in the certificate
- **Fix**: Regenerate the certificate with all IPs/hostnames you'll use:
  ```bash
  mkcert 192.168.1.100 192.168.1.200 armguard.local localhost 127.0.0.1
  ```

### Nginx won't start / SSL errors
- **Check certificate paths** in Nginx config match the actual file locations
- **Check file permissions**: cert should be 644, key should be 600
- **Check logs**: `sudo tail -f /var/log/nginx/error.log`

### Can't access from other devices
- **Firewall**: Ports 80 and 443 should already be open (step 9)
- **Verify server IP**: `ip addr show` or `hostname -I`
- **Test connectivity**: From client, `ping 192.168.1.100`

### Gunicorn service issues
- **Check status**: `sudo systemctl status gunicorn`
- **View logs**: `sudo journalctl -u gunicorn -n 50`
- **Check socket**: `ls -l /run/gunicorn.sock`
- **Permissions**: Ensure www-data owns the project directory

### Static files not loading
- **Run collectstatic**: `python manage.py collectstatic --noinput`
- **Check Nginx config**: Verify `/static/` location matches your `STATIC_ROOT`
- **Permissions**: `sudo chown -R www-data:www-data /path/to/staticfiles/`

---

## Security Notes

- **CA private key**: The file `~/.local/share/mkcert/rootCA-key.pem` is **very sensitive**. Anyone with this file can create trusted certificates for your devices. Keep it secure on the server.
- **LAN only**: This setup is for local networks. Don't expose port 443 to the public internet without additional security (VPN, fail2ban, etc.).
- **Certificate rotation**: mkcert certificates are valid for 10+ years. If compromised, regenerate:
  ```bash
  mkcert -uninstall  # Remove old CA
  mkcert -install    # Create new CA
  # Regenerate certificates and reinstall CA on all clients
  ```

---

## Advanced: Hosting Multiple Apps with .local Domains

Instead of using IP addresses, you can host **multiple web applications** on the same server using `.local` mDNS hostnames with Nginx as a reverse proxy. This gives you clean URLs like `https://armguard.local`, `https://app2.local`, etc.

### Why use mkcert + Nginx together?

| Component | Purpose |
|-----------|---------|
| **mkcert** | Generates trusted HTTPS certificates for local domains |
| **Nginx** | Routes traffic to multiple apps, serves HTTPS using mkcert certs |
| **Avahi/mDNS** | Makes `.local` domains discoverable on your network |

### Setup: Multiple Apps on One Server

#### 1) Install Avahi for .local domain resolution

```bash
sudo apt install avahi-daemon
sudo systemctl enable avahi-daemon
sudo systemctl start avahi-daemon

# Set your server hostname
sudo hostnamectl set-hostname armguard
```

Now your server is accessible at `armguard.local` from any device on the network.

#### 2) Generate certificates for each app

```bash
# Generate a wildcard cert for multiple subdomains (recommended)
mkcert "*.local" localhost 127.0.0.1

# OR generate individual certs for each app
mkcert armguard.local inventory.local personnel.local localhost 127.0.0.1
```

Move certificates to secure location:
```bash
sudo mkdir -p /etc/ssl/local-apps
sudo mv *.local*.pem /etc/ssl/local-apps/
sudo chmod 644 /etc/ssl/local-apps/*.pem
sudo chmod 600 /etc/ssl/local-apps/*-key.pem
```

#### 3) Configure Nginx for multiple apps

Create separate server blocks for each app:

**App 1: Armguard Django app** (`/etc/nginx/sites-available/armguard.local`):
```nginx
server {
    listen 80;
    server_name armguard.local;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name armguard.local;

    ssl_certificate /etc/ssl/local-apps/_local.pem;
    ssl_certificate_key /etc/ssl/local-apps/_local-key.pem;

    # Modern SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers off;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;

    # Proxy to Gunicorn
    location / {
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_pass http://unix:/run/gunicorn-armguard.sock;
    }

    location /static/ {
        alias /home/user/armguard/staticfiles/;
        expires 30d;
    }

    location /media/ {
        alias /home/user/armguard/media/;
        expires 30d;
    }
}
```

**App 2: Another Django/Flask/Node.js app** (`/etc/nginx/sites-available/inventory.local`):
```nginx
server {
    listen 80;
    server_name inventory.local;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name inventory.local;

    ssl_certificate /etc/ssl/local-apps/_local.pem;
    ssl_certificate_key /etc/ssl/local-apps/_local-key.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers off;

    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;

    location / {
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_pass http://localhost:8080;  # Different app on port 8080
    }
}
```

Enable all sites:
```bash
sudo ln -sf /etc/nginx/sites-available/armguard.local /etc/nginx/sites-enabled/
sudo ln -sf /etc/nginx/sites-available/inventory.local /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

#### 4) Create separate Gunicorn services for each Django app

For the armguard app, modify the systemd service to use a unique socket:

`/etc/systemd/system/gunicorn-armguard.service`:
```ini
[Unit]
Description=gunicorn daemon for armguard
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/home/user/armguard
Environment="PATH=/home/user/armguard/venv/bin"
ExecStart=/home/user/armguard/venv/bin/gunicorn \
          --workers 3 \
          --bind unix:/run/gunicorn-armguard.sock \
          core.wsgi:application

[Install]
WantedBy=multi-user.target
```

For a second Django app:

`/etc/systemd/system/gunicorn-inventory.service`:
```ini
[Unit]
Description=gunicorn daemon for inventory
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/home/user/inventory-app
Environment="PATH=/home/user/inventory-app/venv/bin"
ExecStart=/home/user/inventory-app/venv/bin/gunicorn \
          --workers 2 \
          --bind unix:/run/gunicorn-inventory.sock \
          inventory.wsgi:application

[Install]
WantedBy=multi-user.target
```

Start both services:
```bash
sudo systemctl daemon-reload
sudo systemctl start gunicorn-armguard
sudo systemctl start gunicorn-inventory
sudo systemctl enable gunicorn-armguard
sudo systemctl enable gunicorn-inventory
```

#### 5) Update Django ALLOWED_HOSTS for each app

In each app's `settings.py`:
```python
# armguard/core/settings.py
ALLOWED_HOSTS = ['armguard.local', '192.168.1.100', 'localhost']

# inventory-app/inventory/settings.py
ALLOWED_HOSTS = ['inventory.local', '192.168.1.100', 'localhost']
```

#### 6) Add local DNS entries on client devices

Since mDNS only resolves the server's hostname (e.g., `armguard.local`), you need to map additional `.local` domains on **client devices**:

**Windows** (edit `C:\Windows\System32\drivers\etc\hosts` as Administrator):
```
192.168.1.100   armguard.local
192.168.1.100   inventory.local
192.168.1.100   personnel.local
```

**macOS/Linux** (edit `/etc/hosts` with sudo):
```
192.168.1.100   armguard.local
192.168.1.100   inventory.local
192.168.1.100   personnel.local
```

**Android/iOS**: Use a DNS manager app or configure static DNS entries (more complex, hosts file method recommended for desktop only).

#### 7) Access your apps

Now you can access:
- 🔹 `https://armguard.local` - Main armguard Django app
- 🔹 `https://inventory.local` - Second app
- 🔹 `https://personnel.local` - Third app

All with **trusted HTTPS certificates** and **no browser warnings** (after installing the mkcert CA on clients).

### Summary: Multi-App Architecture

```
┌─────────────────────────────────────────────────────┐
│  Client Devices (Windows, Android, iOS, macOS)      │
│  - CA installed (rootCA.pem)                        │
│  - /etc/hosts entries for .local domains            │
└────────────────┬────────────────────────────────────┘
                 │
                 │ HTTPS (443)
                 │
┌────────────────▼────────────────────────────────────┐
│  Ubuntu Server (192.168.1.100)                      │
│  ┌──────────────────────────────────────────────┐  │
│  │  Nginx (Reverse Proxy)                       │  │
│  │  - Listens on port 443 (HTTPS)               │  │
│  │  - Routes by server_name (armguard.local,    │  │
│  │    inventory.local, etc.)                    │  │
│  │  - Uses mkcert certificates                  │  │
│  └────┬─────────────────┬────────────────┬──────┘  │
│       │                 │                │          │
│  ┌────▼─────┐     ┌─────▼──────┐   ┌────▼──────┐  │
│  │ Gunicorn │     │ Gunicorn   │   │ Node.js/  │  │
│  │ armguard │     │ inventory  │   │ Flask app │  │
│  │ :sock    │     │ :8080      │   │ :3000     │  │
│  └──────────┘     └────────────┘   └───────────┘  │
└─────────────────────────────────────────────────────┘
```

**Benefits**:
- ✅ Clean URLs for each app
- ✅ Single server, single port (443)
- ✅ All apps use HTTPS with trusted certs
- ✅ Easy to add/remove apps (just add Nginx config)
- ✅ Isolated services (each app has own Gunicorn/process)

---

## Performance Optimization for Multiple Apps

Running multiple web apps on a single server (especially on limited hardware like Raspberry Pi) requires optimization to ensure smooth performance.

### 1. Optimize Nginx as a Reverse Proxy

**Enable compression and buffering** in `/etc/nginx/nginx.conf` (inside `http` block):

```nginx
http {
    # Gzip compression
    gzip on;
    gzip_comp_level 5;
    gzip_min_length 256;
    gzip_types
        text/plain
        text/css
        text/javascript
        application/json
        application/javascript
        application/x-javascript
        text/xml
        application/xml
        application/xml+rss;

    # Proxy buffering
    proxy_buffering on;
    proxy_buffers 16 4k;
    proxy_buffer_size 2k;

    # Connection optimizations
    keepalive_timeout 65;
    keepalive_requests 100;

    # ... rest of config
}
```

**Serve static files directly from Nginx** (don't let Django/Flask handle them):

```nginx
server {
    listen 443 ssl http2;
    server_name armguard.local;

    # Static files - served by Nginx (fast!)
    location /static/ {
        alias /home/user/armguard/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        alias /home/user/armguard/media/;
        expires 7d;
    }

    # Dynamic content - proxied to Gunicorn
    location / {
        proxy_pass http://unix:/run/gunicorn-armguard.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Apply changes:
```bash
sudo nginx -t
sudo systemctl reload nginx
```

### 2. Limit Gunicorn Workers and Threads

**Don't over-provision workers** — use the formula: `(2 × CPU cores) + 1`

For a 4-core Raspberry Pi:
```bash
# In /etc/systemd/system/gunicorn-armguard.service
ExecStart=/path/to/venv/bin/gunicorn \
          --workers 3 \
          --threads 2 \
          --timeout 120 \
          --bind unix:/run/gunicorn-armguard.sock \
          core.wsgi:application
```

For lighter apps or limited RAM:
```bash
ExecStart=/path/to/venv/bin/gunicorn \
          --workers 2 \
          --threads 2 \
          --max-requests 1000 \
          --max-requests-jitter 50 \
          --bind unix:/run/gunicorn-inventory.sock \
          inventory.wsgi:application
```

**`--max-requests`**: Restart worker after N requests (prevents memory leaks)

Reload after changes:
```bash
sudo systemctl daemon-reload
sudo systemctl restart gunicorn-armguard
```

### 3. Use Lightweight Databases

**For small to medium apps**:
- ✅ **SQLite** (default Django) — no separate server process, low overhead
- ✅ **TinyDB** (Python JSON DB) — for simple data
- ❌ Avoid PostgreSQL/MySQL unless you need multi-user concurrency or large datasets

**If using PostgreSQL/MySQL**, limit memory usage:

PostgreSQL (`/etc/postgresql/*/main/postgresql.conf`):
```ini
shared_buffers = 128MB          # Lower for limited RAM
effective_cache_size = 512MB
work_mem = 4MB
maintenance_work_mem = 64MB
max_connections = 20            # Limit connections
```

MySQL (`/etc/mysql/mysql.conf.d/mysqld.cnf`):
```ini
innodb_buffer_pool_size = 128M  # Lower for limited RAM
max_connections = 50
```

Restart database after changes:
```bash
sudo systemctl restart postgresql  # or mysql
```

### 4. Enable Swap File (Safety Net for RAM Spikes)

**On Raspberry Pi or low-RAM servers**, add swap to prevent crashes:

```bash
# Check current swap
free -h

# Configure swap (Raspberry Pi)
sudo dphys-swapfile swapoff
sudo nano /etc/dphys-swapfile
```

Edit `CONF_SWAPSIZE`:
```
CONF_SWAPSIZE=1024  # 1GB swap (adjust based on your needs)
```

Apply:
```bash
sudo dphys-swapfile setup
sudo dphys-swapfile swapon
free -h  # Verify swap is active
```

**For Ubuntu Server** (non-Raspberry Pi):
```bash
# Create 2GB swap file
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Make permanent
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# Verify
free -h
```

⚠️ **Note**: Swap on SD cards is slower than RAM but prevents out-of-memory crashes.

### 5. Monitor and Clean System Resources

**Install monitoring tools**:
```bash
sudo apt install htop iotop
```

**Monitor in real-time**:
```bash
htop           # CPU, RAM, processes
iotop          # Disk I/O
sudo journalctl -u gunicorn-armguard -f  # App logs
```

**Clean up unused packages**:
```bash
sudo apt autoremove
sudo apt autoclean
sudo apt clean
```

**Set up auto-restart for crashed services**:

In each Gunicorn systemd service, add:
```ini
[Service]
Restart=always
RestartSec=3
```

Example:
```ini
[Unit]
Description=gunicorn daemon for armguard
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/home/user/armguard
Environment="PATH=/home/user/armguard/venv/bin"
ExecStart=/home/user/armguard/venv/bin/gunicorn \
          --workers 3 \
          --threads 2 \
          --bind unix:/run/gunicorn-armguard.sock \
          core.wsgi:application
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

Reload and restart:
```bash
sudo systemctl daemon-reload
sudo systemctl restart gunicorn-armguard
```

### 6. Optimize Django Settings for Production

In `core/settings.py`:

```python
# Disable debug (already done)
DEBUG = False

# Use persistent connections (reduces DB overhead)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
        'CONN_MAX_AGE': 600,  # Reuse connections for 10 minutes
    }
}

# Session caching (reduces DB queries)
SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'

# Cache static file references
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'

# Logging (optional - helps debug performance issues)
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'WARNING',
            'class': 'logging.FileHandler',
            'filename': '/var/log/armguard/django.log',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'WARNING',
            'propagate': True,
        },
    },
}
```

Create log directory:
```bash
sudo mkdir -p /var/log/armguard
sudo chown www-data:www-data /var/log/armguard
```

### 7. Use PM2 for Node.js Apps (if applicable)

If running Node.js apps alongside Django:

```bash
# Install PM2
sudo npm install -g pm2

# Start app with limited instances
pm2 start app.js -i 2 --name "node-app"

# Auto-restart on crash
pm2 startup systemd
pm2 save

# Monitor
pm2 monit
```

### Performance Checklist

- ✅ Nginx serves static files (not Django/Flask)
- ✅ Gzip compression enabled in Nginx
- ✅ Gunicorn workers limited to `(2 × CPU) + 1`
- ✅ Database connections optimized (`CONN_MAX_AGE`)
- ✅ Swap file configured (1-2GB)
- ✅ Auto-restart enabled for services
- ✅ `DEBUG = False` in Django
- ✅ Regular cleanup (`apt autoremove`)
- ✅ Monitoring tools installed (`htop`)

### Expected Performance

With these optimizations on a Raspberry Pi 4 (4GB RAM):
- **2-3 Django apps**: Smooth, <100MB RAM per app
- **5+ apps**: Possible with swap and careful worker limits
- **Response time**: <200ms for cached pages, <500ms for dynamic

On a dedicated Ubuntu Server (2GB+ RAM):
- **5-10 apps**: No issues with proper configuration
- **Response time**: <100ms for most requests

---

## Quick Reference: Service Management

```bash
# Restart all services after changes
sudo systemctl restart gunicorn
sudo systemctl restart nginx

# View logs
sudo journalctl -u gunicorn -f    # Follow Gunicorn logs
sudo journalctl -u nginx -f       # Follow Nginx logs
sudo tail -f /var/log/nginx/error.log

# Check status
sudo systemctl status gunicorn
sudo systemctl status nginx

# Enable services on boot (already done in setup)
sudo systemctl enable gunicorn
sudo systemctl enable nginx
```

---

## Summary

✅ **You now have**:
- Nginx reverse proxy configured
- Gunicorn running as a systemd service
- Full HTTPS encryption on your LAN
- Trusted SSL certificates (no browser warnings)
- Secure Django deployment ready for production use

✅ **To add new client devices**:
- Copy `rootCA.pem` from server's `~/.local/share/mkcert/`
- Install on the client (follow platform-specific instructions above)

✅ **For updates/maintenance**:
- Certificates last 10+ years (no renewal needed)
- Update Nginx config if you change IPs/hostnames
- Keep the server's `rootCA-key.pem` file secure
- Use `sudo systemctl restart gunicorn` after code changes
- Use `sudo systemctl reload nginx` after Nginx config changes

---

**Deployment workflow**:
1. Deploy Django code to Ubuntu Server (see [UBUNTU_INSTALL.md](./UBUNTU_INSTALL.md))
2. Follow this guide (all steps in order)
3. Install CA certificate on all client devices (Part 2)
4. Access your app at `https://your-server-ip` with full HTTPS encryption

---

*Created: 2025-11-08*
