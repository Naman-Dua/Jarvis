import cv2

def scan_for_master():
    # Initialize the webcam
    cap = cv2.VideoCapture(0)
    # Load the pre-trained face detection model from OpenCV
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

    print("Vision: Scanning for Master...")
    
    # We'll try to find a face for a few seconds
    for _ in range(30): 
        ret, frame = cap.read()
        if not ret:
            break
            
        # Convert to grayscale for the math to work
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)

        if len(faces) > 0:
            cap.release()
            cv2.destroyAllWindows()
            return True
            
    cap.release()
    cv2.destroyAllWindows()
    return False