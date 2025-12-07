import sys

import numpy as np
from ultralytics import YOLO

MODEL = YOLO("yolov8m_synthetic.pt")
MIN_CONFIDENCE = 0.35


def create_model(data: str):
    new_model = YOLO("yolo11n.pt")
    new_model.train(data=data, epochs=5)
    new_model.val()


def detect_cards(frame) -> tuple[dict[str, int], dict[str, int], np.ndarray] | None:
    results = MODEL.predict(frame, verbose=False, conf=MIN_CONFIDENCE)
    if not results:
        return
    result = results[0]
    if not result.boxes:
        return

    frame_height = frame.shape[0]
    midpoint = frame_height / 2
    types = result.names

    dealer_cards: dict[str, int] = {}
    player_cards: dict[str, int] = {}

    for box, cls in zip(result.boxes.xyxy, result.boxes.cls):
        y_center = (box[1] + box[3]) / 2
        card_name = types.get(int(cls.item()))
        if card_name in dealer_cards or card_name in player_cards:
            continue
        if y_center < midpoint:
            dealer_cards[card_name] = 1
        else:
            player_cards[card_name] = 1

    return (dealer_cards, player_cards, result.plot())


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python card_classification.py path/to/data.yaml")
        sys.exit(1)
    create_model(sys.argv[1])
