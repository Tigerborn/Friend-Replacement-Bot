import os
import requests
from dotenv import load_dotenv
import subprocess

#Runs the backup script for the containers on homelab

def backup_container(container):

    print("Starting backup...")

    result = subprocess.run(
        ["/home/caleb/scripts/backup.sh", container],
        capture_output=True,
        text=True,
        timeout=60
    )

    print("Return code:", result.returncode)
    print("STDOUT:", result.stdout)
    print("STDERR:", result.stderr)

    if result.returncode == 0:
        return f"Successfully backed up {container}."

    return f"Backup failed.\n{result.stderr}"