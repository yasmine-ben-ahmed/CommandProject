from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import numpy as np
import cv2
import shutil
import os
from PIL import Image
import math

# Initialize FastAPI app
app = FastAPI(title="Triangle Angle Detector")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.get("/")
def home():
    return {"message": "Upload a triangle image to detect angles"}

def detect_triangle_angles(image_path):
    # Read the image
    img = cv2.imread(image_path)
    if img is None:
        raise HTTPException(status_code=400, detail="Could not read image")
    
    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Apply Gaussian blur
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # Apply adaptive threshold
    thresh = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                  cv2.THRESH_BINARY_INV, 11, 2)
    
    # Find contours
    contours, _ = cv2.findContours(thresh, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    
    # Sort contours by area and get the largest one
    contours = sorted(contours, key=cv2.contourArea, reverse=True)
    
    # Find triangular contour
    triangle_contour = None
    for contour in contours:
        # Approximate the contour
        epsilon = 0.04 * cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, epsilon, True)
        
        # If it has 3 vertices, it's a triangle
        if len(approx) == 3:
            triangle_contour = approx
            break
    
    if triangle_contour is None:
        raise HTTPException(status_code=400, detail="No triangle detected in the image")
    
    # Get the corners
    corners = [point[0] for point in triangle_contour]
    
    # Calculate the angles
    angles = []
    for i in range(3):
        p1 = corners[i]
        p2 = corners[(i+1) % 3]
        p3 = corners[(i+2) % 3]
        
        # Calculate vectors
        v1 = np.array([p1[0] - p2[0], p1[1] - p2[1]])
        v2 = np.array([p3[0] - p2[0], p3[1] - p2[1]])
        
        # Calculate angle using dot product formula
        dot = np.dot(v1, v2)
        mag1 = np.linalg.norm(v1)
        mag2 = np.linalg.norm(v2)
        
        # Avoid division by zero
        if mag1 * mag2 == 0:
            cos_angle = 0
        else:
            cos_angle = dot / (mag1 * mag2)
        
        # Ensure cos_angle is within valid range
        cos_angle = max(min(cos_angle, 1.0), -1.0)
        
        # Get angle in degrees
        angle = math.degrees(math.acos(cos_angle))
        
        angles.append({
            "vertex": i,
            "coordinates": (int(p2[0]), int(p2[1])),
            "angle_degrees": round(angle, 2)
        })
    
    # Annotate the image for visualization
    output_img = img.copy()
    for i, corner in enumerate(corners):
        # Draw vertices
        cv2.circle(output_img, tuple(corner), 10, (0, 0, 255), -1)
        # Label angles
        cv2.putText(output_img, f"{angles[i]['angle_degrees']}°", 
                   (corner[0]-20, corner[1]-20), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    
    # Save the annotated image
    output_path = image_path.replace(".", "_annotated.")
    cv2.imwrite(output_path, output_img)
    
    return {
        "shape": "Triangle",
        "angles": angles,
        "sum_of_angles": round(sum(angle["angle_degrees"] for angle in angles), 2),
        "annotated_image": output_path
    }

@app.post("/detect-triangle-angles/")
async def detect_angles(file: UploadFile = File(...)):
    """
    Upload an image of a triangle to detect its angles.
    """
    # Check if file is an image
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Save the file
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    try:
        # Process the image to detect triangle angles
        result = detect_triangle_angles(file_path)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))