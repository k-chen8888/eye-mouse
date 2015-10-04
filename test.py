import cv2, sys


# Setup
cv2.setUseOptimized(True)

facePath = sys.argv[1]
eyePath = sys.argv[2]

faceCascade = cv2.CascadeClassifier(facePath)
eyeCascade = cv2.CascadeClassifier(eyePath)

videoCapture = cv2.VideoCapture(0)
videoCapture.set(cv2.CAP_PROP_FPS, 1)

oldFace = (0, 0, -1, -1)
oldLeftEye = (0, 0, -1, -1)
oldRightEye = (0, 0, -1, -1)

eyeHitBox = 16 # If the box reaches this far, move it
move = (0, 0, 0, 0) # Up, Down, Left, Right

lClick = 0
notlClick = 0.0
lThreshold = 32
rClick = 0
notrClick = 0.0
rThreshold = 32


# HitBox calculation... remember that left and right are mirrored!
def hit(old, new):
    return (1 if old[1] - new[1] >= eyeHitBox else 0, 1 if old[1] - new[1] <= -1 * eyeHitBox else 0, 1 if old[0] - new[0] <= -1 * eyeHitBox else 0, 1 if old[0] - new[0] >= eyeHitBox else 0)


# Gets an eye from the image and draws it; side == False is left
def getEye(roi_gray, roi_color, side):
    global oldLeftEye
    global oldRightEye
    global move
    
    eyes = eyeCascade.detectMultiScale(
        roi_gray,
        scaleFactor=2.1,
        minSize=(30, 30),
        maxSize=((oldFace[0]+oldFace[2]) >> 3, (oldFace[1]+oldFace[3]) >> 3),
        flags=cv2.CASCADE_SCALE_IMAGE
    )
    
    if len(eyes) != 1:
        return False
    
    for (ex, ey, ew, eh) in eyes:
        if side:
            move = hit((ex, ey, ew, eh), oldRightEye)
            oldRightEye = (ex, ey, ew, eh) if oldRightEye[2] == -1 or move[0] or move[1] or move[2] or move[3] else oldRightEye
            cv2.rectangle(roi_color, (oldRightEye[0], oldRightEye[1]), (oldRightEye[0]+oldRightEye[2], oldRightEye[1]+oldRightEye[3]), (255, 0, 0), 2)
        else:
            move = hit((ex, ey, ew, eh), oldLeftEye)
            oldLeftEye = (ex, ey, ew, eh) if oldLeftEye[2] == -1 or move[0] or move[1] or move[2] or move[3] else oldLeftEye
            cv2.rectangle(roi_color, (oldLeftEye[0], oldLeftEye[1]), (oldLeftEye[0]+oldLeftEye[2], oldLeftEye[1]+oldLeftEye[3]), (255, 0, 0), 2)
    
    return True


# Capture each frame of the video and process for cascades
while True:
    ret, frame = videoCapture.read()
    
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    faces = faceCascade.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=6,
        minSize=(30, 30),
        flags=cv2.CASCADE_SCALE_IMAGE
    )
    
    if len(faces) == 0:
        oldFace = (0, 0, -1, -1)
    else:
        # Green box around faces
        for (x, y, w, h) in faces:
            oldFace = (x, y, w, h) if oldFace[2] == -1 or (abs(oldFace[0] - x) > 4 and abs(oldFace[1] - y) > 4) else oldFace
            cv2.rectangle(frame, (oldFace[0], oldFace[1]), (oldFace[0]+oldFace[2], oldFace[1]+oldFace[3]), (0, 255, 0), 2)
            
            # Left eye
            if not getEye(gray[y:oldFace[1]+(oldFace[3]>>1), oldFace[0]+(oldFace[2]>>1):oldFace[0]+oldFace[2]], frame[y:oldFace[1]+(oldFace[3]>>1), oldFace[0]+(oldFace[2]>>1):oldFace[0]+oldFace[2]], False):
                move = (0, 0, 0, 0)
                lClick += 1
                notlClick += 1.0
                rThreshold = 256
            elif notlClick > 0.0:
                notlClick += 1.0
            
            # Right eye
            if not getEye(gray[y:oldFace[1]+(oldFace[3]>>1), x:oldFace[0]+(oldFace[2]>>1)], frame[y:oldFace[1]+(oldFace[3]>>1), x:oldFace[0]+(oldFace[2]>>1)], True):
                move = (0, 0, 0, 0)
                rClick += 1
                notrClick += 1.0
                lThreshold = 256
            elif notrClick > 0.0:
                notrClick += 1.0
            
            # Resolve movement    
            if move[0] or move[1] or move[2] or move[3]:
                print move
            
            # Resolve clicks
            if notlClick > 0 and lClick > lThreshold and lClick / notlClick > .5:
                print "single left click"
                lClick = 0
                notlClick = 0
                lThreshold = 16
            else:
                notlClick = 0
                lThreshold = 16
            if notrClick > 0 and rClick > rThreshold and rClick / notrClick > .5:
                print "single right click"
                rClick = 0
                notrClick = 0
                rThreshold = 16
            else:
                notrClick = 0
                rThreshold = 16
    
    cv2.imshow('Video', frame)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break


# Clean up
videoCapture.release()
cv2.destroyAllWindows()