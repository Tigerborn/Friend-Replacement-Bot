import os
import requests
from dotenv import load_dotenv
import subprocess

#Runs the backup script for the containers on homelab

def backup_container(container):

    result = subprocess.run(
        [
            "/home/caleb/scripts/backup.sh",
            container
        ],
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        return f"Successfully backed up {container}."

    return f"Backup failed.\n{result.stderr}"