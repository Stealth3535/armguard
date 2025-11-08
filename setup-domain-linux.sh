#!/bin/bash

################################################################################
# ArmGuard Custom Domain Setup for Linux/Ubuntu
# 
# This script configures armguard.rds domain for local access
# Usage: sudo bash setup-domain-linux.sh
################################################################################

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
DOMAIN="armguard.rds"
HOSTS_FILE="/etc/hosts"

# Print banner
echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}  ArmGuard Custom Domain Setup${NC}"
echo -e "${CYAN}  Domain: ${DOMAIN}${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}ERROR: This script must be run as root (use sudo)${NC}"
    echo ""
    echo -e "${YELLOW}Usage: sudo bash setup-domain-linux.sh${NC}"
    exit 1
fi

# Get the server's IP address
echo -e "${YELLOW}Detecting server IP address...${NC}"

# Try to get the main network IP (not loopback, not docker, not virtual)
IP_ADDRESS=$(ip -4 addr show | grep -oP '(?<=inet\s)\d+(\.\d+){3}' | grep -v '^127\.' | grep -v '^172\.17\.' | grep '^192\.168\.' | head -n 1)

if [ -z "$IP_ADDRESS" ]; then
    # Fallback: try any non-loopback IP
    IP_ADDRESS=$(hostname -I | awk '{print $1}')
fi

if [ -z "$IP_ADDRESS" ]; then
    echo -e "${RED}Could not detect IP address automatically.${NC}"
    read -p "Please enter your server's IP address: " IP_ADDRESS
fi

echo -e "${GREEN}Using IP address: ${IP_ADDRESS}${NC}"
echo ""

# Create entry
ENTRY="${IP_ADDRESS}    ${DOMAIN}"

# Backup hosts file
echo -e "${YELLOW}Creating backup of hosts file...${NC}"
cp "$HOSTS_FILE" "${HOSTS_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
echo -e "${GREEN}Backup created: ${HOSTS_FILE}.backup.$(date +%Y%m%d_%H%M%S)${NC}"
echo ""

# Check if entry already exists
if grep -q "armguard\.rds" "$HOSTS_FILE"; then
    echo -e "${YELLOW}Found existing entry for ${DOMAIN}${NC}"
    EXISTING=$(grep "armguard\.rds" "$HOSTS_FILE")
    echo -e "${YELLOW}  ${EXISTING}${NC}"
    echo ""
    
    # Remove old entry
    echo -e "${YELLOW}Removing old entry...${NC}"
    sed -i '/armguard\.rds/d' "$HOSTS_FILE"
fi

# Add new entry
echo -e "${YELLOW}Adding new entry to hosts file:${NC}"
echo -e "${GREEN}  ${ENTRY}${NC}"
echo ""

echo "" >> "$HOSTS_FILE"
echo "# ArmGuard - Added by setup-domain-linux.sh on $(date '+%Y-%m-%d %H:%M:%S')" >> "$HOSTS_FILE"
echo "$ENTRY" >> "$HOSTS_FILE"

# Verify entry was added
if grep -q "$DOMAIN" "$HOSTS_FILE"; then
    echo -e "${GREEN}SUCCESS! Domain configured successfully!${NC}"
    echo ""
    
    # Test DNS resolution
    echo -e "${YELLOW}Testing DNS resolution...${NC}"
    if ping -c 1 -W 1 "$DOMAIN" &> /dev/null; then
        echo -e "${GREEN}✓ ${DOMAIN} resolves to ${IP_ADDRESS}${NC}"
    else
        echo -e "${YELLOW}⚠ Ping test inconclusive (may be blocked by firewall)${NC}"
    fi
    echo ""
    
    echo -e "${CYAN}========================================${NC}"
    echo -e "${GREEN}  Setup Complete!${NC}"
    echo -e "${CYAN}========================================${NC}"
    echo ""
    
    echo -e "${YELLOW}You can now access ArmGuard at:${NC}"
    echo -e "${GREEN}  http://${DOMAIN}:8000${NC}"
    echo -e "${GREEN}  http://${DOMAIN}:8000/superadmin/${NC}"
    echo ""
    
    echo -e "${YELLOW}Next steps:${NC}"
    echo -e "${GREEN}1. Start Django server:${NC}"
    echo -e "   ${CYAN}python manage.py runserver 0.0.0.0:8000${NC}"
    echo ""
    echo -e "${GREEN}2. Open browser and go to:${NC}"
    echo -e "   ${CYAN}http://${DOMAIN}:8000${NC}"
    echo ""
    
    echo -e "${YELLOW}For mobile/other devices on same network:${NC}"
    echo -e "${GREEN}Use IP address:${NC} ${CYAN}http://${IP_ADDRESS}:8000${NC}"
    echo -e "${YELLOW}(Domain names require configuring each device's hosts file)${NC}"
    echo ""
    
    echo -e "${YELLOW}To remove this domain later:${NC}"
    echo -e "   ${CYAN}sudo sed -i '/armguard\.rds/d' /etc/hosts${NC}"
    echo ""
    
else
    echo -e "${RED}ERROR: Failed to add entry to hosts file!${NC}"
    exit 1
fi

echo -e "${CYAN}Hosts file location: ${HOSTS_FILE}${NC}"
echo -e "${CYAN}Backup location: ${HOSTS_FILE}.backup.*${NC}"
echo ""
