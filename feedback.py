import json
from datetime import datetime
import google.generativeai as genai
import pandas as pd
import streamlit as st
from config import genai  
import json
import re

def analyze_feedback_with_llm(text):
    if not text.strip():
        return {"sentiment": "Neutral", "insight": ""}

    try:
        # Make sure your API is set up before this

        prompt = f"""
        Analyze the following feedback and return only a JSON object with two fields:
        - "sentiment": one of ["Positive", "Neutral", "Negative"]
        - "insight": a short summary of what the user felt

        Feedback: "{text}"

        Respond with ONLY the JSON, no explanations or markdown.
        """

        model = genai.GenerativeModel(model_name="gemini-2.0-flash")
        response = model.generate_content(prompt)
        raw_text = response.text.strip()

        # Try to extract and parse JSON safely
        try:
            return json.loads(raw_text)
        except json.JSONDecodeError:
            # Fallback: extract JSON-like substring with regex
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


def store_feedback(dish_name, rating, detailed_feedback, sentiment, insight,model_version,adaptation_type):
    feedback_data = {
        "timestamp": datetime.now().isoformat(),
        "dish_name": dish_name,
        "rating": rating,
        "detailed_feedback": detailed_feedback,
        "sentiment": sentiment,
        "insight": insight,
        'model_version':model_version,
        "adaptation_type": adaptation_type 
    }
    with open("feedback_log.json", "a") as f:
        f.write(json.dumps(feedback_data) + "\n")
   

def collect_feedback_ui(dish_name,model_version):
    st.markdown("### 💬 Rate this Recipe")
    rating = st.radio("How would you rate this recipe?", ["Great", "Good", "Okay", "Bad"], horizontal=True)
    detailed_feedback = st.text_area("Tell us what you liked or what could be improved:")

    if st.button("Submit Feedback"):
        analysis = analyze_feedback_with_llm(detailed_feedback)
        store_feedback(dish_name, rating, detailed_feedback, analysis["sentiment"], analysis["insight"],model_version,adaptation_type='None')
        st.success("✅ Thank you! Your feedback was submitted.")

def visualize_feedback_dashboard():
    st.markdown("## 📊 User Feedback Overview")
    try:
        with open("feedback_log.json", "r") as f:
            data = [json.loads(line) for line in f]

        df = pd.DataFrame(data)
        st.bar_chart(df["rating"].value_counts())
        st.bar_chart(df["sentiment"].value_counts())
        st.dataframe(df)
    except FileNotFoundError:
        st.warning("No feedback data available yet.")
