# tftp_server.py

A portable, single-file TFTP server built on [tftpy](https://github.com/msoulier/tftpy). Drop it on any machine with Python 3 and go.

## Requirements

It's recommended to run inside a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install tftpy
```

To deactivate the venv when done:

```bash
deactivate
```

If you'd prefer a global install:

```bash
pip install tftpy
```

> **Note:** On macOS/Linux, if running on port 69 with `sudo`, sudo won't inherit your activated venv. By default this uses a high port (`-p 6969`) to avoid sudo entirely, or invoke the venv Python directly: `sudo venv/bin/python3 tftp_server.py`.

## Usage

```
python3 tftp_server.py [options]
```

### Options

| Flag | Default | Description |
|---|---|---|
| `-r`, `--root DIR` | `./tftp-root` | Root directory to serve files from |
| `-b`, `--bind ADDR` | `0.0.0.0` | IP address to bind to |
| `-p`, `--port PORT` | `6969` | UDP port to listen on |
| `--read-only` | Off | Reject all WRQ (upload) requests |
| `--timeout SECS` | `60` | Per-transfer timeout |
| `--blksize BYTES` | `512` | TFTP block size (max 65464) |
| `-v`, `--verbose` | Off | Enable debug logging |

## Examples

```bash
# Serve tftp-root on all interfaces (requires root for port 69)
sudo venv/bin/python3 tftp_server.py

# Bind to a specific management interface
sudo venv/bin/python3 tftp_server.py -r /tftpboot -b 192.168.1.100

# High port — no root required (venv active)
python3 tftp_server.py -p 6969

# Read-only with verbose logging
python3 tftp_server.py --read-only -v

# Larger block size for faster firmware transfers
sudo venv/bin/python3 tftp_server.py --blksize 1468
```

## Notes

- **Port 69** requires root (`sudo`) on Linux/macOS. This uses `-p 6969` (or any port ≥ 1024) to run unprivileged.
- When using `sudo` with a venv, call `sudo venv/bin/python3` directly rather than activating the venv first — `sudo` doesn't inherit your shell environment.
- The root directory will be **created automatically** if it doesn't exist. Defaults to a `tftp-root` folder next to the script.
- Stop the server cleanly with `Ctrl-C` or `SIGTERM`.
- Block size `1468` is a common choice for LAN transfers to avoid IP fragmentation (1500 MTU − 20 IP − 8 UDP − 4 TFTP = 1468).
