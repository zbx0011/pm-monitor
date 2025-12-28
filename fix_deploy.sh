#!/bin/bash

# 修复 404 错误的脚本
# 原因：Nginx 无法直接读取 /root 目录下的文件（权限问题）。
# 解决：将文件复制到标准的 Web 目录 /var/www/monitor

TARGET_DIR="/var/www/monitor"
DOMAIN="diffzhou.top"

echo "=== 开始修复部署 ==="

# 1. 创建标准 Web 目录并复制文件
echo "1. 正在将网站文件移动到 $TARGET_DIR ..."
mkdir -p $TARGET_DIR
cp -r * $TARGET_DIR

# 2. 设置正确的权限 (www-data 用户)
echo "2. 修正文件权限..."
chown -R www-data:www-data $TARGET_DIR
chmod -R 755 $TARGET_DIR

# 3. 更新 Nginx 配置
echo "3. 更新 Nginx 配置..."
cat > /etc/nginx/sites-available/$DOMAIN <<EOF
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN 172.245.53.67;
    root $TARGET_DIR;
    index precious_metals_monitor.html;

    location / {
        try_files \$uri \$uri/ =404;
    }
}
EOF

# 4. 重启 Nginx
echo "4. 重载服务..."
ln -sf /etc/nginx/sites-available/$DOMAIN /etc/nginx/sites-enabled/
nginx -t
systemctl reload nginx

echo "=== 修复完成 ==="
echo "请尝试访问: http://172.245.53.67/precious_metals_monitor.html"
echo "如果域名 DNS 已生效，也可以尝试再次运行 certbot 开启 HTTPS。"
