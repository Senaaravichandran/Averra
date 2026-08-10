import face_recognition
import cv2

# Load image
image = face_recognition.load_image_file("photos\Haricoatpic.jpg")
face_locations = face_recognition.face_locations(image)

# Convert image to BGR (for OpenCV display)
image_bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

# Draw rectangles around faces
for (top, right, bottom, left) in face_locations:
    cv2.rectangle(image_bgr, (left, top), (right, bottom), (0, 255, 0), 2)

# Show image
cv2.imshow("Detected Face(s)", image_bgr)
cv2.waitKey(0)
cv2.destroyAllWindows()
