"""import cv2
#print(cv2.__version__)

#READING AN IMAGE

image=cv2.imread('Haricoatpic.jpeg')
cv2.imshow('HariBabu',image)
cv2.waitKey()  #THE IMAGE IS WAITING FOR THE USER CLICKS ANY KEY INORDER TO CLOSE IT"""

"""import face_recognition
import cv2

# Load image
image = face_recognition.load_image_file('photos/Haricoatpic.jpeg')
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

import cv2

cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        print("Failed to grab frame")
        break

    cv2.imshow("Webcam Test", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()"""


"""import cv2
import face_recognition
import csv
import numpy as np
from datetime import datetime

# Start video capture
video_capture = cv2.VideoCapture(0)

if not video_capture.isOpened():
    print("Error: Could not open webcam")
    exit()

# Load sample images and learn how to recognize them
jobs_image = face_recognition.load_image_file("photos/jobs.jpg")
jobs_encoding = face_recognition.face_encodings(jobs_image)[0]

ratan_tata_image = face_recognition.load_image_file("photos/tata.jpg")
ratan_tata_encoding = face_recognition.face_encodings(ratan_tata_image)[0]

sadmona_image = face_recognition.load_image_file("photos/sadmona.jpg")
sadmona_encoding = face_recognition.face_encodings(sadmona_image)[0]

tesla_image = face_recognition.load_image_file("photos/tesla.jpg")
tesla_encoding = face_recognition.face_encodings(tesla_image)[0]

# Store encodings and names
known_face_encodings = [
    jobs_encoding,
    ratan_tata_encoding,
    sadmona_encoding,
    tesla_encoding
]

known_face_names = [
    "Jobs",
    "Ratan Tata",
    "Sadmona",
    "Tesla"
]

students = known_face_names.copy()

# Create CSV file for today's attendance
current_date = datetime.now().strftime("%Y-%m-%d")
f = open(current_date + '.csv', 'w+', newline='')
inwriter = csv.writer(f)

while True:
    ret, frame = video_capture.read()
    if not ret:
        print("Failed to grab frame. Exiting...")
        break

    # Resize frame for faster processing
    small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
    rgb_small_frame = small_frame[:, :, ::-1]

    # Detect faces
    face_locations = face_recognition.face_locations(rgb_small_frame)
    face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

    face_names = []

    for face_encoding in face_encodings:
        matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
        name = ""

        face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
        best_match_index = np.argmin(face_distances)

        if matches[best_match_index]:
            name = known_face_names[best_match_index]

        face_names.append(name)

        if name in students:
            students.remove(name)
            print("Remaining students:", students)

            current_time = datetime.now().strftime("%H:%M:%S")
            inwriter.writerow([name, current_time])

    # Show video feed
    cv2.imshow("Attendance System", frame)

    # Press 'q' to exit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Cleanup
video_capture.release()
cv2.destroyAllWindows()
f.close() """


chatgpt I just want you to create a smart attendance system in python 
using opencv, face_recognition when the code is executed the webcam should open and stay until 
the user clicks the 'q' key to close it, then the photo of a students is given to a folder , 
when a person comes infront of the camera then the webcam should detect the 
person's face using rectangle on the face , if the person infront of the camera's 
photo is already there in the folder then it should mark attendance called "Person X present" or 
else it should mark the rectangle and say "person Unknown" all the marked attendance names and their current 
time of recording their attendance should be entered in an excel, jsut give me the entire code of this project

