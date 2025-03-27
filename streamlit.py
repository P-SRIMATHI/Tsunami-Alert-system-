import streamlit as st
import numpy as np
import tensorflow as tf
import requests
from twilio.rest import Client
import firebase_admin
from firebase_admin import messaging, credentials
import psycopg2

# Load pre-trained AI model (Placeholder for actual model)
model = tf.keras.models.load_model("disaster_model.h5")

# Twilio credentials for SMS alerts
TWILIO_ACCOUNT_SID = "your_account_sid"
TWILIO_AUTH_TOKEN = "your_auth_token"
TWILIO_PHONE_NUMBER = "your_twilio_number"
client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# Firebase setup for push notifications
cred = credentials.Certificate("firebase_credentials.json")
firebase_admin.initialize_app(cred)

# Database connection (PostgreSQL for resource allocation)
conn = psycopg2.connect(
    database="disaster_db", user="your_user", password="your_password", host="localhost", port="5432"
)
cursor = conn.cursor()

def predict_disaster(sensor_data, location):
    features = np.array(sensor_data).reshape(1, -1)
    prediction = model.predict(features)
    
    if prediction[0][0] > 0.8:  # If AI detects a disaster probability > 80%
        send_alert(location)
        allocate_resources(location)
        return f"Disaster detected at {location}! Probability: {prediction[0][0]:.2f}"
    
    return f"No disaster detected at {location}. Probability: {prediction[0][0]:.2f}"


def send_alert(location):
    message = f"Emergency Alert! A disaster is predicted at {location}. Take necessary precautions."
    
    # Send SMS alert
    client.messages.create(
        body=message,
        from_=TWILIO_PHONE_NUMBER,
        to="+1234567890"  # Replace with real recipient number
    )
    
    # Send push notification via Firebase
    notification = messaging.Message(
        notification=messaging.Notification(
            title="Disaster Alert!",
            body=message
        ),
        topic="disaster_alerts"
    )
    messaging.send(notification)

def allocate_resources(location):
    cursor.execute("SELECT resource FROM resources WHERE status='available' LIMIT 5")
    resources = cursor.fetchall()
    
    if resources:
        cursor.execute("UPDATE resources SET status='deployed' WHERE resource IN %s", (tuple(resources),))
        conn.commit()
    
    return resources

# Streamlit UI
st.title("AI-Powered Disaster Alert System")
st.write("Monitor and predict disasters in real-time using AI.")

sensor_data = st.text_area("Enter Sensor Data (comma-separated values)")
location = st.text_input("Enter Location")

if st.button("Predict Disaster"):
    if sensor_data and location:
        sensor_values = list(map(float, sensor_data.split(',')))
        result = predict_disaster(sensor_values, location)
        st.success(result)
    else:
        st.error("Please enter valid sensor data and location.")
