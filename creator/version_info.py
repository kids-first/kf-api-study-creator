# This file will be re-written during the Docker build. For development, the
# following defaults are provided.
import subprocess
import os

try:
    VERSION = (
        subprocess.check_output(["git", "describe", "--always", "--tags"])
        .strip()
        .decode()
    )
except (FileNotFoundError, subprocess.CalledProcessError):
    VERSION = os.environ.get("VERSION", "LOCAL")

try:
    COMMIT = (
        subprocess.check_output(["git", "rev-parse", "--short", "HEAD"])
        .strip()
        .decode()
    )
except (FileNotFoundError, subprocess.CalledProcessError):
    COMMIT = os.environ.get("COMMIT", "-")
