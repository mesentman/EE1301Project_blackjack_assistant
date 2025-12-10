import subprocess
import re
import signal


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

    for line in process.stdout:

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
