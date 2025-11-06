import sys

from ultralytics import YOLO

model = YOLO("runs/detect/train/weights/best.pt")


def create_model(data: str):
    new_model = YOLO("yolo11n.pt")
    new_model.train(data=data, epochs=5)
    new_model.val()


def detect_cards(frame):
    results = model.predict(frame, verbose=False)
    if not results:
        return
    result = results[0]
    types = result.names
    counts = result.boxes.cls.int().bincount()
    ret = {types.get(cid): count.item() for cid, count in enumerate(counts) if count > 0}
    print(ret)
    return result


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python card_classification.py path/to/data.yaml")
        sys.exit(1)
    create_model(sys.argv[1])
