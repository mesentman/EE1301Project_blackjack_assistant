from threading import Thread

import webserver
from card_classification import detect_cards
from websockets.sync.server import serve


def receive(websocket):
    for message in websocket:
        with open("frame.jpg", "wb") as f:
            f.write(message)


def main():
    Thread(name="FlaskServerThread", target=webserver.run_server, daemon=True).start()
    with serve(receive, "localhost", 8001) as server:
        server.serve_forever()


if __name__ == "__main__":
    # main()
    detect_cards("frame.jpg")
