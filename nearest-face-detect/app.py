import cv2, time

# Load pre-trained face detection model (Haar Cascade)
face_classifier = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)

# Init video capture using webcam (commented set resolution to 320x240 for performance to use to RPi)
video_capture = cv2.VideoCapture(0)
# video_capture.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
# video_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)


# Function to detect the nearest (largest) face in the frame
def detect_nearest_face(vid):
    gray_image = cv2.cvtColor(vid, cv2.COLOR_BGR2GRAY)
    faces = face_classifier.detectMultiScale(gray_image, 1.1, 5, minSize=(40, 40))

    if len(faces) == 0:
        return None

    return max(faces, key=lambda rect: rect[2] * rect[3])


# Create a KCF (fast), MOSSE (faster) or CSRT (more accurate) tracker based on installation
## Checking for legacy first to increase compatibility with older OpenCV versions
def create_tracker():
    if hasattr(cv2, "legacy") and hasattr(
        cv2.legacy, "TrackerKCF_create"
    ):  # Old version of KCF in new OpenCV
        print("Using legacy KCF tracker")
        return cv2.legacy.TrackerKCF_create()

    if hasattr(cv2, "TrackerKCF_create"):  # Supported version of KCF in new OpenCV
        print("Using KCF tracker")
        return cv2.TrackerKCF_create()

    if hasattr(cv2, "legacy") and hasattr(
        cv2.legacy, "TrackerMOSSE_create"
    ):  # Old version of MOSSE in new OpenCV
        print("Using tracker: MOSSE (legacy)")
        return cv2.legacy.TrackerMOSSE_create()

    if hasattr(cv2, "TrackerMOSSE_create"):  # Supported version of MOSSE in new OpenCV
        print("Using tracker: MOSSE")
        return cv2.TrackerMOSSE_create()

    if hasattr(cv2, "legacy") and hasattr(
        cv2.legacy, "TrackerCSRT_create"
    ):  # Old version of CSRT in new OpenCV
        print("Using legacy CSRT tracker")
        return cv2.legacy.TrackerCSRT_create()

    if hasattr(cv2, "TrackerCSRT_create"):  # Supported version of CSRT in new OpenCV
        print("Using CSRT tracker")
        return cv2.TrackerCSRT_create()

    raise RuntimeError("No CSRT / KCF / MOSSE tracker found in installation")


tracker = None
locked = False  # currently locked to a face
lost_since = None  # time since losing lock
REDETECT_DELAY = 2.0  # seconds to wait before re-detecting after losing lock
WIN, last_print = "Face Detection and Lock-On", 0

print("--------------- Acquiring Face Lock ---------------")
while True:
    result, vid_frame = video_capture.read()  # read frames from video
    if not result:
        break  # terminate loop if frame not read successfully

    H, W = vid_frame.shape[:2]  # take H and W of frame (window) for bounds checking

    if not locked:  # Detection phase
        bbox = detect_nearest_face(vid_frame)
        if bbox is not None:
            tracker = create_tracker()
            tracker.init(vid_frame, tuple(bbox))
            locked = True
            lost_since = None
            x, y, w, h = map(int, bbox)
            cv2.rectangle(vid_frame, (x, y), (x + w, y + h), (0, 255, 255), 2)

            current = time.time()  # Print coords every 0.5 s
            if current - last_print >= 0.5:
                print(f"Subject locked: x={x}, y={y}, w={w}, h={h}")
                last_print = current
    else:  # Tracking phase
        success, newbox = tracker.update(vid_frame)
        if success:
            x, y, w, h = map(int, newbox)
            in_frame = 0 <= x < W and 0 <= y < H and x + w <= W and y + h <= H
            if in_frame:
                cv2.rectangle(vid_frame, (x, y), (x + w, y + h), (0, 220, 0), 3)
                lost_since = None

                current = time.time()  # Print coords every 0.5 s
                if current - last_print >= 0.5:
                    print(f"Tracking locked subject: x={x}, y={y}, w={w}, h={h}")
                    last_print = current
            else:
                success = False

        if not success:  # Lost tracking
            if lost_since is None:
                lost_since = time.time()

            if time.time() - lost_since >= REDETECT_DELAY:
                tracker = None
                locked = False
                print("---------------- Re-Acquiring Lock ----------------")

    cv2.imshow(WIN, vid_frame)  # Display processed frame in a window

    # Exit conditions
    if (cv2.waitKey(1) & 0xFF == ord("q")) or (
        cv2.getWindowProperty(WIN, cv2.WND_PROP_VISIBLE) < 1
    ):
        break

video_capture.release()
cv2.destroyAllWindows()
