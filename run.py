"""
Madhyastha - Run Script
Starts frontend (Vite) silently in background, then backend (FastAPI) with full terminal output.
"""
import subprocess
import sys
import os
import signal
import time

ROOT = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(ROOT, "backend")
FRONTEND_DIR = os.path.join(ROOT, "frontend")
VENV_PYTHON = os.path.join(BACKEND_DIR, "venv", "Scripts", "python.exe")

processes = []


def start_frontend():
    """Start frontend silently in background — output suppressed"""
    print("[Madhyastha] Starting frontend on http://localhost:5173 ...")
    npm_cmd = "npm.cmd" if os.name == "nt" else "npm"
    proc = subprocess.Popen(
        [npm_cmd, "run", "dev"],
        cwd=FRONTEND_DIR,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    processes.append(proc)
    return proc


def start_backend():
    """Start backend with full terminal output — this is the main process"""
    print("[Madhyastha] Starting backend on http://localhost:8000 ...")
    print()
    proc = subprocess.Popen(
        [VENV_PYTHON, "-m", "uvicorn", "app.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"],
        cwd=BACKEND_DIR,
        stdout=sys.stdout,
        stderr=sys.stderr,
    )
    processes.append(proc)
    return proc


def cleanup(*args):
    print("\n[Madhyastha] Shutting down...")
    for proc in processes:
        try:
            proc.terminate()
            proc.wait(timeout=5)
        except Exception:
            proc.kill()
    print("[Madhyastha] All servers stopped.")
    sys.exit(0)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    print("=" * 60)
    print("  Madhyastha - AI Dispute Resolution Platform")
    print("=" * 60)
    print()

    # 1. Start frontend FIRST (silent background)
    frontend = start_frontend()
    time.sleep(3)  # Wait for Vite to be ready
    print("[Madhyastha] Frontend ready at http://localhost:5173")
    print()

    # 2. Start backend (full terminal output below)
    print("[Madhyastha] Backend logs below:")
    print("-" * 60)
    backend = start_backend()

    try:
        backend.wait()
    except KeyboardInterrupt:
        cleanup()
