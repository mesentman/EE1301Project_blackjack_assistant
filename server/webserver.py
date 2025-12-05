import os
import socket
import ssl
import subprocess
from turtle import ht

from flask import Flask, render_template

from main import WEBSOCKET_PORT


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
    """Generate mkcert certificates for the current IP if missing and cleanup old ones."""
    cert_name = f"{ip}-cert.pem"
    key_name = f"{ip}-key.pem"

    # Clean up old certificates for other IPs
    for file in os.listdir("."):
        if file.endswith(("-cert.pem", "-key.pem")) and not file.startswith(ip):
            print(f"Removing old certificate file: {file}")
            os.remove(file)

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


APP = Flask(__name__)
PORT = 5500
IP = _get_local_ip()
CERT_NAME, KEY_NAME = _ensure_certificates(IP)
ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
ssl_context.load_cert_chain(certfile=CERT_NAME, keyfile=KEY_NAME)
using_tunnel = False
external_ip = "asdf.trycloudflare.com"


@APP.route("/")
def home():
    if using_tunnel:
        return render_template("index.html", ip=external_ip)
    else:
        return render_template("index.html", ip=IP + ":" + str(WEBSOCKET_PORT))


def run_server(tunnel: bool, ip: str):
    global using_tunnel, external_ip
    using_tunnel = tunnel
    if tunnel:
        external_ip = ip.removeprefix("https://")
        APP.run(port=PORT, debug=False)
    else:
        APP.run(host="0.0.0.0", port=PORT, ssl_context=(CERT_NAME, KEY_NAME), debug=False)


if __name__ == "__main__":
    run_server()
