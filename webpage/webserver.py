import os
import socket
import subprocess

from flask import Flask, render_template, request

app = Flask(__name__)


def _get_local_ip():
    """Detect the local network IP address."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip


def _ensure_certificates(ip):
    """Generate mkcert certificates for the current IP if missing."""
    cert_name = f"{ip}-cert.pem"
    key_name = f"{ip}-key.pem"

    if not os.path.exists(cert_name) or not os.path.exists(key_name):
        print(f"Generating HTTPS certificate for {ip} using mkcert...")
        subprocess.run(["mkcert", ip, "localhost", "127.0.0.1"], check=True)

        # Rename mkcert output files
        for file in os.listdir("."):
            if file.endswith(".pem") and "+" in file:
                base = file.split("+")[0]
                cert_file = f"{base}+2.pem"
                key_file = f"{base}+2-key.pem"
                os.rename(cert_file, cert_name)
                os.rename(key_file, key_name)
                print(f"Certificate and key saved as {cert_name} and {key_name}.")
                break
    else:
        print(f"Certificate for {ip} already exists.")

    return cert_name, key_name


@app.route("/")
def home():
    return render_template("index.html")


def run_server():
    port = 5500
    ip = _get_local_ip()
    cert_name, key_name = _ensure_certificates(ip)
    app.run(host="0.0.0.0", port=port, ssl_context=(cert_name, key_name), debug=False)


if __name__ == "__main__":
    run_server()
