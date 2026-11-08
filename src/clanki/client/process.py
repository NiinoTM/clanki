import atexit
import os
import shutil
import signal
import subprocess
import sys
import time
from typing import Any, Optional
from clanki.client.anki_connect import AnkiConnectClient
from clanki.ui.display import render_progress
from clanki.ui.theme import C_RED, RESET

class AnkiProcessManager:
    """Manages lifecycle of headless Anki desktop subprocess."""

    def __init__(self, client: Optional[AnkiConnectClient] = None):
        self.client = client or AnkiConnectClient()
        self._proc: Optional[subprocess.Popen] = None
        self._registered = False

    def ensure_running(self, timeout: float = 15.0) -> bool:
        # 1. Silently attach if Anki is already open externally
        if self.client.is_alive():
            return True

        # 2. Stage 1: Validate system binary
        sys.stdout.write(render_progress(15, "Locating 'anki' binary in PATH..."))
        sys.stdout.flush()

        anki_bin = shutil.which("anki")
        if not anki_bin:
            sys.stdout.write("\n")
            print(
                f"{C_RED}❌ 'anki' executable not found in PATH.{RESET}\n"
                "Ensure Anki desktop is installed and accessible via your PATH.",
                file=sys.stderr,
            )
            return False

        # 3. Stage 2: Configure environment & spawn subprocess
        sys.stdout.write(render_progress(35, "Configuring offscreen Qt environment..."))
        sys.stdout.flush()

        env = os.environ.copy()
        env["QT_QPA_PLATFORM"] = "offscreen"

        try:
            self._proc = subprocess.Popen(
                [anki_bin],
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception as err:
            sys.stdout.write("\n")
            print(f"{C_RED}❌ Failed to start Anki subprocess: {err}{RESET}", file=sys.stderr)
            return False

        self._register_hooks()
        sys.stdout.write(render_progress(50, f"Spawned headless Anki (PID: {self._proc.pid})..."))
        sys.stdout.flush()

        # 4. Stage 3: Polling loop with dynamic elapsed-time telemetry
        start_time = time.time()
        expected_window = 3.0  # Normalized duration for startup percentage calculation

        while time.time() - start_time < timeout:
            if self._proc.poll() is not None:
                sys.stdout.write("\n")
                print(
                    f"{C_RED}❌ Headless Anki exited unexpectedly (exit code {self._proc.returncode}).{RESET}",
                    file=sys.stderr,
                )
                self._proc = None
                return False

            if self.client.is_alive():
                elapsed = time.time() - start_time
                sys.stdout.write(
                    render_progress(100, f"Headless session ready (initialized in {elapsed:.1f}s).\n")
                )
                sys.stdout.flush()
                return True

            elapsed = time.time() - start_time
            # Incrementally interpolate progress between 50% and 95% while polling
            pct = min(95, 50 + int((elapsed / expected_window) * 45))
            sys.stdout.write(
                render_progress(
                    pct,
                    f"Awaiting AnkiConnect socket on 127.0.0.1:8765 ({elapsed:.1f}s)...",
                )
            )
            sys.stdout.flush()
            time.sleep(0.2)

        sys.stdout.write("\n")
        print(f"{C_RED}❌ Timed out waiting for AnkiConnect at {self.client.url}.{RESET}", file=sys.stderr)
        self.shutdown()
        return False

    def shutdown(self) -> None:
        if self._proc and self._proc.poll() is None:
            try:
                self._proc.terminate()
                self._proc.wait(timeout=3)
            except Exception:
                try:
                    self._proc.kill()
                except Exception:
                    pass
            self._proc = None

    def _register_hooks(self) -> None:
        if not self._registered:
            atexit.register(self.shutdown)
            signal.signal(signal.SIGTERM, self._signal_handler)
            signal.signal(signal.SIGINT, self._signal_handler)
            self._registered = True

    def _signal_handler(self, signum: int, frame: Any) -> None:
        self.shutdown()
        sys.exit(0)
