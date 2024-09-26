"""
This is a standalone script that checks if a requirements file is up-to-date with the poetry.lock file.
It computes a SHA1 hash of `poetry.lock` and compares that with a comment in the first line of `requirements.txt`.

Usage:
```
python validation_script.py
# for custom file paths:
python validation_script.py path/to/poetry.lock path/to/requirements.txt
```
"""

import hashlib
import sys
from pathlib import Path

lock_file_path = sys.argv[1] if len(sys.argv) > 1 else "poetry.lock"
requirements_file_path = sys.argv[2] if len(sys.argv) > 2 else "requirements.txt"

lock_file = Path(lock_file_path)
requirements_file = Path(requirements_file_path)

lock_hash = hashlib.sha1(lock_file.read_bytes()).hexdigest()
first_line = requirements_file.read_text().split("\n")[0]

if first_line != f"# poetry.lock hash: {lock_hash}":
    raise ValueError(
        "requirements.txt is out of date, use the `poetry-auto-export` plugin to update it!"
    )
