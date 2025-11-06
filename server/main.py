import io
import ssl
from multiprocessing.managers import Server
from threading import Thread

import cv2
import numpy as np
import requests as r
import webserver
from card_classification import detect_cards
from PIL import Image
from websockets import ConnectionClosedError
from websockets.sync.server import serve

BASE_URL: str = "https://api.particle.io/v1/devices/"
DEVICE_ID: str = ""
PARTICLE_FUNCTION: str = ""
ACCESS_TOKEN: str = ""  # Don't want to actually store this here


def receive(websocket):
    try:
        for message in websocket:
            img = Image.open(io.BytesIO(message))
            frame = np.array(img)[:, :, ::-1]
            ret, display = detect_cards(frame)
            print(ret)
            cv2.imshow("Live Image", display)
            cv2.waitKey(1)
            # r.post(
            #     url=BASE_URL + DEVICE_ID + "/" + PARTICLE_FUNCTION,
            #     headers={"Authorization": "Bearer " + ACCESS_TOKEN},
            #     data={"arg": str(ret)},
            # )
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
