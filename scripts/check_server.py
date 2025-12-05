#!/usr/bin/env python3
"""Test if the TPS server is running."""
import socket
import sys

def check_port(host='127.0.0.1', port=8000):
    """Check if a port is listening."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2)
    try:
        result = sock.connect_ex((host, port))
        if result == 0:
            print(f"✅ Port {port} is OPEN - server is running")
            return True
        else:
            print(f"❌ Port {port} is CLOSED - server not running")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        sock.close()

if __name__ == "__main__":
    if not check_port():
        print("\nTo start the server, run:")
        print("  cd /Users/zimeow/Joneshong/TPS")
        print("  uv run python -m uvicorn tps.app:app --host 127.0.0.1 --port 8000")
        sys.exit(1)
