"""
Launcher entry point for PyInstaller-packaged .exe.
Double-click to start: one Chrome window serves as both
the Web UI dashboard and WeChat automation browser.
"""
import sys
import os
import traceback
from pathlib import Path


def _kill_previous():
    """Kill any process holding port 8000 (stale instance from previous run)."""
    import subprocess
    try:
        out = subprocess.check_output(
            'netstat -ano', shell=True, text=True,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
        )
        for line in out.splitlines():
            if ":8000" in line and "LISTENING" in line:
                parts = line.strip().split()
                pid = parts[-1]
                subprocess.call(
                    f"taskkill /f /pid {pid}", shell=True,
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                    creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
                )
                print(f"Cleaned up stale process (PID {pid})")
                import time
                time.sleep(1)
                break
    except Exception:
        pass


def main():
    # Kill stale process from previous run
    _kill_previous()

    # Determine exe/writable dir
    if getattr(sys, "frozen", False):
        _exe_dir = Path(sys.executable).parent
    else:
        _exe_dir = Path(__file__).resolve().parent

    # Ensure writable directories exist
    for d in ["logs", "storage", "config"]:
        (_exe_dir / d).mkdir(parents=True, exist_ok=True)

    # Create default .env if missing
    _env_path = _exe_dir / ".env"
    if not _env_path.exists():
        _env_path.write_text(
            "# WeChat AI Publisher Config\n"
            "APP_NAME=wechat-ai-publisher\n"
            "APP_VERSION=2.2.0\n"
            "APP_ENV=production\n"
            "ADMIN_TOKEN=wxai2026!\n"
            "CLIENT_MODE=true\n"
            "SERVER_HOST=127.0.0.1\n"
            "SERVER_PORT=8000\n"
            "LOG_LEVEL=INFO\n"
            "AI_API_KEY=your-deepseek-api-key-here\n"
            "AI_BASE_URL=https://api.deepseek.com\n"
            "AI_MODEL=deepseek-chat\n"
            "IMAGE_PROVIDER=jimeng\n"
            "IMAGE_API_KEY=\n"
            "IMAGE_BASE_URL=https://ark.cn-beijing.volces.com/api/v3\n"
            "IMAGE_MODEL=doubao-seedream-4-0\n"
            "OBSIDIAN_PATH=\n"
            "ENABLE_AI_GENERATE=true\n"
            "ENABLE_KNOWLEDGE=true\n"
            "ENABLE_IMAGE=true\n"
            "PUBLISH_MODE=auto\n",
            encoding="utf-8",
        )

    print(f"Work dir: {_exe_dir}")
    print("Starting server on http://127.0.0.1:8000 ...")
    print("Dashboard will open in Chrome window.")
    print("Close this window to shut down.")
    print("-" * 50)

    import uvicorn
    from backend.config import settings

    try:
        from backend.main import app
        uvicorn.run(
            app,
            host=settings.SERVER_HOST,
            port=settings.SERVER_PORT,
            log_level=settings.LOG_LEVEL.lower(),
        )
    except Exception:
        print("\n" + "=" * 50)
        print("STARTUP FAILED:")
        traceback.print_exc()
        print("=" * 50)
        print("\nCheck the .env file next to this exe for API keys.")
        input("Press Enter to exit...")


if __name__ == "__main__":
    main()
