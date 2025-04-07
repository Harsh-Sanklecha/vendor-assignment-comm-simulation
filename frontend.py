import streamlit as st
import requests

FASTAPI_URL = "http://localhost:8000/process-task"

# Sample categories and urgency levels
categories = ["plumbing", "electrical", "cleaning", "other"]
urgency_levels = ["low", "medium", "high"]

st.title("Vendor Assignment & Communication Simulation")

# Create a form
with st.form(key='task_form'):
    task_description = st.text_area("Task Description", placeholder="Describe the task...")
    category = st.selectbox("Category", options=categories, index=None, placeholder="Select a category (optional)")
    urgency = st.radio("Urgency", options=urgency_levels)
    special_requirements = st.text_area("Special Requirements", placeholder="Any special requirements...")

    # Form submission button
    submit_button = st.form_submit_button(label='Submit')

    if submit_button:
        if not task_description:
            st.error("Task description is required.")
        else:
            # Prepare data payload
            payload = {
                "task_description": task_description,
                "category": category,
                "urgency": urgency,
                "special_requirements": special_requirements
            }

            try:
                # Send POST request to FastAPI
                response = requests.post(FASTAPI_URL, json=payload)
                response.raise_for_status()  # Raise exception for HTTP errors

                # Process response
                result = response.json()
                st.success("Task processed successfully!")
                st.write("**Response from server:**", result)

            except requests.exceptions.RequestException as e:
                st.error(f"An error occurred: {e}")
