# tftp_server.py

A portable, single-file TFTP server built on [tftpy](https://github.com/msoulier/tftpy). Drop it on any machine with Python 3 and go.

## Requirements

```bash
pip install tftpy
```

## Usage

```
python3 tftp_server.py [options]
```

### Options

| Flag | Default | Description |
|---|---|---|
| `-r`, `--root DIR` | Current directory | Root directory to serve files from |
| `-b`, `--bind ADDR` | `0.0.0.0` | IP address to bind to |
| `-p`, `--port PORT` | `69` | UDP port to listen on |
| `--read-only` | Off | Reject all WRQ (upload) requests |
| `--timeout SECS` | `60` | Per-transfer timeout |
| `--blksize BYTES` | `512` | TFTP block size (max 65464) |
| `-v`, `--verbose` | Off | Enable debug logging |

## Examples

```bash
# Serve current directory on all interfaces (requires root for port 69)
sudo python3 tftp_server.py

# Bind to a specific management interface
sudo python3 tftp_server.py -r /tftpboot -b 192.168.1.100

# High port — no root required
python3 tftp_server.py -r /tftpboot -p 6969

# Read-only with verbose logging
python3 tftp_server.py -r /tftpboot --read-only -v

# Larger block size for faster firmware transfers
sudo python3 tftp_server.py -r /tftpboot --blksize 1468
```

## Notes

- **Port 69** requires root (`sudo`) on Linux/macOS. Use `-p 6969` (or any port ≥ 1024) to run unprivileged.
- The root directory will be **created automatically** if it doesn't exist.
- Transfer progress is logged every 10% with human-readable sizes.
- Stop the server cleanly with `Ctrl-C` or `SIGTERM`.
- Block size `1468` is a common choice for LAN transfers to avoid IP fragmentation (1500 MTU − 20 IP − 8 UDP − 4 TFTP = 1468).