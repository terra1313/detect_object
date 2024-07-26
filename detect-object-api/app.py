import cv2
import numpy as np
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uuid


class Block(BaseModel):
    x: int = 10
    y: int = 10
    w: int = 10
    h: int = 10
    label: str = "tomato"


class OutputData(BaseModel):
    blocks: list[Block] = [{"x": 10, "y": 10, "w": 50, "h": 20, "label": "car"}]


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost.tiangolo.com",
        "https://localhost.tiangolo.com",
        "http://localhost",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Chargement des classes
with open("src/coco.names", "r") as f:
    classes = [line.strip() for line in f.readlines()]

net = cv2.dnn.readNetFromDarknet("src/yolov3.cfg", "src/yolov3.weights")
net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
ln = net.getLayerNames()
ln = [ln[i - 1] for i in net.getUnconnectedOutLayers()]


@app.post("/detect/")
async def detect_objects(file: UploadFile = File(...)):
    # Chargement de l'image
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    height, width, channels = image.shape

    # Détection
    blob = cv2.dnn.blobFromImage(
        image, 0.00392, (416, 416), (0, 0, 0), True, crop=False
    )
    net.setInput(blob)
    outs = net.forward(ln)

    # Analyse des résultats
    class_ids = []
    confidences = []
    boxes = []

    for out in outs:
        for detection in out:
            scores = detection[5:]
            class_id = np.argmax(scores)
            confidence = scores[class_id]
            if confidence > 0.5:
                # Extraction des coordonnées du rectangle délimitant
                center_x = int(detection[0] * width)
                center_y = int(detection[1] * height)
                w = int(detection[2] * width)
                h = int(detection[3] * height)

                x = int(center_x - w / 2)
                y = int(center_y - h / 2)

                boxes.append([x, y, w, h])
                confidences.append(float(confidence))
                class_ids.append(class_id)

    # Application de la suppression de non-maxima
    indexes = cv2.dnn.NMSBoxes(boxes, confidences, 0.5, 0.4)
    BOXS = []
    for i in range(len(boxes)):
        if i in indexes:
            x, y, w, h = boxes[i]
            BOXS.append((x, y, w, h, class_ids[i]))

    # Dessin des rectangles et des labels sur l'image
    font = cv2.FONT_HERSHEY_PLAIN
    colors = np.random.uniform(0, 255, size=(len(classes), 3))

    final_image = image.copy()
    for i in range(len(BOXS)):
        x, y, w, h, id = BOXS[i]
        label = str(classes[id])
        color = colors[id]
        cv2.rectangle(final_image, (x, y), (x + w, y + h), color, 1)
        cv2.putText(image, label, (x, y - 10), font, 1, color, 1)

    # Sauvegarde de l'image modifiée
    uuid1 = uuid.uuid1()
    final_image_path = f"final.{uuid1}.jpg"
    cv2.imwrite(final_image_path, image)

    # Retourner l'image modifiée
    return FileResponse(final_image_path)


@app.post("/detect/block/")
async def detect_objects_block(file: UploadFile = File(...)):
    # Chargement de l'image
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    height, width, _ = image.shape

    # Détection
    blob = cv2.dnn.blobFromImage(
        image, 0.00392, (416, 416), (0, 0, 0), True, crop=False
    )
    net.setInput(blob)
    outs = net.forward(ln)

    # Analyse des résultats
    class_ids = []
    confidences = []
    boxes = []

    for out in outs:
        for detection in out:
            scores = detection[5:]
            class_id = np.argmax(scores)
            confidence = scores[class_id]
            if confidence > 0.5:
                # Extraction des coordonnées du rectangle délimitant
                center_x = int(detection[0] * width)
                center_y = int(detection[1] * height)
                w = int(detection[2] * width)
                h = int(detection[3] * height)

                x = int(center_x - w / 2)
                y = int(center_y - h / 2)

                boxes.append([x, y, w, h])
                confidences.append(float(confidence))
                class_ids.append(class_id)

    # Application de la suppression de non-maxima
    indexes = cv2.dnn.NMSBoxes(boxes, confidences, 0.5, 0.4)
    BOXS = []
    for i in range(len(boxes)):
        if i in indexes:
            x, y, w, h = boxes[i]
            BOXS.append((x, y, w, h, class_ids[i]))

    output = []
    for i in range(len(BOXS)):
        x, y, w, h, id = BOXS[i]
        output.append({"x": x, "y": y, "w": w, "h": h, "label": str(classes[id])})

    return output