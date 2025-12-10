import numpy as np
from ultralytics import YOLO

MODEL = YOLO("yolov8m_synthetic.pt")
MIN_CONFIDENCE = 0.35


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
