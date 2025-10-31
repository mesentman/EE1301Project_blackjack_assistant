import sys

from ultralytics import YOLO


def create_model(data: str):
    model = YOLO("yolo11n.pt")
    model.train(data=data, epochs=5)
    model.val()
    results = model("frame.jpg")
    for result in results:
        result.show()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python card_classification.py path/to/data.yaml")
        sys.exit(1)
    create_model(sys.argv[1])
