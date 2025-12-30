import os
import zipfile
import subprocess
import sys
import shutil

# Configuration
LOCAL_PATH = r"e:\项目\币圈等监控系统"
REMOTE_USER = "root"
REMOTE_HOST = "172.245.53.67"
REMOTE_TARGET_DIR = "/var/www/monitor"
ZIP_FILENAME = "deploy_package.zip"

EXCLUDES = [
    ".git", ".agent", "__pycache__", "node_modules", "chrome_profile", 
    ".vscode", "deploy_package.zip", "sync_to_vps.ps1", "sync_deploy.py"
]

def zip_project():
    print(f"1. Compressing files in {LOCAL_PATH}...")
    if os.path.exists(ZIP_FILENAME):
        os.remove(ZIP_FILENAME)
        
    with zipfile.ZipFile(ZIP_FILENAME, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(LOCAL_PATH):
            # Filtering excluded directories
            dirs[:] = [d for d in dirs if d not in EXCLUDES]
            
            for file in files:
                if file == ZIP_FILENAME or file in EXCLUDES:
                    continue
                if file.endswith(".pyc") or file.endswith(".log"):
                    continue
                
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, LOCAL_PATH)
                zipf.write(file_path, arcname)
    print(f"   Created {ZIP_FILENAME}")

def upload_and_deploy():
    print(f"2. Uploading to {REMOTE_HOST}...")
    scp_cmd = f"scp {ZIP_FILENAME} {REMOTE_USER}@{REMOTE_HOST}:/tmp/"
    code = os.system(scp_cmd)
    if code != 0:
        print("Error: SCP failed.")
        return

    print("3. Deploying on remote server...")
    remote_cmds = [
        f"mkdir -p {REMOTE_TARGET_DIR}",
        f"unzip -o /tmp/{ZIP_FILENAME} -d {REMOTE_TARGET_DIR}",
        f"chown -R www-data:www-data {REMOTE_TARGET_DIR}",
        f"chmod -R 755 {REMOTE_TARGET_DIR}",
        f"systemctl reload nginx",
        f"rm /tmp/{ZIP_FILENAME}"
    ]
    
    ssh_cmd = f'ssh {REMOTE_USER}@{REMOTE_HOST} "{" ; ".join(remote_cmds)}"'
    code = os.system(ssh_cmd)
    
    if code == 0:
        print("\nSUCCESS! Deployment executed.")
        print(f"Verify at http://{REMOTE_HOST}/precious_metals_monitor.html")
    else:
        print("\nError: SSH command failed.")

    # Cleanup
    if os.path.exists(ZIP_FILENAME):
        os.remove(ZIP_FILENAME)

if __name__ == "__main__":
    os.chdir(LOCAL_PATH)
    try:
        zip_project()
        upload_and_deploy()
    except Exception as e:
        print(f"An error occurred: {e}")
        input("Press Enter to exit...")
