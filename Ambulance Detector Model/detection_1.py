from ultralytics import YOLO
import cv2
 
# Load trained model
model = YOLO("signal/ambulance_model.pt")
 
# Load video
cap = cv2.VideoCapture("signal/test_1.mp4")
 
if not cap.isOpened():
    print("Error: Could not open video file.")
    exit()
 
frame_count = 0  # For frame skipping
 
while True:
    ret, frame = cap.read()
    if not ret:
        break
 
    frame_count += 1
 
    # Skip every alternate frame (improves speed significantly)
    if frame_count % 2 != 0:
        continue
 
    # Resize frame for faster inference
    frame_resized = cv2.resize(frame, (1920,1080))
 
    # Run detection at smaller inference size
    results = model(frame_resized, imgsz=320)
 
    ambulance_detected = False
 
    for r in results:
        for box in r.boxes:
            confidence = float(box.conf[0])
 
            if confidence > 0.5:
                ambulance_detected = True
 
                x1, y1, x2, y2 = map(int, box.xyxy[0])
 
                cv2.rectangle(frame_resized, (x1, y1), (x2, y2), (0, 0, 255), 2)
                cv2.putText(frame_resized,
                            f"Ambulance {confidence:.2f}",
                            (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.6,
                            (0, 0, 255),
                            2)
 
    if ambulance_detected:
        print("ambulance detected")
 
    cv2.imshow("Detection", frame_resized)
 
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
 
cap.release()
cv2.destroyAllWindows()