import os
from dotenv import load_dotenv
import google.generativeai as genai
import random
from config import genai 
import json
load_dotenv()

# A/B Testing: Choose a model version at random
def get_ab_test_model():
    return random.choice(["gemini-2.0-flash", "gemini-1.5-flash"])
# Configure the Gemini API key
model_version = get_ab_test_model()

# Use the Gemini Flash 2.0 model
model = genai.GenerativeModel(model_name=model_version)

class RecipeAgentWithContext:
    def __init__(self, dish_name):
        self.dish_name = dish_name
        self.history = []
        self.model_version = model_version
        self.latest_recipe = {} 
      

    def update_history(self, user_input, response):
        """Update the history with the latest user input and agent's response."""
        self.history.append({
            "user_input": user_input,
            "response": response
        })  

    def process_input(self, user_input):
        """Handle user input and maintain context."""
        # You can maintain a context history that grows over time
        context = "\n".join([f"User: {entry['user_input']}\nAI: {entry['response']}" for entry in self.history])
        
        if "recipe" in user_input:
            response = self.get_recipe(context)
        elif "adaptation" in user_input or "personalized" in user_input:
            response = self.get_personalized_recipe(context)
    
        else:
            response = "I'm sorry, I didn't understand that. Can you clarify?"
        
        # Update history with the new input-response pair
        self.update_history(user_input, response)

        return response

    def get_recipe(self, context):
        # Generate a standard recipe, including context
        return self.generate_recipe(self.dish_name, context)

    def get_personalized_recipe(self, context, adaptation_type="", custom_request=""):
        # Include the context when requesting personalized recipes
        prompt = f"""
        Context: {context}

        You are a pastry chef AI. A user is adapting the recipe for "{self.dish_name}".
        Please rewrite the recipe based on:
        - Adaptation: {adaptation_type}
        - Special Request: {custom_request}
        
        Provide updated ingredients and instructions with friendly explanations.
        """
        return self.generate_recipe(prompt)


    def generate_recipe(self, dish_name):
        """
        Generate a patisserie recipe using Gemini for the given dish.
        """
        prompt = f"""You are a professional pastry chef AI. A user has uploaded a photo of a patisserie dish named "{dish_name}".

    Please provide:
    1. A list of ingredients.
    2. Step-by-step instructions for making the dish.
    3. Nutritional info (optional).
    4. A short fun fact or tip related to the dessert.

    Keep it warm, engaging, and friendly."""

        try:
                model = genai.GenerativeModel(self.model_version)
                response = model.generate_content(prompt)
                recipe_text = response.text if hasattr(response, 'text') else "No recipe generated"
                self.latest_recipe = recipe_text
            
                return self.latest_recipe, self.model_version
    
        except Exception as e:return f"Error generating recipe: {str(e)}"
        
    def evaluate_generated_recipe(self, recipe):
        """Evaluate the generated recipe using Gemini's model."""
        prompt = f"""
        You are a professional pastry chef and culinary critic. Analyze the following AI-generated recipe for "{self.dish_name}":

        {recipe}

        Evaluate the recipe based on:
        1. Clarity (score 1-10)
        2. Technical Accuracy (score 1-10)
        3. Factual issues or confusion
        4. Suggestions for improvement

        Return your response in JSON format like:
        {{
            "clarity_score": int,
            "accuracy_score": int,
            "issues": "text",
            "suggestions": "text"
        }}
        """

        try:
            model = genai.GenerativeModel(model_version)
            response =model.generate_content(prompt)
            evaluation_response = response.text.strip()
            return evaluation_response
        except Exception as e:
            return f"Error evaluating recipe: {str(e)}"
            
    
    def analyze_feedback_with_llm(self, text):
        if not text.strip():
            return {"sentiment": "Neutral", "insight": ""}
        
        try:
            prompt = f"""
            Analyze the following feedback and return only a JSON object with two fields:
            - "sentiment": one of ["Positive", "Neutral", "Negative"]
            - "insight": a short summary of what the user felt
    
            Feedback: "{text}"
    
            Respond with ONLY the JSON, no explanations or markdown.
            """

            model = genai.GenerativeModel(model_version)
            # Generate response using the model
            response = model.generate_content(prompt)
            
            # Assuming response.text is the correct way to access model output
            raw_text = response.text.strip()
    
            # Try to parse the JSON from the model's response
            try:
                return json.loads(raw_text)
            except json.JSONDecodeError:
                print("Error parsing JSON:", raw_text)  # Debugging log for raw output
                # Fallback: try to extract JSON-like structure with regex
                match = re.search(r'\{.*?\}', raw_text, re.DOTALL)
                if match:
                    return json.loads(match.group(0))
                else:
                    return {
                        "sentiment": "Unknown",
                        "insight": "Could not parse the LLM response as valid JSON"
                    }
    
        except Exception as e:
            return {"sentiment": "Unknown", "insight": str(e)}