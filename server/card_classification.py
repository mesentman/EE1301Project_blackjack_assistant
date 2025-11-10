import sys

import numpy as np
from ultralytics import YOLO

MODEL = YOLO("runs/detect/train2/weights/best.pt")
MIN_CONFIDENCE = 0.5


def create_model(data: str):
    new_model = YOLO("yolo11n.pt")
    new_model.train(data=data, epochs=5)
    new_model.val()


def detect_cards(frame) -> tuple[dict[str, int], np.ndarray] | None:
    results = MODEL.predict(frame, verbose=False, conf=MIN_CONFIDENCE)
    if not results:
        return
    result = results[0]
    if not result.boxes:
        return
    types = result.names
    counts = result.boxes.cls.int().bincount()
    ret = {types.get(cid): min(count.item(), 1) for cid, count in enumerate(counts) if count > 0}
    return (ret, result.plot())


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python card_classification.py path/to/data.yaml")
        sys.exit(1)
    create_model(sys.argv[1])
