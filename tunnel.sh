./cloudflared-linux-amd64 tunnel --url http://localhost:8001
./cloudflared-linux-amd64 tunnel --url http://localhost:5500
python server/main.py --tunnel
