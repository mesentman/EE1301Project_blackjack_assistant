import io
import ssl
from threading import Thread

import cv2
import numpy as np
import webserver
from card_classification import detect_cards
from PIL import Image
from websockets.sync.server import serve


def receive(websocket):
    for message in websocket:
        img = Image.open(io.BytesIO(message))
        frame = np.array(img)[:, :, ::-1]
        res = detect_cards(frame).plot()
        cv2.imshow("Live Image", res)
        cv2.waitKey(1)


def main():
    Thread(name="FlaskServerThread", target=webserver.run_server, daemon=True).start()
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ssl_context.load_cert_chain(certfile=webserver.CERT_NAME, keyfile=webserver.KEY_NAME)
    with serve(receive, webserver.IP, 8001, ssl=ssl_context) as server:
        server.serve_forever()


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
