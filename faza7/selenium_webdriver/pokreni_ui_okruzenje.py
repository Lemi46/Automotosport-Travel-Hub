# Pokreće lokalni mock API i Django server podešen na MySQL.

from __future__ import annotations

import os
import subprocess
import sys
import threading
from pathlib import Path

from mock_motorsport_api import build_server


def main() -> int:
    here = Path(__file__).resolve().parent
    project_root = here.parents[1] / "faza5"
    mock_host = os.getenv("MOCK_API_HOST", "127.0.0.1")
    mock_port = int(os.getenv("MOCK_API_PORT", "8765"))
    django_addr = os.getenv("DJANGO_ADDR", "127.0.0.1:8000")

    server = build_server(mock_host, mock_port)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    env = os.environ.copy()
    base = f"http://{mock_host}:{mock_port}"
    env.update(
        {
            "F1_API_URL": f"{base}/f1/current.json",
            "MOTOGP_SEASONS_API_URL": f"{base}/motogp/seasons",
            "MOTOGP_EVENTS_API_URL": f"{base}/motogp/events",
            "SPORTSDB_API_URL": f"{base}/wsbk/eventsseason.php",
        }
    )

    print(f"Mock API: {base}")
    print(f"Django:   http://{django_addr}")
    print("Za prekid pritisnite Ctrl+C.")
    process = subprocess.Popen(
        [sys.executable, "manage.py", "runserver", django_addr, "--noreload"],
        cwd=project_root,
        env=env,
    )
    try:
        return process.wait()
    except KeyboardInterrupt:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
        return 130
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    raise SystemExit(main())
