import atexit
import os
import shutil
import signal
import subprocess
import sys
import time
from typing import Any, Optional
from clanki.client.anki_connect import AnkiConnectClient
from clanki.ui.theme import C_CYAN, C_GREEN, C_RED, RESET

class AnkiProcessManager:
    """Manages lifecycle of headless Anki desktop subprocess."""

    def __init__(self, client: Optional[AnkiConnectClient] = None):
        self.client = client or AnkiConnectClient()
        self._proc: Optional[subprocess.Popen] = None
        self._registered = False

    def ensure_running(self, timeout: float = 15.0) -> bool:
        # Reuse existing desktop or headless instance
        if self.client.is_alive():
            return True

        anki_bin = shutil.which("anki")
        if not anki_bin:
            print(
                f"\n{C_RED}❌ 'anki' executable not found in PATH.{RESET}\n"
                "Ensure Anki desktop is installed and accessible via your PATH.",
                file=sys.stderr,
            )
            return False

        print(
            f"\n{C_CYAN}🔄 Starting headless Anki session in background (QT_QPA_PLATFORM=offscreen)...{RESET}",
            end="",
            flush=True,
        )

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
            print(f"\n{C_RED}❌ Failed to start Anki subprocess: {err}{RESET}", file=sys.stderr)
            return False

        self._register_hooks()

        start_time = time.time()
        while time.time() - start_time < timeout:
            if self._proc.poll() is not None:
                print(
                    f"\n{C_RED}❌ Headless Anki exited unexpectedly (exit code {self._proc.returncode}).{RESET}",
                    file=sys.stderr,
                )
                self._proc = None
                return False

            if self.client.is_alive():
                print(f" {C_GREEN}ready!{RESET}")
                return True

            time.sleep(0.4)

        print(f"\n{C_RED}❌ Timed out waiting for AnkiConnect at {self.client.url}.{RESET}", file=sys.stderr)
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
