from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx
import requests
import base64
import re
import numpy as np
from io import BytesIO
from PIL import Image as PilImage
import tensorflow.keras.models as models
from tensorflow.keras.preprocessing import image
from tensorflow.keras.applications.vgg16 import preprocess_input


def classify_image_vgg16(img):
    # Load and preprocess the image
    img_array = image.img_to_array(img)
    img_array = np.expand_dims(img_array, axis=0)
    img_array = preprocess_input(img_array)

    # Make predictions
    return model.predict(img_array)[0][0]


app = FastAPI()

# Load pretrained VGG16 model
model = models.load_model('cats-dogs.keras')
source_url = "https://api.exactly.ai/v0/careers/cat-or-dog/818f697d-29cf-456c-8aa6-baf3dd66c673/"


# Configure CORS
origins = [
    "http://localhost:*",
    # Add other origins as needed, e.g., "http://127.0.0.1:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


def extract_seconds(message: str) -> int:
    # Extract the number of seconds from the message using regex
    match = re.search(r'Please wait (\d+) seconds', message)
    if match:
        return int(match.group(1))
    return 0


@app.post("/next-image/")
async def retrieve_next_image():
    async with httpx.AsyncClient(timeout=60) as client:
        try:
            # Send POST request to the external service
            response = await client.post(source_url)
            response.raise_for_status()  # Raise an error for bad status codes

            response_data = response.json()
            image_data = base64.b64decode(response_data)
            img = PilImage.open(BytesIO(image_data))
            img = img.resize((370, 370))
            result = classify_image_vgg16(img)
            animal = "cat" if result > 0.5 else "dog"
            return {"category": animal, "imageBase64": response_data}

        except httpx.HTTPStatusError as exc:
            # Handle specific HTTP errors from the external service
            if exc.response.status_code == 403:
                try:
                    error_data = exc.response.json()
                    message = error_data.get("client_message", "Forbidden")
                    wait_seconds = extract_seconds(message)
                    raise HTTPException(status_code=403, detail={"message": message, "wait_seconds": wait_seconds})
                except ValueError:
                    raise HTTPException(status_code=403, detail="Forbidden")
            else:
                raise HTTPException(status_code=exc.response.status_code, detail=f"Image source error: {exc.response.text}")

        except httpx.RequestError as exc:
            # Handle request errors (e.g., connection errors)
            raise HTTPException(status_code=502, detail=f"Error communicating with image source: {str(exc)}")

        except ValueError:
            # Handle JSON decode errors
            raise HTTPException(status_code=502, detail="Invalid JSON response from image source")

        except Exception as exc:
            # Handle other possible errors
            raise HTTPException(status_code=500, detail=f"Internal server error: {str(exc)}")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8001)
