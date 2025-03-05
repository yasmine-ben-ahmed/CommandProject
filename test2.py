from PIL import Image

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
                
                # Check if the shape is close to a square
                width_height_ratio = abs(width_cm / height_cm)
                print(f"Width/Height Ratio: {width_height_ratio:.2f}")
                
                # If the ratio is very close to 1, consider it a square
                if abs(1 - width_height_ratio) <= square_tolerance:
                    print("Considered as a SQUARE")
                else:
                    print("Considered as a RECTANGLE")
                
                return round(width_cm, 2), round(height_cm, 2)
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

# Example usage with dynamically retrieved DPI
image_dimensions = get_image_dimensions('uploads/square1.png', unit='cm')

if image_dimensions:
    image_width, image_height = image_dimensions
    print(f"Width: {image_width} cm, Height: {image_height} cm")
else:
    print("Failed to retrieve image dimensions.")