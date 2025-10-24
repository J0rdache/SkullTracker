import cv2
import time

class FaceTracker:
    def __init__(self, CameraWidth, CameraHeight, 
                 CameraFps, CameraIndex, Classifier, ScaleFactor, 
                 MinNeighbors, MinSize, MotionTolerance, 
                 TrackingGrace, RollingAvgCount, CenterWidth):
    
        self.face_cascade = cv2.CascadeClassifier(Classifier)

        self.cap = cv2.VideoCapture(CameraIndex)

        if not self.cap.isOpened():
            raise IOError("Cannot open webcam")
        
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, CameraWidth)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CameraHeight)
        self.cap.set(cv2.CAP_PROP_FPS, CameraFps)

        self.camInfo = {
            "width": int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            "height": int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            "fps": int(self.cap.get(cv2.CAP_PROP_FPS))
        }
        print(self.camInfo['fps'])
        self.faces = []
        self.targetFace = None
        self.lastGraceTime = time.time()
        self.lastAcquireTime = time.time()
        self.locked = False
        self.tracker = None
        self.targetXList = []
        self.xListPos = 0
        self.targetAvgX = None
        self.ScaleFactor = ScaleFactor
        self.MinNeighbors = MinNeighbors
        self.MinSize = MinSize
        self.MotionTolerance = MotionTolerance
        self.TrackingGrace = TrackingGrace
        self.RollingAvgCount = RollingAvgCount
        self.CenterWidth = CenterWidth

    def __del__(self):
        self.cap.release()
        cv2.destroyAllWindows()

    def findTarget(self):
        largestFace = None
        maxArea = 0
        for (x, y, w, h) in self.faces:
            if w * h > maxArea:
                maxArea = w * h
                largestFace = (x, y, w, h)
        return largestFace
    
    def create_tracker(self):
        if hasattr(cv2, "TrackerCSRT_create"):
            print("Using CSRT tracker")
            return cv2.TrackerCSRT_create()
        raise RuntimeError("Tracker not found in opencv installation.")

    def trackTargetFace(self):
        (lx, ly, lw, lh) = self.targetFace
        ht = self.MotionTolerance * lw
        vt = self.MotionTolerance * lh
        for (x, y, w, h) in self.faces:
            if (x + w // 2 > lx + lw // 2 - ht and x + w // 2 < lx + lw // 2 + ht and y + h // 2 > ly + lh // 2 - vt and y + h // 2 < ly + lh // 2 + vt):
                return (x, y, w, h)
        return None
    
    def drawOnFrame(self, frame):
        # Draws rectangles around faces, displays camera info, and displays the horizontal coordinates of the target face
        font = cv2.FONT_HERSHEY_SIMPLEX
        fontScale = 0.85
        thickness = 2

        for (x, y, w, h) in self.faces:
            if self.targetFace is not None and (x, y, w, h) == self.targetFace:
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), thickness)
                cv2.putText(frame, "Target", (x, y - 10), font, fontScale, (0, 255, 0), thickness)
                targetXText = f"Target X: {self.targetAvgX}"
                cv2.putText(frame, targetXText, (10, self.camInfo['height'] - 40), font, fontScale, (255, 0, 0), thickness)
            else:
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), thickness)
        
        camText = f"{self.camInfo['width']}x{self.camInfo['height']} @ {self.camInfo['fps']} FPS"
        cv2.putText(frame, camText, (10, 30), font, fontScale, (0, 0, 255), thickness)

        return frame
    
    def update(self):
        ret, frame = self.cap.read()

        if not ret:
            return 0
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        self.faces = self.face_cascade.detectMultiScale(gray, scaleFactor=self.ScaleFactor, minNeighbors=self.MinNeighbors, minSize=self.MinSize)

        if not self.locked or time.time() - self.lastAcquireTime > 10:
            
            self.locked = False
            self.targetFace = self.findTarget()
            if self.targetFace is not None:
                
                self.lastAcquireTime = time.time()
                self.tracker = self.create_tracker()
                self.tracker.init(frame, tuple(self.targetFace))
                self.locked = True
                self.lastGraceTime = None
        else:
            success, self.targetFace = self.tracker.update(frame)
            (x, y, w, h) = self.targetFace
            in_frame = x >= 0 & x + w < self.camInfo['width'] & y > 0 & y + h < self.camInfo['height']
            if success & in_frame:
                self.lastGraceTime = None
    
        if self.targetFace is not None:
            centerX = self.targetFace[0] + self.targetFace[2] // 2
            if len(self.targetXList) < self.RollingAvgCount:
                self.targetXList.append(centerX)
                self.xListPos += 1
            elif self.xListPos < self.RollingAvgCount:
                self.targetXList[self.xListPos] = centerX
                self.xListPos += 1
            else:
                self.xListPos = 0
                self.targetXList[self.xListPos] = centerX
                self.xListPos += 1
        
        if len(self.targetXList) != 0:
            self.targetAvgX = sum(self.targetXList) // len(self.targetXList)
        else:
            self.targetAvgX = 0
        
        frame = self.drawOnFrame(frame)
        #cv2.imshow('USRT Face Tracking', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            return 400
        if not len(self.faces) and not self.locked:
            currentTime = time.time()
            if self.lastGraceTime is None:
                self.lastGraceTime = currentTime
            if currentTime - self.lastAcquireTime >= self.TrackingGrace
                return 401
        else:
            self.lastGraceTime = None
        if self.locked:
            if self.targetAvgX > self.camInfo['width'] // 2 - self.CenterWidth // 2 and self.targetAvgX < self.camInfo['width'] // 2 + self.CenterWidth // 2:
                return 0
            elif self.targetAvgX < self.camInfo['width'] // 2:
                return (self.camInfo['width'] // 2 - self.targetAvgX) / (self.camInfo['width'] // 2) * 10
            elif self.targetAvgX > self.camInfo['width'] // 2:
                return -(self.targetAvgX - self.camInfo['width'] // 2) / self.camInfo['width'] * 10
        else:
            return 0
        return 400


        