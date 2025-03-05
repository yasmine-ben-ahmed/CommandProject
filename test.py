import requests

# Upload an image
image_path = "uploads/rectangle.png"  # Replace with your actual image path
url = "http://127.0.0.1:8000/process/"

with open(image_path, "rb") as img:
    response = requests.post(url, files={"file": img})

print(response.json())  # Display the response


