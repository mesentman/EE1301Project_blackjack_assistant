import os
import socket
import subprocess

from flask import Flask, render_template, request

app = Flask(__name__)


def get_local_ip():
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


def ensure_certificates(ip):
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


@app.route("/upload", methods=["POST"])
def upload_frame():
    # This is pretty damn slow sending jpeg images one at a time with http.
    # Probably want to look into real time data transfer with sockets.
    print("Received frame!")
    frame = request.data  # binary JPEG
    with open("frame.jpg", "wb") as f:
        f.write(frame)
    return "OK", 200


def main():
    port = 5500
    ip = get_local_ip()
    cert_name, key_name = ensure_certificates(ip)
    app.run(host="0.0.0.0", port=port, ssl_context=(cert_name, key_name), debug=False)


if __name__ == "__main__":
    main()
