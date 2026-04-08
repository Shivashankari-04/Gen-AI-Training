import streamlit as st
import time
from sentiment_pipeline import build_sentiment_graph
import os

# Set UI Configuration
st.set_page_config(page_title="AI Sentiment Router", page_icon="🧠", layout="centered")

st.title("Dynamic Feedback Router 🧠")
st.markdown("Enter your query or feedback below. The **LangGraph** backend will cleanly process it through Pandas, analyze the sentiment, and route it to the proper logical node dynamically.")

# Input Form
user_input = st.text_area("Your Query/Feedback:", placeholder="Type your experience here... (e.g. 'I absolutely loved the service!' or 'The delivery was terrible.')")

# UI Container to drop results into
result_container = st.empty()

if st.button("Submit Feedback", type="primary"):
    if user_input:
        with st.spinner("Executing LangGraph Nodes (Ingest ➔ Analyze ➔ Route) ..."):
            # Delay slightly just for visual effect on the web app indicating processing
            time.sleep(1) 
            
            # Setup env variables correctly so tracing still works if the user wants it!
            os.environ["LANGCHAIN_TRACING_V2"] = "true"
            os.environ["LANGCHAIN_PROJECT"] = "sentiment-webapp"
            
            pipeline = build_sentiment_graph()
            initial_state = {"raw_query": user_input, "clean_query": "", "sentiment": "", "response": ""}
            
            # Trigger workflow mathematically
            result = pipeline.invoke(initial_state)
            
            with result_container.container():
                st.divider()
                st.subheader("LangGraph Route Results:")
                
                # Dynamic mapping for clean UI colors
                color_map = {"POSITIVE": "green", "NEGATIVE": "red", "NEUTRAL": "gray"}
                label_color = color_map.get(result["sentiment"], "gray")
                
                st.markdown(f"**Detected Sentiment / Path Traversed:** :{label_color}[{result['sentiment']}]")
                st.info(f"**Generated Route Response:** {result['response']}")
    else:
        st.warning("Please enter a query first before testing the routing!")
