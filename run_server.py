import socket
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return '127.0.0.1'

def find_free_port(start_port=5000):
    for port in range(start_port, start_port + 20):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('127.0.0.1', port)) != 0:
                return port
    return start_port

if __name__ == '__main__':
    port = find_free_port(5000)
    lan_ip = get_local_ip()
    print("=" * 60)
    print("HOTEL COASTAL PALACE - FULL STACK SERVER")
    print("=" * 60)
    print(f"1. On this Laptop / PC:")
    print(f"   Website:  http://127.0.0.1:{port}/")
    print(f"   Admin:    http://127.0.0.1:{port}/admin")
    print()
    print(f"2. On Mobile Phones / Tablets (Same Wi-Fi Network):")
    print(f"   Website:  http://{lan_ip}:{port}/")
    print(f"   Admin:    http://{lan_ip}:{port}/admin")
    print()
    print(f"Admin Credentials: admin / coastal2026!")
    print("=" * 60)
    sys.stdout.flush()
    # Bind to 0.0.0.0 so other devices on same Wi-Fi can connect
    app.run(host='0.0.0.0', port=port, debug=False)

