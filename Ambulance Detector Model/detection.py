from ultralytics import YOLO
import cv2

# Load your trained model
model = YOLO("signal/ambulance_model.pt")

# Load MP4 file instead of webcam
cap = cv2.VideoCapture("signal/test_1.mp4")

if not cap.isOpened():
    print("Error: Could not open video file.")
    exit()

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Run detection
    results = model(frame)

    ambulance_detected = False

    for r in results:
        for box in r.boxes:
            confidence = float(box.conf[0])

            if confidence > 0.5:
                ambulance_detected = True

                x1, y1, x2, y2 = map(int, box.xyxy[0])

                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
                cv2.putText(frame,
                            f"Ambulance {confidence:.2f}",
                            (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.7,
                            (0, 0, 255),
                            2)

    if ambulance_detected:
        print("ambulance detected")

    cv2.imshow("Detection", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
