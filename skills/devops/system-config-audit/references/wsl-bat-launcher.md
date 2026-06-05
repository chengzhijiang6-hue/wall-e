# WSL .bat Launcher Creation Guide

## Problem
Creating a Windows `.bat` file from within WSL to launch a WSL-based CLI tool (Hermes Agent, OpenClaw, etc.) encounters encoding issues: Chinese characters or other non-ASCII text in the bat file display as garbled when run in Windows cmd.exe.

## Root Cause
- WSL writes files in UTF-8 encoding by default
- Windows cmd.exe in different regions uses different code pages:
  - Chinese Windows: CP936 (GBK)
  - US/European Windows: CP437 (OEM) or CP1252
  - Modern Windows 10/11: can use CP65001 (UTF-8) depending on settings
- No single non-ASCII encoding works reliably across all Windows configurations
- UTF-8 BOM (`utf-8-sig`) works on Windows 10+ but not on older systems

## Solution
**Use pure 7-bit ASCII only** in the bat file. No Chinese, no accented characters, no emoji.

## Verified Working Template
```bat
@echo off
title WALL-E - Hermes Agent
echo ========================================
echo    Launch WALL-E (Hermes Agent)
echo ========================================
echo.

wsl -d Ubuntu-24.04 --cd /mnt/c/wsl/hermes_official /mnt/c/wsl/hermes_official/venv/bin/hermes

echo.
if %errorlevel% neq 0 (
    echo Exit code: %errorlevel%
    echo If launch failed, check that WSL is running normally.
    pause
)
```

## Key Components

| Component | Description |
|-----------|-------------|
| `wsl -d <DISTRO>` | Launch specific WSL distro (Ubuntu-24.04) |
| `--cd <PATH>` | Set working directory inside WSL |
| `/full/path/to/binary` | Direct executable path (not via bash -c) |
| `title` | Set the terminal window title |
| `%errorlevel%` | Check exit code to show error on failure |

## Verification
After writing the bat file from WSL, verify all bytes are ASCII (< 0x80):
```bash
python3 -c "
with open('/path/to/file.bat', 'rb') as f:
    raw = f.read()
    non_ascii = [(i, b) for i, b in enumerate(raw) if b >= 128]
    if non_ascii:
        print(f'WARNING: {len(non_ascii)} non-ASCII bytes found: {non_ascii[:10]}')
    else:
        print('OK: All bytes are ASCII')
"
```

## Alternative Approaches Tested (Failed)
- **UTF-8 encoded non-ASCII** → garbled as `σÉ»σè¿` when cmd uses Latin-1/CP437
- **GBK encoded Chinese** → garbled as `╞⌠╢»` when cmd uses CP437
- **utf-8-sig (UTF-8 with BOM)** → works on Win10+ but breaks on older systems

## User-Facing Explanation
When the user asks for Chinese text in the bat, explain:
"The bat file must use only English characters to ensure it works correctly on all Windows systems regardless of language settings. You can add Chinese text yourself after testing the basic launch works."
