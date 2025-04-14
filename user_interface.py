import streamlit as st
from ingredient_recognition import recognize_dish
from recipe_generation import RecipeAgentWithContext
from feedback import analyze_feedback_with_llm
import urllib.parse
import json
from datetime import datetime
from feedback_utils import visualize_feedback_dashboard

st.set_page_config(page_title="Sweet Talker", page_icon="🍰")

st.markdown("""
<style>
body {
    background-image: url('SweetTalker_logo.png');
    background-size: cover;
    background-repeat: no-repeat;
    background-position: center center;
    background-attachment: fixed;
    color: #000;
}

.block-container {
    background-color: rgb(241, 239, 223);
    padding: 2rem;
    border-radius: 15px;
}

.brand-description {
    text-align: center;
    font-size: 100px;
    font-weight: normal;
    color: #6b5534;
    margin-top: 20px;
    margin-bottom: 40px;
}

.upload-section {
    display: flex;
    justify-content: center;
    align-items: center;
    margin-top: 40px;
}

.custom-upload {
    background: #6b5534;
    color: white;
    font-size: 20px;
    font-weight: bold;
    padding: 20px 40px;
    border-radius: 12px;
    text-align: center;
    box-shadow: 0 8px 16px rgb(241, 239, 223);
    cursor: pointer;
    transition: all 0.3s ease;
}

.custom-upload:hover {
    
    transform: scale(1.05);
    box-shadow: 0 10px 20px rgb(241, 239, 223);
}

[data-testid="stSidebar"] {
    background-color: rgb(241, 239, 223);
}
</style>
""", unsafe_allow_html=True)

# Brand Logo
st.markdown('<div class="logo-container">', unsafe_allow_html=True)
# Replace this with your own logo file path or URL
st.image("SweetTalker_logo.png", width=2000)  # Or use a local path to your logo
st.markdown('</div>', unsafe_allow_html=True)

# Brand Description (Additional Information)
st.markdown('<p class="brand-description">Upload a photo of your favorite pastry, and get a personalized recipe and much more!</p>', unsafe_allow_html=True)

# Upload section with vibrant styling
st.markdown('<div class="upload-section"><div class="custom-upload"> Upload Your Delicious Treat</div></div>', unsafe_allow_html=True)

# Now show the uploader (label is hidden, user clicks the styled button above)
image = st.file_uploader("Choose an image of your patisserie (Cake, Pastry, etc.)", type=["jpg", "png", "jpeg"], label_visibility="collapsed")

# If the user uploads an image
if image:
    st.image(image, caption="Uploaded Patisserie Image", use_container_width=True)
    
    # Recognize the dish from the uploaded image
    dish_name = recognize_dish(image)
    
    # Display the recognized dish name
    st.write(f"**Recognized Dish**: {dish_name}")

    # Create an instance of RecipeAgentWithContext
    agent = RecipeAgentWithContext(dish_name)

    # Generate the recipe dynamically using the agent's method
    st.write("Generating Recipe... Please wait.")
    recipe,model_version= agent.generate_recipe(dish_name)
   

    # Display the dynamically generated recipe
    st.write("**Recipe Instructions**:")
    st.write(recipe)

    # 👉 Add Download Button for Original Recipe
    original_recipe_text = f"Original Recipe for {dish_name}:\n\n{recipe}"
    st.download_button(
        label="📥 Download Original Recipe",
        data=original_recipe_text,
        file_name=f"{dish_name}_original_recipe.txt",
        mime="text/plain"
    )


    # Streamlit UI for Personalized Recipe Adaptations with Agent Context
    st.markdown("### 🎯 Personalized Recipe Adaptations")

    # Creating two columns for adaptation type and custom requests
    col1, col2 = st.columns(2)
    
    with col1:
        # Radio buttons for adaptation type
        adaptation_type = st.radio("Choose an adaptation:", [
            "None", 
            "Vegan", 
            "Gluten-Free", 
            "Low Sugar", 
            "Use Pantry Ingredients", 
            "Cultural Twist"
        ], help="Select an adaptation based on your preferences. 'None' means no changes.")

    with col2:
        # Text input for custom preferences
        custom_request = st.text_input("Any specific preferences?", 
                                    placeholder="e.g., 'No eggs', 'Use almond milk'", 
                                    help="You can mention any specific ingredient or dietary preference.")

    # If adaptation is chosen or a custom request is made
    if adaptation_type != "None" or custom_request:
        st.write("Generating your personalized recipe... Please wait.")

        # Create a user prompt for the adaptation
        user_prompt = f"personalized recipe with {adaptation_type} adaptation and preferences: {custom_request}"
        
        # Process the prompt using the agent (with context)
        personalized_recipe,_ = agent.get_personalized_recipe(
            context="\n ".join([f"User: {h['user_input']}\nAI: {h['response']}" for h in agent.history]),
            adaptation_type=adaptation_type,
            custom_request=custom_request
        )
        

        agent.update_history(user_prompt, personalized_recipe)
        # Display the personalized recipe
        st.write("**Here’s your personalized version:**")
        
        st.markdown(personalized_recipe.strip())

        # Add a download button for the recipe
        recipe_text = f"Recipe for {dish_name} (Personalized):\n\n{personalized_recipe}"
        st.download_button(
            label="Download Recipe",
            data =recipe_text,
            file_name=f"{dish_name}_personalized_recipe.txt",
            mime="text/plain"
        )

    else:
        st.warning("Please choose an adaptation or provide specific preferences to personalize your recipe.")

    # -- Evaluation Score --
    evaluation_response = agent.evaluate_generated_recipe(recipe)
    try:
        if not evaluation_response:
            raise ValueError("❌ Gemini response is empty.")

        # Gemini may return JSON inside a code block. Strip it.
        if evaluation_response.startswith("```json"):
            evaluation_response = evaluation_response.replace("```json", "").replace("```", "").strip()

        evaluation_data = json.loads(evaluation_response)

        clarity = evaluation_data.get("clarity_score")
        accuracy = evaluation_data.get("accuracy_score")
        issues = evaluation_data.get("issues")
        suggestions = evaluation_data.get("suggestions")

    except Exception as e:
        st.warning("❌ Error parsing recipe evaluation.")
        st.text(f"Error: {str(e)}")
        st.text("Raw Gemini Output:")
        st.text(repr(evaluation_response))

    # -- Collect Feedback --
    st.markdown("### 💬 Rate this Recipe")
    rating = st.radio("How would you rate this recipe?", ["Great", "Good", "Okay", "Bad"], horizontal=True)
    # After displaying dish_name
    confirm = st.radio("Is this the correct dish?", ["Yes", "No"], horizontal=True)

    recognition_correct = True if confirm == "Yes" else False

    # Optional feedback field
    detailed_feedback = st.text_area("Tell us what you liked or what could be improved:")
    
    # Store when user submits
    if st.button("Submit Feedback"):
        # LLM-based sentiment and insight extraction
        analysis = analyze_feedback_with_llm(detailed_feedback)

        # Collect all feedback data
        feedback_data = {
            "timestamp": datetime.now().isoformat(),
            "dish_name": dish_name,
            "rating": rating,
            "detailed_feedback": detailed_feedback,
            "sentiment": analysis["sentiment"],
            "insight": analysis["insight"],
            "model_version":model_version,
            "adaptation_type": adaptation_type,
            "recognition_correct": recognition_correct,
            'clarity_score':evaluation_data['clarity_score'],
            'accuracy_score':evaluation_data['accuracy_score'],
            'issues':evaluation_data['issues'],
            'suggestions':evaluation_data['suggestions']

        }

        # Save to local file
        with open("feedback_log.json", "a") as f:
            f.write(json.dumps(feedback_data) + "\n")

        st.success("✅ Thank you! Your feedback was submitted.")

    if st.sidebar.checkbox("🔍 View Feedback Dashboard (Admin Only)"):
        visualize_feedback_dashboard(recipe,dish_name)
