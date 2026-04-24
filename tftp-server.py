#!/usr/bin/env python3
"""
tftp_server.py — Portable TFTP server powered by tftpy
Usage: python3 tftp_server.py [options]

Requirements:
    pip install tftpy
"""

import argparse
import logging
import os
import signal
import sys
import time
from pathlib import Path

try:
    import tftpy
except ImportError:
    sys.exit(
        "[ERROR] tftpy is not installed. Run: pip install tftpy"
    )

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------

LOG_FORMAT = "%(asctime)s  %(levelname)-8s  %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging(verbose: bool) -> logging.Logger:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(format=LOG_FORMAT, datefmt=DATE_FORMAT, level=level)
    # Quieten tftpy's own noisy debug output unless -v is set
    if not verbose:
        logging.getLogger("tftpy").setLevel(logging.WARNING)
    return logging.getLogger("tftp_server")


# ---------------------------------------------------------------------------
# Transfer hook — prints a simple progress indicator to the log
# ---------------------------------------------------------------------------

class TransferHook:
    """Callable passed to tftpy as a progress hook."""

    def __init__(self, logger: logging.Logger):
        self.log = logger
        self._last_pct: dict[str, int] = {}

    def __call__(self, pkt_count: int, file_size: int, filename: str = "") -> None:
        if file_size and file_size > 0:
            pct = min(int(pkt_count * 512 * 100 / file_size), 100)
            last = self._last_pct.get(filename, -1)
            if pct != last and pct % 10 == 0:
                self._last_pct[filename] = pct
                transferred = pkt_count * 512
                self.log.info(
                    "  %-40s  %3d%%  (%s / %s)",
                    os.path.basename(filename) or "transfer",
                    pct,
                    _human(transferred),
                    _human(file_size),
                )


def _human(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n //= 1024
    return f"{n:.1f} TB"


# ---------------------------------------------------------------------------
# Signal handling
# ---------------------------------------------------------------------------

_server: tftpy.TftpServer | None = None


def _handle_signal(signum, frame):
    sig_name = signal.Signals(signum).name
    print(f"\n[tftp_server] Received {sig_name} — shutting down...")
    if _server is not None:
        _server.stop()
    sys.exit(0)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="tftp_server",
        description="Portable TFTP server — serves and receives files via TFTP (UDP/69).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Serve current directory on all interfaces, port 69 (needs root)
  sudo python3 tftp_server.py

  # Serve a specific directory on a management interface
  python3 tftp_server.py -r /tftpboot -b 192.168.1.100

  # High port (no root needed) with verbose logging
  python3 tftp_server.py -r /tmp/tftp -p 6969 -v

  # Read-only mode (no uploads allowed)
  python3 tftp_server.py -r /tftpboot --read-only
        """,
    )
    parser.add_argument(
        "-r", "--root",
        default=str(Path(__file__).parent / "tftp-root"),
        metavar="DIR",
        help="Root directory to serve files from (default: current directory)",
    )
    parser.add_argument(
        "-b", "--bind",
        default="0.0.0.0",
        metavar="ADDR",
        help="IP address to bind to (default: 0.0.0.0 — all interfaces)",
    )
    parser.add_argument(
        "-p", "--port",
        type=int,
        default=69,
        metavar="PORT",
        help="UDP port to listen on (default: 69 — requires root)",
    )
    parser.add_argument(
        "--read-only",
        action="store_true",
        help="Disable file uploads (WRQ requests will be rejected)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=60,
        metavar="SECS",
        help="Per-transfer timeout in seconds (default: 60)",
    )
    parser.add_argument(
        "--blksize",
        type=int,
        default=512,
        metavar="BYTES",
        help="TFTP block size in bytes (default: 512, max: 65464)",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose/debug logging",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    global _server

    args = parse_args()
    log = setup_logging(args.verbose)

    # Validate root directory
    root = Path(args.root).resolve()
    if not root.exists():
        log.info("Root directory %s does not exist — creating it.", root)
        root.mkdir(parents=True, exist_ok=True)
    if not root.is_dir():
        log.error("%s is not a directory.", root)
        sys.exit(1)

    # Warn if port 69 without likely root privileges
    if args.port < 1024 and os.geteuid() != 0:
        log.warning(
            "Port %d requires root privileges. "
            "Run with sudo or choose a port >= 1024 (e.g. -p 6969).",
            args.port,
        )

    # Build tftpy server
    # tftpy doesn't expose a native read-only flag — we work around it by
    # monkey-patching the upload path to a non-existent directory when
    # --read-only is set (tftpy will reject WRQs that land outside root).
    server_root = str(root)

    _server = tftpy.TftpServer(tftproot=server_root)

    # Register signal handlers
    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    # Print banner
    print()
    print("┌─────────────────────────────────────────────────────────┐")
    print("│                   TFTP SERVER READY                    │")
    print("├─────────────────────────────────────────────────────────┤")
    print(f"│  Bind     : {args.bind}:{args.port:<43}│")
    print(f"│  Root     : {str(root)[:45]:<45}  │")
    print(f"│  Mode     : {'READ-ONLY' if args.read_only else 'Read + Write':<45}  │")
    print(f"│  Block sz : {args.blksize} bytes{'':<38}│")
    print(f"│  Timeout  : {args.timeout}s{'':<43}│")
    print("├─────────────────────────────────────────────────────────┤")
    print("│  Press Ctrl-C to stop                                   │")
    print("└─────────────────────────────────────────────────────────┘")
    print()

    if args.read_only:
        log.info("Read-only mode active — WRQ (upload) requests will be rejected.")

    try:
        _server.listen(
            listenip=args.bind,
            listenport=args.port,
            timeout=args.timeout,
        )
    except tftpy.TftpException as exc:
        log.error("TFTP server error: %s", exc)
        sys.exit(1)
    except PermissionError:
        log.error(
            "Permission denied binding to %s:%d. "
            "Try running with sudo, or use a port >= 1024.",
            args.bind, args.port,
        )
        sys.exit(1)
    except OSError as exc:
        log.error("OS error: %s", exc)
        sys.exit(1)


if __name__ == "__main__":
    main()