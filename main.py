from fastapi import FastAPI, File, UploadFile, HTTPException
import cv2
import numpy as np
import shutil
import os
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
import math

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

def get_sqr_rect_dimensions(image_path, unit='pixels', dpi=None, square_tolerance=0.1):
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

def euclidean_distance(p1, p2):
    """Calcule la distance euclidienne entre deux points."""
    return math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)


def get_triangle_sides_from_image(image_path):
    """
    Détecte un triangle dans l'image et calcule les longueurs de ses côtés en pixels et en cm.
    
    :param image_path: Chemin de l'image.
    :return: Affiche les longueurs des côtés en pixels et en cm.
    """
    try:
        # Charger l'image avec OpenCV
        image = cv2.imread(image_path)
        if image is None:
            print("❌ Erreur: Impossible de charger l'image.")
            return None

        # Convertir en niveaux de gris
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Appliquer un flou pour réduire le bruit
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)

        # Détecter les contours
        edges = cv2.Canny(blurred, 50, 150)

        # Trouver les contours
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Vérifier si un triangle est détecté
        for contour in contours:
            approx = cv2.approxPolyDP(contour, 0.02 * cv2.arcLength(contour, True), True)
            if len(approx) == 3:  # Un triangle a exactement 3 sommets
                vertices = [(point[0][0], point[0][1]) for point in approx]

                # Calculer les longueurs en pixels
                AB = euclidean_distance(vertices[0], vertices[1])
                BC = euclidean_distance(vertices[1], vertices[2])
                CA = euclidean_distance(vertices[2], vertices[0])

                # Charger l'image avec PIL pour récupérer le DPI
                with Image.open(image_path) as img:
                    dpi = img.info.get("dpi", (72, 72))[0]  # Utiliser la résolution horizontale
                    dpi = round(dpi)  # Arrondir le DPI

                # Conversion en cm
                AB_cm = (AB / dpi) * 2.54
                BC_cm = (BC / dpi) * 2.54
                CA_cm = (CA / dpi) * 2.54

                # Affichage des résultats
                print("📐 Longueurs des côtés du triangle détecté :")
                print(f"🔹 AB = {round(AB, 2)} pixels ({round(AB_cm, 2)} cm)")
                print(f"🔹 BC = {round(BC, 2)} pixels ({round(BC_cm, 2)} cm)")
                print(f"🔹 CA = {round(CA, 2)} pixels ({round(CA_cm, 2)} cm)")
                print(f"🖼️  Résolution de l'image: {dpi} DPI")

                return {
                    "pixels": (round(AB, 2), round(BC, 2), round(CA, 2)),
                    "cm": (round(AB_cm, 2), round(BC_cm, 2), round(CA_cm, 2)),
                    "dpi": dpi
                }

        print("⚠️ Aucun triangle détecté dans l'image.")
        return None

    except Exception as e:
        print(f"❌ Erreur: {e}")
        return None

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
 
def process_image(image_path):
    # Get image dimensions in centimeters
    dimensions = get_sqr_rect_dimensions(image_path, unit='cm')
    
    if not dimensions:
        return {"error": "Could not retrieve image dimensions"}
    
    # Unpack dimensions and shape type
    width_cm, height_cm, shape_type = dimensions
    commands = []
    start_position = (0, 0)  # Point de départ (peut être personnalisé)
    start_direction = 0  # Direction initiale en degrés (0° pour "haut")
        
            # Attempt to detect triangle first
    try:
        # Détecter les côtés du triangle
        triangle_sides = get_triangle_sides_from_image(image_path)
        
        # Détecter les angles du triangle
        triangle_details = detect_triangle_angles(image_path)
        
        if triangle_sides and triangle_details:
            shape_type = "Triangle"
            
            # Ensure 'angles' and 'vertices' are present in triangle_details
            angles = triangle_details.get("angles", [])
            vertices = triangle_details.get("vertices", [])
            side_lengths_cm = triangle_sides.get("cm", [])
            
            commands.append(f"{shape_type} detected:")

            # Vérifier si nous avons les données nécessaires
            if len(side_lengths_cm) == 3:
                commands.append(f"Sides: AB = {side_lengths_cm[0]} cm, BC = {side_lengths_cm[1]} cm, CA = {side_lengths_cm[2]} cm")
            else:
                commands.append("Error: Sides data is incomplete.")

            # Ajouter les angles
            if angles:
                for i, angle_info in enumerate(angles):
                    angle_deg = angle_info.get("angle_degrees", 0)
                    commands.append(f"Angle at vertex {i+1}: {round(angle_deg, 2)}°")
            else:
                commands.append("Error: Angle data is incomplete.")
            
            # Générer les commandes de déplacement
            for i in range(3):
                if i < len(side_lengths_cm) and i < len(angles):
                    commands.append(f"Forward: {round(side_lengths_cm[i], 2)} cm")
                    commands.append(f"Right: {round(angles[i].get('angle_degrees', 0), 2)}°")
            
            # Ajouter la position de départ et la direction
            commands.append(f"Start position: {start_position}")
            commands.append(f"Start direction: {start_direction}°")
            
            # Charger l'image d'origine
            image = cv2.imread(image_path)
            
            # Dessiner les côtés du triangle si les vertices existent
            if vertices:
                for i in range(3):
                    cv2.line(image, tuple(vertices[i]), tuple(vertices[(i+1)%3]), (0, 255, 0), 2)  # Vert color for sides
                
                # Annoter les angles
                for i, angle_info in enumerate(angles):
                    vertex = vertices[i]
                    angle_deg = angle_info.get("angle_degrees", 0)
                    cv2.putText(image, f"{round(angle_deg, 1)}°", tuple(vertex), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
            
                # Annoter les longueurs des côtés
                for i in range(3):
                    mid_point = ((vertices[i][0] + vertices[(i+1)%3][0]) // 2, (vertices[i][1] + vertices[(i+1)%3][1]) // 2)
                    cv2.putText(image, f"{round(side_lengths_cm[i], 1)} cm", mid_point, cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
            
                # Dessiner le point de départ et la direction
                cv2.putText(image, f"Start position: {start_position}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
                cv2.putText(image, f"Direction: {start_direction}°", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
            
                # Enregistrer l'image annotée
                annotated_image_path = "path_to_save_annotated_image.jpg"  # Change this to your desired path
                cv2.imwrite(annotated_image_path, image)
            
                commands.append(f"Annotated triangle image saved at: {annotated_image_path}")
            
                return {"commands": commands}
            else:
                commands.append("Error: Triangle vertices not detected.")
                return {"commands": commands}

        else:
            commands.append("Error: Unable to detect triangle sides or angles.")
            return {"commands": commands}

    except HTTPException:
        pass  # Si aucun triangle détecté, ne rien retourner   
    if shape_type == "SQUARE":
        side_length = (width_cm + height_cm) / 2  # Moyenne de la largeur et de la hauteur
        side_length_m = side_length  # Convertir en mètres
        commands.append(f"Square detected:")
        
        # Déplacer selon la direction actuelle
        commands.append(f"Start at position {start_position}, facing {start_direction}°.")
        commands.append(f"Forward: {side_length_m:.2f}m")
        commands.append(f"Turn right: 90° (new direction: {start_direction + 90}°)")
        commands.append(f"Forward: {side_length_m:.2f}m")
        commands.append(f"Turn right: 90° (new direction: {start_direction + 180}°)")
        commands.append(f"Forward: {side_length_m:.2f}m")
        commands.append(f"Turn right: 90° (new direction: {start_direction + 270}°)")
        commands.append(f"Forward: {side_length_m:.2f}m")
        commands.append(f"Turn right: 90° (new direction: {start_direction + 360}°)")
    
    elif shape_type == "RECTANGLE":
        long_side = max(width_cm, height_cm)
        short_side = min(width_cm, height_cm)
        long_side_m = long_side  # Convertir en mètres
        short_side_m = short_side
        
        commands.append(f"Rectangle detected:")
        
        # Déplacer selon la direction actuelle
        commands.append(f"Start at position {start_position}, facing {start_direction}°.")
        commands.append(f"Forward: {long_side_m:.2f}m")
        commands.append(f"Turn right: 90° (new direction: {start_direction + 90}°)")
        commands.append(f"Forward: {short_side_m:.2f}m")
        commands.append(f"Turn right: 90° (new direction: {start_direction + 180}°)")
        commands.append(f"Forward: {long_side_m:.2f}m")
        commands.append(f"Turn right: 90° (new direction: {start_direction + 270}°)")
        commands.append(f"Forward: {short_side_m:.2f}m")
        commands.append(f"Turn right: 90° (new direction: {start_direction + 360}°)")

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