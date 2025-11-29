import io
import os
import ssl
from threading import Thread

import cv2
import numpy as np
import requests as r
import webserver
from card_classification import detect_cards
from dotenv import load_dotenv
from PIL import Image
from websockets import ConnectionClosedError
from websockets.sync.server import Server, serve

load_dotenv()

BASE_URL: str = "https://api.particle.io/v1/devices/"
DEVICE_ID: str = os.getenv("PARTICLE_DEVICE_ID", "")
PARTICLE_FUNCTION: str = "receive_cards"
ACCESS_TOKEN: str = os.getenv("PARTICLE_ACCESS_TOKEN", "")


SUIT_MAP: dict[str, int] = {"S": 0, "H": 1, "D": 2, "C": 3}
# fmt: off
RANK_MAP: dict[str, int] = {
    "A": 0, "2": 1, "3": 2, "4": 3, "5": 4, "6": 5, "7": 6,
    "8": 7, "9": 8, "10": 9, "J": 10, "Q": 11, "K": 12
}
# fmt: on


def card_to_int(card: str) -> int:
    suit = card[-1]
    rank = card[:-1]
    return SUIT_MAP[suit] * 13 + RANK_MAP[rank]


def format_cards_for_particle(cards: dict[str, int]) -> str:
    # TODO:  This assumes half and half split between player and dealer
    card_list = [card_to_int(c) for c in cards.keys()]
    mid = len(card_list) // 2
    player_cards = card_list[:mid]
    dealer_cards = card_list[mid:]
    player_str = ",".join(str(c) for c in player_cards)
    dealer_str = ",".join(str(c) for c in dealer_cards)
    return f"{player_str}|{dealer_str}"


def receive(websocket):
    prev_timestamp = None
    print("WebSocket Connection Established.")
    try:
        for message in websocket:
            timestamp_ms = int.from_bytes(message[:8])
            if not prev_timestamp:
                prev_timestamp = timestamp_ms
            # Artificial Frame Limiting to ~8 FPS
            if timestamp_ms - prev_timestamp < 125:
                continue
            prev_timestamp = timestamp_ms
            data = message[8:]
            img = Image.open(io.BytesIO(data))
            frame = np.array(img)[:, :, ::-1]
            result = detect_cards(frame)
            if not result:
                continue
            cards, display = result
            print(cards)
            formatted = format_cards_for_particle(cards)
            print(formatted)
            cv2.imshow("Live Image", display)
            cv2.waitKey(1)
            if cards:
                r.post(
                    url=BASE_URL + DEVICE_ID + "/" + PARTICLE_FUNCTION,
                    headers={"Authorization": "Bearer " + ACCESS_TOKEN},
                    data={"arg": formatted},
                )
    except ConnectionClosedError:
        print("WebSocket Connection Closed.")


def run_websocket(server: Server):
    with server:
        server.serve_forever()


def main():
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ssl_context.load_cert_chain(certfile=webserver.CERT_NAME, keyfile=webserver.KEY_NAME)
    server = serve(receive, webserver.IP, 8001, ssl=ssl_context)
    Thread(name="WebSocketServerThread", target=run_websocket, daemon=True, args=(server,)).start()
    webserver.run_server()
    server.shutdown()


if __name__ == "__main__":
    main()
    # print("Starting")
    # average_time = 0
    # n = 25
    # for i in range(n):
    #     start = time.time()
    #     detect_cards("frame.jpg")
    #     average_time += time.time() - start
    # print(f"Average detection time: {average_time / n:.3f} seconds")
