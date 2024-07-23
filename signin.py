import streamlit as st
import sqlite3
import pandas as pd
import cv2
import face_recognition
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from imdb import IMDb
from PIL import Image
import requests
from io import BytesIO
import random
import os

# Function to initialize the database and create the users table
def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            preferences TEXT,
            face_encoding BLOB
        )
    ''')
    conn.commit()
    conn.close()

# Function to add face_encoding column if it doesn't exist
def add_face_encoding_column():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    try:
        c.execute('ALTER TABLE users ADD COLUMN face_encoding BLOB')
        conn.commit()
    except sqlite3.OperationalError as e:
        print("Column face_encoding already exists or another error occurred:", e)
    conn.close()

# Function to encode face image
def encode_face_image(image_path):
    image = face_recognition.load_image_file(image_path)
    encodings = face_recognition.face_encodings(image)
    if encodings:
        return encodings[0]
    else:
        return None

# Function to handle the sign-in page with face recognition
def sign_in():
    st.title("Sign In")

    conn = sqlite3.connect('users.db')
    c = conn.cursor()

    username = st.text_input("Username")

    st.write("Use your webcam for face recognition:")
    if st.button("Start Webcam", key="start_webcam"):
        cap = cv2.VideoCapture(0)
        ret, frame = cap.read()
        if ret:
            face_image_path = f"{username}_sign_in.jpg"
            cv2.imwrite(face_image_path, frame)
            cap.release()
            cv2.destroyAllWindows()

            c.execute("SELECT * FROM users WHERE username = ?", (username,))
            user = c.fetchone()
            if user:
                stored_face_encoding = user[-1]
                if stored_face_encoding is not None:
                    stored_face_encoding = np.frombuffer(stored_face_encoding, dtype=np.float64)
                    current_face_encoding = encode_face_image(face_image_path)

                    if current_face_encoding is not None:
                        results = face_recognition.compare_faces([stored_face_encoding], current_face_encoding)
                        if results[0]:
                            st.success("Welcome back!")
                            st.experimental_set_query_params(user=username)
                            st.session_state['user'] = username
                            st.experimental_rerun()  # Reload the app to go to the home page
                        else:
                            st.error("Face does not match the username provided.")
                    else:
                        st.error("Face not detected in the current image.")
                else:
                    st.error("No face encoding found for this user. Please sign up first.")
            else:
                st.error("Invalid username.")
        else:
            st.error("Failed to capture image from webcam.")

    conn.close()

# Function to handle the sign-up page with face recognition
def sign_up():
    st.title("Sign Up")

    conn = sqlite3.connect('users.db')
    c = conn.cursor()

    new_username = st.text_input("Choose a Username")
    new_password = st.text_input("Choose a Password", type='password')
    face_image_file = st.file_uploader("Upload a face image", type=["jpg", "jpeg", "png"])

    if st.button("Sign Up", key="sign_up"):
        if face_image_file is not None:
            face_image_path = f"{new_username}_sign_up.jpg"
            with open(face_image_path, "wb") as f:
                f.write(face_image_file.getbuffer())

            face_encoding = encode_face_image(face_image_path)

            if face_encoding is not None:
                face_encoding_blob = face_encoding.tobytes()
                try:
                    c.execute("INSERT INTO users (username, password, face_encoding) VALUES (?, ?, ?)", 
                              (new_username, new_password, face_encoding_blob))
                    conn.commit()
                    st.success("Account created successfully! Please sign in.")
                    st.session_state['page'] = 'sign_in'  # Redirect to sign-in page
                    st.experimental_rerun()
                except sqlite3.IntegrityError:
                    st.error("Username already taken. Please choose a different one.")
            else:
                st.error("Face not detected in the uploaded image.")
        else:
            st.error("Please upload a face image.")
    conn.close()

# Main function to initialize the app
if __name__ == "__main__":
    init_db()  # Initialize the database
    add_face_encoding_column()  # Ensure face_encoding column exists

    if 'page' not in st.session_state:
        st.session_state['page'] = 'sign_in'

    if st.session_state['page'] == 'sign_in':
        if 'user' not in st.session_state:
            sign_in()
        else:
            home()
    elif st.session_state['page'] == 'sign_up':
        sign_up()

    st.sidebar.title("Navigation")
    if st.sidebar.button("Sign In", key="sidebar_sign_in"):
        st.session_state['page'] = 'sign_in'
        st.experimental_rerun()
    if st.sidebar.button("Sign Up", key="sidebar_sign_up"):
        st.session_state['page'] = 'sign_up'
        st.experimental_rerun()
