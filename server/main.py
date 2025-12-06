import io
import os
import sys
from threading import Thread

import numpy as np
import requests as r
from tunnel import start_tunnel, stop_tunnel
import webserver
from card_classification import detect_cards
from collections import Counter
from dotenv import load_dotenv
from PIL import Image
from websockets import ConnectionClosedError
from websockets.sync.server import Server, serve

load_dotenv()

BASE_URL: str = "https://api.particle.io/v1/devices/"
DEVICE_ID: str = os.getenv("PARTICLE_DEVICE_ID", "")
PARTICLE_FUNCTION: str = "receive_cards"
ACCESS_TOKEN: str = os.getenv("PARTICLE_ACCESS_TOKEN", "")
BITLY_TOKEN: str = os.getenv("BITLY_ACCESS_TOKEN", "")
WEBSOCKET_PORT: int = 8001

HAND_HISTORY_SIZE: int = 15
MIN_MODE_COUNT: int = 10
MIN_CARDS_DETECTED: int = 1
MAX_FPS = 30


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


def format_cards_for_particle(dealer_cards: dict[str, int], player_cards: dict[str, int]) -> str:
    player_list = [card_to_int(c) for c in player_cards.keys()]
    dealer_list = [card_to_int(c) for c in dealer_cards.keys()]
    player_str = ",".join(str(c) for c in player_list)
    dealer_str = ",".join(str(c) for c in dealer_list)
    return f"{player_str}|{dealer_str}"


def hand_to_key(dealer_cards: dict[str, int], player_cards: dict[str, int]) -> tuple[tuple[str, ...], tuple[str, ...]]:
    return (tuple(sorted(dealer_cards.keys())), tuple(sorted(player_cards.keys())))


def get_stable_hand(
    hand_history: list[tuple[tuple[str, ...], tuple[str, ...]]],
) -> tuple[tuple[str, ...], tuple[str, ...]] | None:
    if len(hand_history) < HAND_HISTORY_SIZE:
        return None
    counter = Counter(hand_history)
    mode, count = counter.most_common(1)[0]
    if count < MIN_MODE_COUNT:
        return None
    total_cards = len(mode[0]) + len(mode[1])
    if total_cards < MIN_CARDS_DETECTED:
        return None
    return mode


def receive(websocket):
    prev_timestamp = None
    hand_history: list[tuple[tuple[str, ...], tuple[str, ...]]] = []
    last_sent_hand: tuple[tuple[str, ...], tuple[str, ...]] | None = None
    print("WebSocket Connection Established.")
    try:
        for message in websocket:
            timestamp_ms = int.from_bytes(message[:8])
            if not prev_timestamp:
                prev_timestamp = timestamp_ms
            # Artificial Frame Limiting to ~8 FPS
            if timestamp_ms - prev_timestamp < (1 / MAX_FPS) * 1000:
                continue
            prev_timestamp = timestamp_ms
            data = message[8:]
            img = Image.open(io.BytesIO(data))
            frame = np.array(img)[:, :, ::-1]
            result = detect_cards(frame)
            if not result:
                continue
            dealer_cards, player_cards, display = result

            print(f"Detected - Dealer: {dealer_cards}, Player: {player_cards}")
            hand_key = hand_to_key(dealer_cards, player_cards)
            hand_history.append(hand_key)
            if len(hand_history) > HAND_HISTORY_SIZE:
                hand_history.pop(0)

            stable_hand = get_stable_hand(hand_history)
            if not stable_hand or stable_hand == last_sent_hand:
                continue

            last_sent_hand = stable_hand
            stable_dealer = {card: 1 for card in stable_hand[0]}
            stable_player = {card: 1 for card in stable_hand[1]}
            print(f"Dealer: {stable_dealer}, Player: {stable_player}")
            formatted = format_cards_for_particle(stable_dealer, stable_player)
            print(formatted)
            resp = r.post(
                url=BASE_URL + DEVICE_ID + "/" + PARTICLE_FUNCTION,
                headers={"Authorization": "Bearer " + ACCESS_TOKEN},
                data={"arg": formatted},
            )
            print(resp.text)
            print(resp.url)
    except ConnectionClosedError:
        print("WebSocket Connection Closed.")


def run_websocket(server: Server):
    with server:
        server.serve_forever()


def process_request(path, request_headers):
    return None


def shorten_url(long_url: str) -> str:
    api_url = "https://api-ssl.bitly.com/v4/shorten"
    headers = {"Authorization": f"Bearer {BITLY_TOKEN}", "Content-Type": "application/json"}
    data = {"long_url": long_url}
    response = r.post(api_url, json=data, headers=headers)
    return response.json().get("link")


def main():
    tunnel = False
    ws_url = ""
    if len(sys.argv) > 2 and sys.argv[1] == "--tunnel":
        cloudflared = sys.argv[2]
        local_url = "127.0.0.1"
        tunnel = True
        ws_url, ws_proc = start_tunnel(cloudflared, f"http://{local_url}:{WEBSOCKET_PORT}")
        live_url, https_proc = start_tunnel(cloudflared, f"http://{local_url}:{webserver.PORT}")
        server = serve(receive, "127.0.0.1", WEBSOCKET_PORT, process_request=process_request)
    else:
        server = serve(receive, webserver.IP, WEBSOCKET_PORT, ssl=webserver.ssl_context)
    Thread(name="WebSocketServerThread", target=run_websocket, daemon=True, args=(server,)).start()
    if tunnel:
        print(f"Live server running at url: {shorten_url(live_url)}")
    webserver.run_server(tunnel, ws_url)
    server.shutdown()
    if tunnel:
        stop_tunnel(ws_proc)
        stop_tunnel(https_proc)


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
