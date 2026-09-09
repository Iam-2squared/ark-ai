"""Exercise the installed UI entrypoint and assets, including from a built wheel."""

import json
import socket
import subprocess
import sys
from contextlib import closing
from http.client import HTTPConnection
from time import monotonic, sleep


def main():
    with closing(socket.socket()) as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    # No user/model code is executed: this starts ARK's explicit deterministic mock.
    command = [sys.executable, "-m", "ark.ui.server", "--mock", "--port", str(port)]
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    try:
        deadline = monotonic() + 10
        while monotonic() < deadline:
            if process.poll() is not None:
                raise RuntimeError(process.stdout.read().decode("utf-8", errors="replace"))
            try:
                with closing(HTTPConnection("127.0.0.1", port, timeout=2)) as client:
                    client.request("GET", "/api/status")
                    response = client.getresponse()
                    status = json.loads(response.read())
                    assert response.status == 200
                    if status["state"] != "ready":
                        sleep(0.02)
                        continue
                break
            except (ConnectionError, OSError):
                sleep(0.02)
        else:
            raise RuntimeError("UI startup timed out")
        assert status["model"]["local_model"] is False
        for path in ("/", "/app.css", "/app.js", "/mark.svg"):
            with closing(HTTPConnection("127.0.0.1", port, timeout=2)) as client:
                client.request("GET", path)
                response = client.getresponse()
                assert response.status == 200 and response.read(), path
        print("Installed Local UI: loopback startup and all bundled assets PASS (MOCK ONLY)")
    finally:
        process.terminate()
        try:
            process.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.communicate(timeout=5)


if __name__ == "__main__":
    main()
