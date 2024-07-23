import streamlit as st
import pandas as pd
from PIL import Image
from io import BytesIO
import requests

# Load the movie data
try:
    data = pd.read_csv('MovieGenre.csv', encoding='utf-8')
except UnicodeDecodeError:
    # If utf-8 fails, try latin-1
    data = pd.read_csv('MovieGenre.csv', encoding='latin-1')

def fetch_movie_details(title):
    try:
        movie = data[data['Title'] == title].iloc[0]
        imdb_link = movie['Imdb Link']
        imdb_score = movie['IMDB Score']
        genre = movie['Genre']
        poster_link = movie['Poster']
        return imdb_link, imdb_score, genre, poster_link
    except IndexError:
        return None, None, None, None

def recommend_movies_by_genre_or_title(input_value, genre=None, search_by='genre'):
    if search_by == 'genre':
        genre_movies = data[data['Genre'].str.contains(genre, case=False, na=False)]
        if genre_movies.empty:
            return []
        recommended_titles = genre_movies['Title']
    else:
        recommended_titles = data[data['Title'].str.contains(input_value, case=False, na=False)]['Title']
    
    return recommended_titles.tolist()

def main():
    st.title("Movie Recommender System")
    
    # Slideshow of movies
    st.subheader("Featured Movies")
    featured_movies = data.sample(5)
    for _, row in featured_movies.iterrows():
        st.image(row['Poster'], caption=row['Title'], use_column_width=True)
    
    # Layout for inputs
    input_col, genre_col = st.columns([2, 1])
    
    # Search input for title
    input_value = input_col.text_input("Enter a movie title", "")
    
    # Select box for genre
    selected_genre = genre_col.selectbox("Select a genre", data['Genre'].unique())
    
    # Button to trigger recommendation
    if input_col.button("Recommend Movies"):
        if input_value:
            st.write(f"Top movie recommendations based on title: {input_value}")
            recommended_titles = recommend_movies_by_genre_or_title(input_value, search_by='title')
        elif selected_genre:
            st.write(f"Top movie recommendations based on genre: {selected_genre}")
            recommended_titles = recommend_movies_by_genre_or_title(None, genre=selected_genre, search_by='genre')
        else:
            st.write("Please enter a movie title or select a genre to get recommendations.")
        
        for i, title in enumerate(recommended_titles):
            imdb_link, imdb_score, genre, poster_link = fetch_movie_details(title)
            if poster_link:
                try:
                    response = requests.get(poster_link)
                    img = Image.open(BytesIO(response.content))
                    st.image(img, caption=title, use_column_width=True)
                    st.markdown(f"**IMDB Link:** [{title}]({imdb_link})")
                    st.markdown(f"**IMDB Score:** {imdb_score}")
                    st.markdown(f"**Genre:** {genre}")
                except Exception as e:
                    st.warning(f"Failed to load poster for {title}: {e}")

# Start the app
if __name__ == "__main__":
    main()