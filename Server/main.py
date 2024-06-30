print("\033[92m {}\033[00m".format("Program Started"))
from flask import Flask, request, Response,jsonify
import numpy as np
import cv2
from ultralytics import YOLO
from sort import Sort

print("\033[92m {}\033[00m".format("All Modules Imported Successfully"))


# Model Loading
model = YOLO("yolov8n.pt", verbose=False)
print("\033[92m {}\033[00m".format("Model Loaded Successfully"))

tracker = Sort(max_age=20, min_hits=10, iou_threshold=0.3)
unique_ids = []

app = Flask(__name__)


class RoutesHandles:
    def __init__(self) -> None:
        self.person_count = 0
    
    def upload(self):
        try:
            response = {
                'error' : False,
                'quit' : False,
                'persons' : 0,
                'greet' : False
            }
            data = request.data
            np_arr = np.frombuffer(data, np.uint8)
            img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

            results = model(img, stream=True, verbose=False)
            detections = np.empty((0, 5))
            self.person_count = 0

            for r in results:
                Boxes = r.boxes
                for box in Boxes:
                    confidence = round(float(box.conf[0]) * 100) / 100
                    is_confident = confidence >= 0.6
                    is_person = int(box.cls[0]) == 0
                    if is_person and is_confident:
                        self.person_count += 1 
                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        current_array = np.array([x1, y1, x2, y2, confidence])
                        detections = np.vstack((detections, current_array))

            results_tracker = tracker.update(detections)
            response['persons']  = self.person_count
            for res in results_tracker:
                x1, y1, x2, y2, id = map(int, res)
                extracted_img = img[y1:y2, x1:x2]
                if id not in unique_ids and extracted_img.size > 0:
                    unique_ids.append(id)
                    response['greet'] = True
            if cv2.waitKey(1) & 0xFF == ord('q'):
                # return Response('Quit', status=200)
                response['quit'] = True
            return jsonify(response)

        except Exception as e:
            response['error'] = True
            response['quit'] = True
            return jsonify(response)
   
        
if __name__ == '__main__':
    routes_handles = RoutesHandles()
    app.add_url_rule('/upload', view_func=routes_handles.upload, methods=['POST'])
    app.run(host='0.0.0.0', port=5000)