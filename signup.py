import streamlit as st
import sqlite3
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from imdb import IMDb
from PIL import Image
import requests
from io import BytesIO
import random

# Function to initialize the database and create the users table
def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            preferences TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Function to handle the sign-in page
def sign_in():
    st.title("Sign In")

    conn = sqlite3.connect('users.db')
    c = conn.cursor()

    username = st.text_input("Username")
    password = st.text_input("Password", type='password')

    if st.button("Sign In", key="sign_in_button"):
        c.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
        user = c.fetchone()
        if user:
            st.success("Welcome back!")
            st.set_query_params(user=username)
            st.session_state['user'] = username
            st.experimental_rerun()  # Reload the app to go to the home page
        else:
            st.error("Invalid username or password")

    if st.button("Go to Sign Up", key="go_to_sign_up"):
        st.session_state['page'] = 'sign_up'
        st.experimental_rerun()

    conn.close()

# Function to handle the sign-up page
def sign_up():
    st.title("Sign Up")

    conn = sqlite3.connect('users.db')
    c = conn.cursor()

    new_username = st.text_input("Choose a Username")
    new_password = st.text_input("Choose a Password", type='password')

    if st.button("Sign Up", key="sign_up_button"):
        try:
            c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (new_username, new_password))
            conn.commit()
            st.success("Account created successfully! Please sign in.")
            st.session_state['page'] = 'sign_in'  # Redirect to sign-in page
            st.experimental_rerun()
        except sqlite3.IntegrityError:
            st.error("Username already taken. Please choose a different one.")
    conn.close()

# Function to fetch movie details
def fetch_movie_details(title):
    ia = IMDb()
    movies = ia.search_movie(title)
    if movies:
        movie_id = movies[0].movieID
        movie = ia.get_movie(movie_id)
        image_url = movie.get('full-size cover url', '')
        director = ', '.join([d['name'] for d in movie.get('directors', [])])
        cast = ', '.join([actor['name'] for actor in movie.get('cast', [])[:5]])
        plot_keywords = movie.get('plot outline', 'No plot available')
        return image_url, director, cast, plot_keywords
    return None, '', '', ''

# Function to recommend movies based on user preferences
def recommend_movies(user_preferences, data, similarity):
    if not user_preferences:
        return random.sample(list(data['title']), 16)

    scores = pd.Series([0] * len(data))
    for genre in user_preferences.split(","):
        genre_movies = data[data['genres'].str.contains(genre, case=False, na=False)]
        if not genre_movies.empty:
            genre_indices = genre_movies.index
            genre_scores = similarity[genre_indices].mean(axis=0)
            scores += genre_scores
    scores = scores.nlargest(16)
    return data['title'].iloc[scores.index]

# Function to update user preferences
def update_preferences(username, new_genre):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT preferences FROM users WHERE username=?", (username,))
    preferences = cursor.fetchone()[0]
    if new_genre not in preferences:
        if preferences:
            preferences += "," + new_genre
        else:
            preferences = new_genre
        cursor.execute("UPDATE users SET preferences=? WHERE username=?", (preferences, username))
        conn.commit()
    conn.close()

# Function to handle the home page
def home():
    data = pd.read_csv("grouped_movies_merge.csv")
    tfidf = TfidfVectorizer(stop_words="english")
    tfidf_matrix = tfidf.fit_transform(data["genres"].tolist())
    similarity = cosine_similarity(tfidf_matrix)

    query_params = st.experimental_get_query_params()
    username = query_params.get('user', [None])[0]

    if not username:
        st.warning("Please sign in to see personalized recommendations.")
        st.experimental_rerun()
        return

    st.header(f"Welcome, {username}!")
    st.subheader("Personalized Movie Recommendations")

    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT preferences FROM users WHERE username=?", (username,))
    user_preferences = cursor.fetchone()[0]
    conn.close()

    recommended_titles = recommend_movies(user_preferences, data, similarity)

    # Show recommended movies in a slideshow
    for title in recommended_titles:
        image_url, director, cast, _ = fetch_movie_details(title)
        if image_url:
            response = requests.get(image_url)
            img = Image.open(BytesIO(response.content))
            st.image(img, caption=title, use_column_width=True)
            st.markdown(f"**Director:** {director}")
            st.markdown(f"**Cast:** {cast}")
            if st.button("Overview", key=f"overview-{title}"):
                st.experimental_set_query_params(title=title)
                st.experimental_rerun()  # Reload to the detail page

    st.subheader("Search Movies")
    input_value = st.text_input("Enter a movie title", "")
    if st.button("Search", key="search_button"):
        recommended_titles = data[data['title'].str.contains(input_value, case=False, na=False)]['title']
        cols = st.columns(4)
        for i, title in enumerate(recommended_titles):
            image_url, director, cast, plot_keywords = fetch_movie_details(title)
            with cols[i % 4]:
                if image_url:
                    response = requests.get(image_url)
                    img = Image.open(BytesIO(response.content))
                    st.image(img, caption=title, use_column_width=True)
                    st.markdown(f"**Director:** {director}")
                    st.markdown(f"**Cast:** {cast}")
                    if st.button("Overview", key=f"overview-{title}-search"):
                        st.experimental_set_query_params(title=title)
                        st.experimental_rerun()  # Reload to the detail page
                        update_preferences(username, title)

    if st.button("Log Out", key="logout_button"):
        st.session_state.pop('user', None)
        st.experimental_rerun()  # Reload to the sign-in page

# Main function to initialize the app
if __name__ == "__main__":
    init_db()  # Initialize the database

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
