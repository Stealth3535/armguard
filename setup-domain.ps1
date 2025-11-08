# ArmGuard Custom Domain Setup
# This script configures armguard.rds domain for local access
# Run as Administrator: Right-click > Run as Administrator

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  ArmGuard Custom Domain Setup" -ForegroundColor Cyan
Write-Host "  Domain: armguard.rds" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "ERROR: This script must be run as Administrator!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Right-click this file and select 'Run as Administrator'" -ForegroundColor Yellow
    Write-Host ""
    pause
    exit 1
}

# Get the computer's IP address (main network adapter)
Write-Host "Detecting your computer's IP address..." -ForegroundColor Yellow
$ipAddress = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object {
    $_.InterfaceAlias -notlike "*Loopback*" -and 
    $_.InterfaceAlias -notlike "*VMware*" -and
    $_.InterfaceAlias -notlike "*VirtualBox*" -and
    $_.IPAddress -like "192.168.*"
} | Select-Object -First 1).IPAddress

if (-not $ipAddress) {
    Write-Host "Could not detect IP address automatically." -ForegroundColor Red
    $ipAddress = Read-Host "Please enter your computer's IP address (e.g., 192.168.68.129)"
}

Write-Host "Using IP address: $ipAddress" -ForegroundColor Green
Write-Host ""

# Hosts file path
$hostsPath = "$env:SystemRoot\System32\drivers\etc\hosts"
$domain = "armguard.rds"
$entry = "$ipAddress    $domain"

# Check if entry already exists
$hostsContent = Get-Content $hostsPath
$existingEntry = $hostsContent | Where-Object { $_ -match "armguard\.rds" }

if ($existingEntry) {
    Write-Host "Found existing entry:" -ForegroundColor Yellow
    Write-Host "  $existingEntry" -ForegroundColor Gray
    Write-Host ""
    
    # Remove old entry
    $hostsContent = $hostsContent | Where-Object { $_ -notmatch "armguard\.rds" }
    Write-Host "Removing old entry..." -ForegroundColor Yellow
}

# Add new entry
Write-Host "Adding new entry to hosts file:" -ForegroundColor Yellow
Write-Host "  $entry" -ForegroundColor Green
Write-Host ""

$hostsContent += ""
$hostsContent += "# ArmGuard - Added by setup-domain.ps1 on $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
$hostsContent += $entry

# Write to hosts file
try {
    $hostsContent | Set-Content $hostsPath -Force
    Write-Host "SUCCESS! Domain configured successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "You can now access ArmGuard at:" -ForegroundColor Cyan
    Write-Host "  http://armguard.rds:8000" -ForegroundColor White -BackgroundColor DarkGreen
    Write-Host "  http://armguard.rds:8000/superadmin/" -ForegroundColor White -BackgroundColor DarkGreen
    Write-Host ""
    
    # Flush DNS cache
    Write-Host "Flushing DNS cache..." -ForegroundColor Yellow
    ipconfig /flushdns | Out-Null
    Write-Host "DNS cache flushed!" -ForegroundColor Green
    Write-Host ""
    
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "  Setup Complete!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Yellow
    Write-Host "1. Make sure Django server is running:" -ForegroundColor White
    Write-Host "   python manage.py runserver 0.0.0.0:8000" -ForegroundColor Gray
    Write-Host ""
    Write-Host "2. Open browser and go to:" -ForegroundColor White
    Write-Host "   http://armguard.rds:8000" -ForegroundColor Gray
    Write-Host ""
    Write-Host "For mobile access:" -ForegroundColor Yellow
    Write-Host "- Connect phone to same Wi-Fi" -ForegroundColor White
    Write-Host "- Use IP instead: http://$ipAddress:8000" -ForegroundColor Gray
    Write-Host "  (Domain names don't work on mobile without DNS server)" -ForegroundColor DarkGray
    Write-Host ""
    
} catch {
    Write-Host "ERROR: Failed to write to hosts file!" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host ""
    pause
    exit 1
}

Write-Host "Press any key to exit..." -ForegroundColor DarkGray
pause | Out-Null
