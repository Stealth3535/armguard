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
- **Nginx** installed and configured as a reverse proxy for Gunicorn
- **Django app** running on Gunicorn (systemd service or manual)
- Devices on the same network that will access the app (Windows PCs, Android/iOS devices)

---

## Part 1: Server Setup (Ubuntu)

### 1) Install mkcert on Ubuntu Server

```bash
# Install dependencies
sudo apt update
sudo apt install -y wget libnss3-tools

# Download and install mkcert (latest version - check GitHub for updates)
wget https://github.com/FiloSottile/mkcert/releases/download/v1.4.4/mkcert-v1.4.4-linux-amd64
sudo mv mkcert-v1.4.4-linux-amd64 /usr/local/bin/mkcert
sudo chmod +x /usr/local/bin/mkcert

# Verify installation
mkcert -version
```

### 2) Create a local Certificate Authority (CA)

```bash
# Generate the local CA (creates rootCA.pem and rootCA-key.pem in ~/.local/share/mkcert)
mkcert -install

# Show the CA certificate location (you'll need this file for client devices)
mkcert -CAROOT
```

**Important**: The CA certificate file is located at `~/.local/share/mkcert/rootCA.pem`. You will copy this file to client devices later.

### 3) Generate SSL certificate for your LAN IP or hostname

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

### 4) Move certificates to a secure location

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

### 5) Configure Nginx for HTTPS

Edit your Nginx server block (e.g., `/etc/nginx/sites-available/armguard`):

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
sudo ln -sf /etc/nginx/sites-available/armguard /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 6) Update Django settings

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

Restart Gunicorn:

```bash
sudo systemctl restart gunicorn
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

## Part 3: Testing and Verification

### On the server:
```bash
# Test Nginx SSL configuration
sudo nginx -t

# Check certificate details
openssl x509 -in /etc/ssl/armguard/192.168.1.100+2.pem -text -noout

# Test HTTPS locally
curl -I https://192.168.1.100
```

### On client devices:
1. Open browser and navigate to `https://192.168.1.100` (or your hostname)
2. Verify:
   - ✅ Green padlock appears
   - ✅ No certificate warnings
   - ✅ Site loads properly
3. Click the padlock → **Certificate** → Verify issuer is "mkcert"

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
- **Firewall**: Open ports 80 and 443
  ```bash
  sudo ufw allow 80/tcp
  sudo ufw allow 443/tcp
  sudo ufw reload
  ```
- **Verify server IP**: `ip addr show` or `hostname -I`
- **Test connectivity**: From client, `ping 192.168.1.100`

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

## Optional: Use .local mDNS hostname

Instead of remembering the IP, use a `.local` hostname (requires Avahi/mDNS):

**On Ubuntu Server:**
```bash
sudo apt install avahi-daemon
sudo systemctl enable avahi-daemon
sudo systemctl start avahi-daemon

# Edit /etc/hostname to set hostname (e.g., "armguard")
sudo hostnamectl set-hostname armguard
```

**Access from clients**: `https://armguard.local` (works on macOS, Linux, Windows 10+ with Bonjour)

**Generate certificate**:
```bash
mkcert armguard.local 192.168.1.100 localhost 127.0.0.1
```

---

## Summary

✅ **You now have**:
- Full HTTPS encryption on your LAN
- Trusted SSL certificates (no browser warnings)
- Secure Django deployment with Nginx + Gunicorn

✅ **To add new client devices**:
- Copy `rootCA.pem` from server's `~/.local/share/mkcert/`
- Install on the client (follow platform-specific instructions above)

✅ **For updates/maintenance**:
- Certificates last 10+ years (no renewal needed)
- Update Nginx config if you change IPs/hostnames
- Keep the server's `rootCA-key.pem` file secure

---

**Next steps**: Follow the [UBUNTU_INSTALL.md](./UBUNTU_INSTALL.md) guide for full Ubuntu deployment, then return here for SSL setup.

---

*Created: 2025-11-08*
