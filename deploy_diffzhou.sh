#!/bin/bash

# Configuration
DOMAIN="diffzhou.top"
WEB_ROOT=$(pwd)

# Ensure script is run as root
if [ "$EUID" -ne 0 ]; then 
  echo "Please run as root"
  exit 1
fi

echo "=== Starting Deployment for $DOMAIN ==="
echo "Web Root: $WEB_ROOT"

# 1. Install Dependencies
echo "Step 1: Installing Nginx and Certbot..."
apt-get update
apt-get install -y nginx certbot python3-certbot-nginx

# 2. Configure Nginx
echo "Step 2: Creating Nginx Configuration..."
cat > /etc/nginx/sites-available/$DOMAIN <<EOF
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;
    root $WEB_ROOT;
    index precious_metals_monitor.html;

    location / {
        try_files \$uri \$uri/ =404;
    }

    # Deny access to hidden files (like .git)
    location ~ /\. {
        deny all;
    }
}
EOF

# Enable site and remove default
ln -sf /etc/nginx/sites-available/$DOMAIN /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test config
echo "Testing Nginx Config..."
nginx -t

if [ $? -eq 0 ]; then
    systemctl reload nginx
    echo "Nginx configured successfully."
else
    echo "Nginx configuration failed. Please check errors."
    exit 1
fi

# 3. SSL Certificate
echo "Step 3: Obtaining SSL Certificate..."
# Check if certificate already exists to avoid rate limits or redundant calls
if [ -d "/etc/letsencrypt/live/$DOMAIN" ]; then
    echo "Certificate already exists. Skipping Certbot..."
else
    certbot --nginx -d $DOMAIN -d www.$DOMAIN --non-interactive --agree-tos --register-unsafely-without-email --redirect
fi

echo "=== Deployment Complete! ==="
echo "You can now visit: https://$DOMAIN"
