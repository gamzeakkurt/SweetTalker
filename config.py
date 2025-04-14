# config.py
import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
genai.configure(api_key=("GOOGLE_API_KEY"))