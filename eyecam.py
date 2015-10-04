import cv2, sys, pyautogui


# Setup
cv2.setUseOptimized(True)

facePath = sys.argv[1]
eyePath = sys.argv[2]

faceCascade = cv2.CascadeClassifier(facePath)
eyeCascade = cv2.CascadeClassifier(eyePath)

videoCapture = cv2.VideoCapture(0)
videoCapture.set(cv2.CAP_PROP_FPS, 1)

oldFace = (0, 0, 0, 0)
oldLeftEye = (0, 0, 0, 0)
oldRightEye = (0, 0, 0, 0)


# Learning rest position (do this for turns 0-(learnPhase - 1))
turns = 0
learnPhase = 128

restFace = (0, 0, -1, -1)
restLeftEye = (0, 0, -1, -1)
restRightEye = (0, 0, -1, -1)


# Moving
eyeHitBox = 8                        # If the box reaches this far, move it
move = (0, 0, 0, 0)                  # Up, Down, Left, Right
scrW, scrH = pyautogui.size()        # Screen size
speed = 16                           # How far to step each read
pyautogui.moveTo(scrW / 2, scrH / 2) # Mouse starts in middle

# Clicking
lClick = 0
notlClick = 0.0
lThreshold = 32
rClick = 0
notrClick = 0.0
rThreshold = 32


# HitBox calculation... remember that left and right are mirrored!
def hit(old, new):
    return (
        1 if old[1] - new[1] >= eyeHitBox else 0,      # Up
        1 if old[1] - new[1] <= -1 * eyeHitBox else 0, # Down
        1 if old[0] - new[0] <= -1 * eyeHitBox else 0, # Left
        1 if old[0] - new[0] >= eyeHitBox else 0       # Right
    )


# Movement calculation
def moveMouse():
    global move
    
    mouseX, mouseY = pyautogui.position()
    
    if move[0]:
        pyautogui.moveTo(mouseX, mouseY + speed)
    if move[1]:
        pyautogui.moveTo(mouseX, mouseY - speed)
    if move[2]:
        pyautogui.moveTo(mouseX - speed, mouseY)
    if move[3]:
        pyautogui.moveTo(mouseX + speed, mouseY)


# Fire a click... side == False is left
def clickMouse(side):
    if side:
        pyautogui.click(button='right')
    else:
        pyautogui.click(button='left')


# Averages eye positions to learn resting eye position... side == False is left
def learnEye(roi_gray, roi_color, side):
    global restLeftEye
    global restRightEye
    
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
            restRightEye = ((restRightEye[0]+ex)/2, (restRightEye[1]+ey)/2, (restRightEye[2]+ew)/2, (restRightEye[3]+eh)/2)
        else:
            restLeftEye = ((restLeftEye[0]+ex)/2, (restLeftEye[1]+ey)/2, (restLeftEye[2]+ew)/2, (restLeftEye[3]+eh)/2)
        
        cv2.rectangle(roi_color, (ex, ey), (ex+ew, ey+eh), (255, 0, 0), 2)
    
    return True


# Gets an eye from the image and draws it... side == False is left
def getEye(roi_gray, roi_color, side):
    global oldLeftEye, restLeftEye
    global oldRightEye, restRightEye
    global restFace
    global move, lClick, rClick
    
    eyes = eyeCascade.detectMultiScale(
        roi_gray,
        scaleFactor=2.1,
        minSize=(30, 30),
        maxSize=((oldFace[0]+oldFace[2]) >> 3, (oldFace[1]+oldFace[3]) >> 3),
        flags=cv2.CASCADE_SCALE_IMAGE
    )
    
    # Resting eye position
    if side:
        cv2.rectangle(frame[restFace[1]:restFace[1]+(restFace[3]>>1), restFace[0]+(restFace[2]>>1):restFace[0]+restFace[2]], (restRightEye[0], restRightEye[1]), (restRightEye[0]+restRightEye[2], restRightEye[1]+restRightEye[3]), (0, 0, 255), 2)
    else:
        cv2.rectangle(frame[restFace[1]:restFace[1]+(restFace[3]>>1), restFace[0]:restFace[0]+(restFace[2]>>1)], (restLeftEye[0], restLeftEye[1]), (restLeftEye[0]+restLeftEye[2], restLeftEye[1]+restLeftEye[3]), (0, 0, 255), 2)
    
    if len(eyes) != 1:
        if side and rClick < 8:
            cv2.rectangle(roi_color, (oldRightEye[0], oldRightEye[1]), (oldRightEye[0]+oldRightEye[2], oldRightEye[1]+oldRightEye[3]), (255, 0, 0), 2)
        elif not side and lClick < 8:
            cv2.rectangle(roi_color, (oldLeftEye[0], oldLeftEye[1]), (oldLeftEye[0]+oldLeftEye[2], oldLeftEye[1]+oldLeftEye[3]), (255, 0, 0), 2)
        
        return False
    
    for (ex, ey, ew, eh) in eyes:
        if side:
            oldRightEye = (ex, ey, ew, eh) if oldRightEye[2] == -1 or move[0] or move[1] or move[2] or move[3] else oldRightEye
            cv2.rectangle(roi_color, (oldRightEye[0], oldRightEye[1]), (oldRightEye[0]+oldRightEye[2], oldRightEye[1]+oldRightEye[3]), (255, 0, 0), 2)
        else:
            move = hit(restLeftEye, (ex, ey, ew, eh))
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
        minSize=(100, 100),
        flags=cv2.CASCADE_SCALE_IMAGE
    )
    
    if turns < learnPhase: # Learning mode
        if len(faces) == 1:
            # Green box around faces
            for (x, y, w, h) in faces:
                restFace = ((restFace[0]+x)/2, (restFace[1]+y)/2, (restFace[2]+w)/2, (restFace[3]+h)/2)
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                
                # Only count turns if both eyes are visible
                
                # Left eye
                if learnEye(gray[y:y+(h>>1), x+(w>>1):x+w], frame[y:y+(h>>1), x+(w>>1):x+w], False):
                    turns += 1
                
                # Right eye
                if not learnEye(gray[y:y+(h>>1), x:x+(w>>1)], frame[y:y+(h>>1), x:x+(w>>1)], True):
                    turns -= 1
        
        if turns == learnPhase:
            print restFace
            print restLeftEye
            print restRightEye
    
    else: # Input mode
        if len(faces) != 1:
            oldFace = (0, 0, -1, -1)
        else:
            # Green box around faces
            for (x, y, w, h) in faces:
                oldFace = (x, y, w, h) if oldFace[2] == -1 or (abs(oldFace[0] - x) > 4 and abs(oldFace[1] - y) > 4) else oldFace
                cv2.rectangle(frame, (oldFace[0], oldFace[1]), (oldFace[0]+oldFace[2], oldFace[1]+oldFace[3]), (0, 255, 0), 2)
                
                # Resting face
                cv2.rectangle(frame, (restFace[0], restFace[1]), (restFace[0]+restFace[2], restFace[1]+restFace[3]), (255, 255, 255), 2)
                
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
                    moveMouse()
                    print move
                
                # Resolve clicks
                if notlClick > 0 and lClick > lThreshold and lClick / notlClick > .5:
                    print "single left click"
                    clickMouse(False)
                    lClick = 0
                    notlClick = 0
                    lThreshold = 16
                else:
                    notlClick = 0
                    lThreshold = 16
                if notrClick > 0 and rClick > rThreshold and rClick / notrClick > .5:
                    print "single right click"
                    clickMouse(True)
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