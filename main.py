from fastapi import FastAPI, File, UploadFile
import cv2
import numpy as np
import shutil
import os
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image

# Initialize FastAPI app
app = FastAPI()

# Enable CORS to allow frontend apps to make requests to this server
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
    return {"message": "Upload an image to process shapes into commands"}

@app.post("/upload/")
async def upload_image(file: UploadFile = File(...)):
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    return {"filename": file.filename, "message": "File uploaded successfully"}

def get_image_dimensions(image_path, unit='pixels', dpi=None, square_tolerance=0.1):
    try:
        with Image.open(image_path) as img:
            # Get pixel dimensions
            width_px, height_px = img.size
            print(f"Resolution: {width_px} × {height_px} pixels")
            
            # Retrieve actual DPI if not provided
            if dpi is None:
                dpi = round(img.info.get("dpi", (72, 72))[0])  # Use horizontal DPI
            
            print(f"Using DPI: {dpi}")
            
            # Convert to desired unit
            if unit == 'pixels':
                return width_px, height_px
            elif unit == 'cm':
                # Convert pixels to centimeters (1 inch = 2.54 cm)
                width_cm = (width_px / dpi) * 2.54
                height_cm = (height_px / dpi) * 2.54
                
                # Print more detailed information about the dimensions
                print(f"Calculated width: {width_cm:.2f} cm")
                print(f"Calculated height: {height_cm:.2f} cm")
                
                # Calculate width/height ratio
                width_height_ratio = width_cm / height_cm
                print(f"Width/Height Ratio: {width_height_ratio:.2f}")
                
                # Check if the shape is close to a square
                # Use absolute ratio for both comparisons
                is_square = abs(width_height_ratio - 1) <= square_tolerance
                shape_type = "SQUARE" if is_square else "RECTANGLE"
                print(f"Considered as a {shape_type}")
                
                return round(width_cm, 2), round(height_cm, 2), shape_type
            elif unit == 'm':
                # Convert pixels to meters
                width_m = (width_px / dpi) * 0.0254
                height_m = (height_px / dpi) * 0.0254
                return round(width_m, 4), round(height_m, 4)
            else:
                raise ValueError("Invalid unit. Choose 'pixels', 'cm', or 'm'.")
    
    except FileNotFoundError:
        print(f"Error: File '{image_path}' not found.")
        return None
    except IOError:
        print(f"Error: Cannot open image file '{image_path}'.")
        return None
    except ValueError as e:
        print(str(e))
        return None
    
def process_image(image_path):
    # Get image dimensions in centimeters
    dimensions = get_image_dimensions(image_path, unit='cm')
    
    if not dimensions:
        return {"error": "Could not retrieve image dimensions"}
    
    # Unpack dimensions and shape type
    width_cm, height_cm, shape_type = dimensions
    commands = []
    
    # Determine shape type and generate commands
    if shape_type == "SQUARE":
        shape_type = "Square"
        side_length = (width_cm + height_cm) / 2  # Average of width and height
        # Convert cm to m (1 cm = 1 m in this example)
        side_length_m = side_length
        
        commands.append(f"{shape_type} detected:")
        commands.append(f"Forward: {side_length_m:.2f}m")
        commands.append("Right: 90°")
        commands.append(f"Forward: {side_length_m:.2f}m")
        commands.append("Right: 90°")
        commands.append(f"Forward: {side_length_m:.2f}m")
        commands.append("Right: 90°")
        commands.append(f"Forward: {side_length_m:.2f}m")
        commands.append("Right: 90°")
    
    else:
        shape_type = "Rectangle"
        long_side = max(width_cm, height_cm)
        short_side = min(width_cm, height_cm)
        
        # Convert cm to m (1 cm = 1 m in this example)
        long_side_m = long_side
        short_side_m = short_side
        
        commands.append(f"{shape_type} detected:")
        commands.append(f"Forward: {long_side_m:.2f}m")
        commands.append("Right: 90°")
        commands.append(f"Forward: {short_side_m:.2f}m")
        commands.append("Right: 90°")
        commands.append(f"Forward: {long_side_m:.2f}m")
        commands.append("Right: 90°")
        commands.append(f"Forward: {short_side_m:.2f}m")
        commands.append("Right: 90°")
    
    return {"commands": commands}

@app.post("/process/")
async def process_uploaded_image(file: UploadFile = File(...)):
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    result = process_image(file_path)
    
    if 'error' in result:
        return result
    
    return result