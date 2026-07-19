import os
import requests
from dotenv import load_dotenv
import subprocess

#Runs the backup script for the containers on homelab

def backup_container(container):

    print("Starting backup...")

    result = subprocess.run(
        ["/homelab/scripts/backup.sh", container],
        capture_output=True,
        text=True,
        timeout=60
    )

    if result.returncode == 0:
        return f"Successfully backed up {container}."

    return f"Backup failed.\n{result.stderr}"

def start(container):
    result = subprocess.run(["/homelab/scripts/start.sh", container], capture_output=True, text=True)
    if result.returncode == 0:
        return f"Successfully started {container}."
    else:
        return f"Failed to start.\n{result.stderr}"

def restart_terraria(container):
    print("Restarting terraria...")
    result = subprocess.run("/homelab/scripts/restart_terraria.sh", capture_output=True, text=True,timeout=60)
    if result.returncode == 0:
        return f"Successfully restarted {container}."
    else:
        start(container)
        return (f"restart failed.\n{result.stderr}" + "\n Manually starting back up!")

