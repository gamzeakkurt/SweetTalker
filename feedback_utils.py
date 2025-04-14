import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import json
import seaborn as sns
from collections import Counter
import re
import pandas as pd
import streamlit as st
from collections import Counter
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import nltk


def visualize_feedback_dashboard(recipe,dish_name):
    st.title("📊 Feedback Dashboard")

    try:
        with open("feedback_log.json", "r") as f:
            feedback_lines = f.readlines()
            data = [json.loads(line) for line in feedback_lines]
    except FileNotFoundError:
        st.warning("⚠️ No feedback data found.")
        return

    if not data:
        st.warning("No feedback to display.")
        return

    df = pd.DataFrame(data)
    #Extracting Features
    df['year'] = pd.to_datetime(df['timestamp'], errors='coerce').dt.year
    df['month'] = pd.to_datetime(df['timestamp'], errors='coerce').dt.month
    df['day'] = pd.to_datetime(df['timestamp'], errors='coerce').dt.day
    df['hour'] = pd.to_datetime(df['timestamp'], errors='coerce').dt.hour

    sentiment_filter = st.selectbox("Filter by Sentiment", ["All", "Positive", "Neutral", "Negative"])
    if sentiment_filter != "All":
        df = df[df["sentiment"] == sentiment_filter]
 
 # Evalution of Recipe
   

    st.subheader("📋 Collected Feedback")
  
    columns_to_include = [col for col in df.columns if col not in ['issues', 'suggestions']]
    st.dataframe(df[columns_to_include])


    # Assuming df is your dataframe
    # Group data by dish name and rating, then count occurrences
    rating_counts = df.groupby(['dish_name', 'rating']).size().unstack().fillna(0)

    # Display a bar chart in Streamlit
    st.subheader("🍽️ Dish Ratings Overview")
    st.bar_chart(rating_counts)
    

    st.subheader("💬 Sentiment Distribution")
    sentiment_counts = df["sentiment"].value_counts()
    fig1, ax1 = plt.subplots()
    ax1.pie(sentiment_counts, labels=sentiment_counts.index, autopct='%1.1f%%', startangle=90)
    ax1.axis("equal")
    st.pyplot(fig1)
    
    # Ensure NLTK assets are downloaded
    # Add custom first-person and domain filler words
    EXTRA_STOPWORDS = {"i", "me", "my", "mine", "user", "users", "recipe", "like", "want", "dont", "didnt", "think", "just"}

    def clean_text(text):
        text = text.lower()
        text = re.sub(r'[^\w\s,]', '', text)  # Remove emojis/symbols
        text = re.sub(r'\d+', '', text)       # Remove digits
        text = re.sub(r'[^\w\s]', '', text)   # Remove punctuation
        return text

    def preprocess_insights(insight_list):
        stop_words = set(stopwords.words('english')).union(EXTRA_STOPWORDS)
        words = []

        for sentence in insight_list:
            cleaned = clean_text(sentence)
            tokens = word_tokenize(cleaned)
            filtered = [word for word in tokens if word not in stop_words and len(word) > 1]
            words.extend(filtered)

        return words

    # Streamlit UI block
    st.subheader("🧠 Common User Detailed Feedback")

    if "insight" in df.columns:
        insights = df["detailed_feedback"].dropna().tolist()
        processed_words = preprocess_insights(insights)
        common_phrases = Counter(processed_words).most_common(10)

        st.write(pd.DataFrame(common_phrases, columns=["Word", "Count"]))
    else:
        st.info("No insights available to analyze.")


    
    st.subheader("🕒 Feedback Distribution by Hour")
    # Group by hour and count entries
    hourly_feedback = df['hour'].value_counts().sort_index()

    # Plot with Streamlit's built-in bar chart
    st.bar_chart(hourly_feedback)

    st.subheader("📊 Sentiment Summary per Dish")
    if "sentiment" in df.columns:
        sentiment_summary = df.groupby(['dish_name', 'sentiment']).size().unstack().fillna(0)
        st.bar_chart(sentiment_summary)

    st.subheader("🧪 A/B Test: Model Sentiment Distribution")
    if "model_version" in df.columns:
        model_perf = df.groupby(['model_version', 'sentiment']).size().unstack().fillna(0)
        st.bar_chart(model_perf)

    
    #Evaluation Results

    latest_row = df.iloc[-1]
    print(latest_row)
    clarity = latest_row["clarity_score"]
    accuracy = latest_row["accuracy_score"]
    issues = latest_row["issues"]
    suggestions = latest_row["suggestions"]

    st.markdown("### 🧪 Recipe Evaluation by Chef Critic (LLM)")
    st.write(f"**Clarity Score:** {clarity}/10")
    st.write(f"**Accuracy Score:** {accuracy}/10")
    st.write(f"**Issues:** {issues}")
    st.write(f"**Suggestions:** {suggestions}")
