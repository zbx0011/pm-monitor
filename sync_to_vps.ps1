
$LocalPath = "e:\项目\币圈等监控系统"
$RemoteUser = "root"
$RemoteIp = "172.245.53.67"
$ZipFile = "deploy.zip"

Write-Host "1. Zipping..."
Set-Location $LocalPath
Compress-Archive -Path * -DestinationPath $ZipFile -Update -Force

Write-Host "2. Uploading..."
scp $ZipFile $RemoteUser@$RemoteIp:/tmp/

Write-Host "3. Deploying..."
$Cmd = "mkdir -p /var/www/monitor; unzip -o /tmp/$ZipFile -d /var/www/monitor; chown -R www-data:www-data /var/www/monitor; chmod -R 755 /var/www/monitor; systemctl reload nginx; rm /tmp/$ZipFile"
ssh $RemoteUser@$RemoteIp $Cmd

Remove-Item $ZipFile
Write-Host "Success! Check http://$RemoteIp/precious_metals_monitor.html"
