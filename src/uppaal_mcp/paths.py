from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

WINDOWS_PATH_RE = re.compile(r"^[A-Za-z]:[\\/]")


def is_windows_path(value: str | os.PathLike[str]) -> bool:
    return bool(WINDOWS_PATH_RE.match(str(value)))


def is_windows_executable(value: str | os.PathLike[str]) -> bool:
    text = str(value)
    return is_windows_path(text) or text.lower().endswith(".exe")


def windows_to_wsl_path(value: str) -> str:
    drive = value[0].lower()
    tail = value[2:].replace("\\", "/").lstrip("/")
    return f"/mnt/{drive}/{tail}"


def wsl_to_windows_path(value: str | os.PathLike[str]) -> str:
    path = str(value)
    match = re.match(r"^/mnt/([A-Za-z])/(.*)$", path)
    if match:
        drive = match.group(1).upper()
        tail = match.group(2).replace("/", "\\")
        return f"{drive}:\\{tail}"

    converted = _try_wslpath(path)
    return converted or path


def local_path(value: str | os.PathLike[str]) -> Path:
    text = str(value)
    if os.name != "nt" and is_windows_path(text):
        return Path(windows_to_wsl_path(text))
    return Path(text).expanduser()


def path_for_verifyta_arg(
    path: str | os.PathLike[str],
    verifyta_path: str | os.PathLike[str],
) -> str:
    text = str(path)
    if os.name != "nt" and is_windows_executable(verifyta_path):
        if is_windows_path(text):
            return text
        return wsl_to_windows_path(Path(text).resolve())
    return text


def _try_wslpath(path: str) -> str | None:
    try:
        result = subprocess.run(
            ["wslpath", "-w", path],
            check=False,
            capture_output=True,
            text=True,
            timeout=2,
        )
    except (FileNotFoundError, subprocess.SubprocessError):
        return None
    if result.returncode != 0:
        return None
    converted = result.stdout.strip()
    return converted or None
