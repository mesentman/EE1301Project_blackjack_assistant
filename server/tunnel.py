import subprocess
import re
import time
import signal
import sys


def start_tunnel(cloudflared_path, local_url):
    process = subprocess.Popen(
        [cloudflared_path, "tunnel", "--url", local_url],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    url_pattern = re.compile(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com")

    print("Starting cloudflared tunnel...")

    tunnel_url = None

    # Read cloudflared output line-by-line until the URL appears
    for line in process.stdout:
        # print("CF:", line.strip())  # optional logging

        match = url_pattern.search(line)
        if match:
            tunnel_url = match.group(0)
            break

    return tunnel_url, process


def stop_tunnel(process):
    print("Stopping cloudflared...")
    try:
        process.send_signal(signal.SIGTERM)
        process.wait(timeout=5)
    except Exception:
        process.kill()


# ------------------------------
# Example usage
# ------------------------------

if __name__ == "__main__":
    url, proc = start_tunnel()
    print("Tunnel is live at:", url)

    try:
        # Your app logic here
        print("Doing stuff with the tunnel...")
        time.sleep(5)  # Replace with your real app code

    finally:
        stop_tunnel(proc)
        print("Tunnel closed.")
