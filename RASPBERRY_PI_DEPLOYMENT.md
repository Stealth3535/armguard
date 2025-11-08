# 🍓 ArmGuard Deployment on Raspberry Pi 5

Complete automated deployment guide for Raspberry Pi 5 running Ubuntu Server.

---

## ⚡ Quick Start (5 Minutes)

### **Step 1: Clone Repository (if not done)**

```bash
cd ~
git clone https://github.com/Stealth3535/armguard.git
cd armguard
```

### **Step 2: Make Scripts Executable**

```bash
chmod +x deployment/deploy-armguard.sh
chmod +x deployment/install-gunicorn-service.sh
chmod +x setup-domain-linux.sh
```

### **Step 3: Run Automated Deployment**

```bash
sudo bash deployment/deploy-armguard.sh
```

### **Step 4: Answer Configuration Questions**

The script will ask you a few questions. **Just press ENTER** to accept defaults:

1. **Project directory:** `/var/www/armguard` ✓ (press ENTER)
2. **Domain name:** `armguard.rds` ✓ (press ENTER)
3. **Server IP:** Auto-detected ✓ (press ENTER)
4. **Run user:** `www-data` ✓ (press ENTER)
5. **Configure SSL?** `yes` ✓ (press ENTER)
   - **SSL type:** `1` for mkcert ✓ (press ENTER)
6. **Use PostgreSQL?** `no` ✓ (press ENTER - SQLite is fine for RPi5)
7. **Configure firewall?** `yes` ✓ (press ENTER)

**Create superuser when prompted:**
- Username: `admin` (or your choice)
- Email: your email
- Password: create a strong password

### **Step 5: Access Your Application**

After deployment completes (5-10 minutes), access at:

```
http://armguard.rds:8000
http://YOUR_RPI_IP:8000
```

**Admin panel:**
```
http://armguard.rds:8000/admin-XXXXXXXX/
```

(The exact admin URL will be shown in the deployment summary)

---

## 📋 What the Script Does

The automated deployment script handles **EVERYTHING**:

✅ **System Setup**
- Updates Ubuntu packages
- Installs Python 3, pip, venv
- Installs Nginx web server
- Installs security tools (UFW firewall, Fail2Ban)

✅ **Application Setup**
- Creates virtual environment in `/var/www/armguard/.venv`
- Installs all Python dependencies from requirements.txt
- Configures SQLite database (or PostgreSQL if chosen)
- Creates `.env` file with secure random secrets
- Runs database migrations
- Creates superuser account (you'll be prompted)
- Collects static files to `/var/www/armguard/staticfiles`

✅ **Web Server Configuration**
- Installs Gunicorn as systemd service
- Calculates optimal workers (2×CPU cores + 1)
- Configures Nginx reverse proxy
- Sets up SSL/HTTPS with mkcert (for LAN)
- Configures logging to `/var/log/armguard/`

✅ **Security Hardening**
- Configures UFW firewall (allows SSH, HTTP, HTTPS)
- Sets up Fail2Ban for brute-force protection
- Applies secure file permissions
- Generates random Django secret key
- Randomizes admin URL for security

✅ **Service Management**
- Enables auto-start on boot
- Configures auto-restart on failure
- Sets up health monitoring

---

## 🎯 After Deployment

### **Check Services Status**

```bash
# Check if Gunicorn is running
sudo systemctl status gunicorn-armguard

# Check if Nginx is running
sudo systemctl status nginx

# View real-time logs
sudo journalctl -u gunicorn-armguard -f
```

### **Access Application**

```bash
# From Raspberry Pi browser
http://armguard.rds:8000

# From other devices on same network
http://192.168.x.x:8000  # Use your RPi IP
```

### **Find Your Deployment Info**

All configuration details are saved:

```bash
sudo cat /var/www/armguard/DEPLOYMENT_INFO.txt
```

This file contains:
- Application URLs
- Admin URL path (randomized)
- Django secret key
- Database credentials (if using PostgreSQL)
- Service file locations

---

## 🔧 Managing Your Application

### **Restart Services**

```bash
# Restart Gunicorn (after code changes)
sudo systemctl restart gunicorn-armguard

# Reload Nginx (after config changes)
sudo systemctl reload nginx

# Restart both
sudo systemctl restart gunicorn-armguard nginx
```

### **View Logs**

```bash
# Application logs
sudo tail -f /var/log/armguard/access.log
sudo tail -f /var/log/armguard/error.log

# System service logs
sudo journalctl -u gunicorn-armguard -n 50
sudo journalctl -u nginx -n 50

# Django security logs
sudo tail -f /var/www/armguard/logs/security.log
```

### **Update Application**

When you push changes to GitHub:

```bash
cd /var/www/armguard

# Pull latest changes
sudo git pull origin main

# Activate virtual environment
sudo -u www-data /var/www/armguard/.venv/bin/python manage.py migrate --settings=core.settings_production

# Collect static files
sudo -u www-data /var/www/armguard/.venv/bin/python manage.py collectstatic --noinput --settings=core.settings_production

# Restart service
sudo systemctl restart gunicorn-armguard
```

---

## 🌐 Network Access

### **From Raspberry Pi (Local)**

```
http://localhost:8000
http://127.0.0.1:8000
http://armguard.rds:8000
```

### **From Other Devices (LAN)**

```
http://192.168.x.x:8000  # Use your RPi's IP address
```

**Find your RPi IP:**
```bash
hostname -I | awk '{print $1}'
```

### **From Mobile Phone**

1. Connect phone to **same Wi-Fi network**
2. Open browser
3. Go to: `http://YOUR_RPI_IP:8000`

**Note:** The domain `armguard.rds` only works on devices where you configure it in the hosts file. For mobile, just use the IP address.

---

## 🔒 SSL/HTTPS Setup

The automated script installs **mkcert** for local SSL:

### **Install CA Certificate on Client Devices**

For HTTPS to work without browser warnings:

**1. On Raspberry Pi, find CA certificate:**
```bash
sudo cat ~/.local/share/mkcert/rootCA.pem
```

**2. Copy to client devices:**

**Windows:**
- Copy `rootCA.pem` file
- Double-click → Install Certificate
- Store Location: Local Machine
- Place in: Trusted Root Certification Authorities

**macOS:**
- Copy `rootCA.pem` file
- Double-click to open Keychain Access
- Set to "Always Trust"

**Android:**
- Settings → Security → Install from storage
- Select `rootCA.pem`

**Linux:**
```bash
sudo cp rootCA.pem /usr/local/share/ca-certificates/mkcert.crt
sudo update-ca-certificates
```

**iOS:**
- Email the file to yourself
- Open on iPhone → Install Profile
- Settings → General → About → Certificate Trust Settings → Enable

---

## 🐛 Troubleshooting

### **Script fails during installation**

```bash
# Check error message carefully
# Usually missing dependencies or permissions

# Try running individual commands to identify issue
sudo apt update
sudo apt install python3 python3-pip python3-venv nginx -y
```

### **Service won't start**

```bash
# Check detailed logs
sudo journalctl -u gunicorn-armguard -n 100 --no-pager

# Common issues:
# 1. Missing Python packages
cd /var/www/armguard
source .venv/bin/activate
pip install -r requirements.txt

# 2. Database not migrated
python manage.py migrate --settings=core.settings_production

# 3. Permission issues
sudo chown -R www-data:www-data /var/www/armguard
```

### **Can't access from browser**

```bash
# 1. Check if services are running
sudo systemctl status gunicorn-armguard
sudo systemctl status nginx

# 2. Check firewall
sudo ufw status
sudo ufw allow 8000/tcp  # If needed

# 3. Check if socket exists
ls -l /run/gunicorn-armguard.sock

# 4. Test Gunicorn directly
cd /var/www/armguard
source .venv/bin/activate
gunicorn --bind 0.0.0.0:8000 core.wsgi:application
```

### **HTTPS not working**

```bash
# Check if mkcert installed
which mkcert

# Check certificates
ls -l /etc/ssl/armguard/

# Reinstall certificates if needed
cd /etc/ssl/armguard
sudo mkcert 192.168.x.x armguard.rds localhost 127.0.0.1
sudo systemctl reload nginx
```

### **"Bad Gateway" error**

This means Nginx is running but can't connect to Gunicorn:

```bash
# 1. Check Gunicorn status
sudo systemctl status gunicorn-armguard

# 2. Check socket permissions
ls -l /run/gunicorn-armguard.sock

# 3. Restart Gunicorn
sudo systemctl restart gunicorn-armguard

# 4. Check Nginx error log
sudo tail -f /var/log/nginx/error.log
```

---

## 🔥 Performance Tips for Raspberry Pi 5

### **Optimize Worker Count**

Raspberry Pi 5 has 4 cores, default workers = 9

For lighter load:
```bash
sudo nano /etc/systemd/system/gunicorn-armguard.service
# Change --workers 9 to --workers 5
sudo systemctl daemon-reload
sudo systemctl restart gunicorn-armguard
```

### **Use SQLite (Default)**

SQLite is sufficient for small teams and performs well on RPi5:
- No database server overhead
- Simple backups (just copy db.sqlite3)
- Fast for <100 concurrent users

### **Enable Swap (If needed)**

If you experience memory issues:
```bash
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

### **Monitor Resources**

```bash
# Install monitoring tools
sudo apt install htop iotop -y

# View system resources
htop

# View disk I/O
sudo iotop
```

---

## 📊 Raspberry Pi 5 Specifications

**Your RPi5 can handle:**
- ✅ 50-100 concurrent users (with SQLite)
- ✅ 200+ concurrent users (with PostgreSQL)
- ✅ 1000+ transactions per day
- ✅ 24/7 operation
- ✅ Multiple Django apps on same server

**Network Performance:**
- Gigabit Ethernet: ~940 Mbps
- Wi-Fi 6: ~200-400 Mbps
- Perfect for LAN deployment

---

## 🎉 Success Checklist

After running the automated script, verify:

- [ ] Gunicorn service running: `sudo systemctl status gunicorn-armguard`
- [ ] Nginx service running: `sudo systemctl status nginx`
- [ ] Application accessible: Open browser to `http://armguard.rds:8000`
- [ ] Admin panel accessible: `http://armguard.rds:8000/admin-XXXXXXXX/`
- [ ] Can login with superuser account
- [ ] Can create personnel/items
- [ ] QR codes generate correctly
- [ ] Transactions work
- [ ] Mobile access works via IP
- [ ] Services auto-start on reboot: `sudo reboot` then check

---

## 📚 Additional Resources

**Documentation Files:**
- `deployment/README.md` - Service management details
- `deployment/QUICK_DEPLOY.md` - Quick deployment reference
- `SECURITY_ONLINE_TESTING.md` - Security hardening guide
- `CUSTOM_DOMAIN_SETUP.md` - Custom domain configuration
- `/var/www/armguard/DEPLOYMENT_INFO.txt` - Your deployment details

**Service Files:**
- `/etc/systemd/system/gunicorn-armguard.service` - Gunicorn service
- `/etc/nginx/sites-available/armguard` - Nginx configuration
- `/var/log/armguard/` - Application logs
- `/var/www/armguard/.env` - Environment configuration

---

## 🆘 Need Help?

**Check logs first:**
```bash
# Application errors
sudo tail -f /var/log/armguard/error.log

# Service errors
sudo journalctl -u gunicorn-armguard -f

# Nginx errors
sudo tail -f /var/log/nginx/error.log
```

**Common commands:**
```bash
# Restart everything
sudo systemctl restart gunicorn-armguard nginx

# Check configuration
python manage.py check --settings=core.settings_production

# Test database
python manage.py dbshell --settings=core.settings_production
```

---

## 🎯 Summary Commands

```bash
# Deploy (run once)
sudo bash deployment/deploy-armguard.sh

# Check status
sudo systemctl status gunicorn-armguard nginx

# View logs
sudo journalctl -u gunicorn-armguard -f

# Restart after changes
sudo systemctl restart gunicorn-armguard

# Access application
http://armguard.rds:8000
http://YOUR_RPI_IP:8000
```

---

**That's it! Your ArmGuard application should now be running on your Raspberry Pi 5! 🚀**

**Estimated deployment time: 5-10 minutes** ⏱️
