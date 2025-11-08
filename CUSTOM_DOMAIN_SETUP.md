# Setup Custom Domain for ArmGuard

This guide helps you configure `armguard.rds` as a custom domain name for accessing ArmGuard.

---

## 🚀 Quick Setup (Windows)

### Automatic Setup (Recommended)

1. **Right-click** `setup-domain.ps1`
2. Select **"Run as Administrator"**
3. Done! Access at: `http://armguard.rds:8000`

### Manual Setup

If you prefer to do it manually:

1. **Open Notepad as Administrator:**
   - Press `Win + S`, search "Notepad"
   - Right-click → "Run as administrator"

2. **Open hosts file:**
   - File → Open
   - Navigate to: `C:\Windows\System32\drivers\etc`
   - Change file type to "All Files (*.*)"
   - Open `hosts`

3. **Add this line at the end:**
   ```
   192.168.68.129    armguard.rds
   ```
   *(Replace with your actual IP from `ipconfig`)*

4. **Save and close**

5. **Flush DNS cache:**
   ```powershell
   ipconfig /flushdns
   ```

---

## 📱 Mobile Phone Access

Unfortunately, custom domain names (like `armguard.rds`) **won't work on mobile phones** unless you:
- Set up a local DNS server (complex)
- Edit your phone's hosts file (requires rooting/jailbreaking)

### Solution: Use IP Address on Mobile

On your mobile phone, just use:
```
http://192.168.68.129:8000
```

This works immediately - no setup needed!

---

## 🌐 Access URLs

### On Your Computer:
- **Main App:** `http://armguard.rds:8000`
- **Admin Panel:** `http://armguard.rds:8000/superadmin/`

### On Your Mobile Phone:
- **Main App:** `http://192.168.68.129:8000`
- **Admin Panel:** `http://192.168.68.129:8000/superadmin/`

---

## ✅ Verification

Test if it's working:

1. **Open Command Prompt:**
   ```powershell
   ping armguard.rds
   ```
   Should reply from your IP address

2. **Open browser:**
   ```
   http://armguard.rds:8000
   ```
   Should show ArmGuard

---

## 🔧 Troubleshooting

### "Cannot access armguard.rds"

**Check 1: Hosts file entry**
```powershell
notepad C:\Windows\System32\drivers\etc\hosts
```
Verify line exists: `192.168.68.129    armguard.rds`

**Check 2: DNS cache**
```powershell
ipconfig /flushdns
```

**Check 3: Server running**
```powershell
python manage.py runserver 0.0.0.0:8000
```

**Check 4: Firewall**
- Windows may block incoming connections
- Allow Python through firewall when prompted

### Mobile can't connect

**Check 1: Same Wi-Fi network**
- Both devices must be on same network
- Check Wi-Fi name on both devices

**Check 2: IP address correct**
```powershell
ipconfig
```
Look for IPv4 address (should start with 192.168.x.x)

**Check 3: Server listening on all interfaces**
Must use `0.0.0.0:8000`, not `127.0.0.1:8000`

---

## 🗑️ Remove Custom Domain

To remove the custom domain:

1. **Open hosts file as Administrator:**
   ```powershell
   notepad C:\Windows\System32\drivers\etc\hosts
   ```

2. **Delete or comment out the line:**
   ```
   # 192.168.68.129    armguard.rds
   ```

3. **Save and flush DNS:**
   ```powershell
   ipconfig /flushdns
   ```

---

## 🎯 Summary

| Device | Access Method | URL |
|--------|---------------|-----|
| **Your Computer** | Custom domain | `http://armguard.rds:8000` |
| **Your Computer** | IP address | `http://192.168.68.129:8000` |
| **Mobile Phone** | IP address only | `http://192.168.68.129:8000` |
| **Other Computers (same network)** | IP address | `http://192.168.68.129:8000` |

---

## 💡 Pro Tips

1. **Bookmark it:** Save `http://armguard.rds:8000` in your browser favorites
2. **Create shortcut:** Right-click desktop → New → Shortcut → Enter URL
3. **Use both:** Domain on computer, IP on mobile - both work!
4. **Static IP:** Configure your computer to use a static IP to avoid changing it

---

**Happy browsing! 🎉**
