import os
from PIL import Image
from dotenv import load_dotenv
from config import genai  

# Function to recognize the dish using Gemini
def recognize_dish(image_path):
    """
    Uses Gemini to recognize the patisserie/dessert in an image.
    """
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        image = Image.open(image_path)

        prompt = """You are a professional pastry chef AI.
        A user has uploaded a photo of a patisserie dish.
        Please identify what dessert or pastry is in the image.
        Respond only with the name of the dish."""

        response = model.generate_content([prompt, image])
        return response.text.strip()

    except Exception as e:
        return f"Error: {str(e)}"
