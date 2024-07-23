import streamlit as st
from imdb import IMDb
from PIL import Image
import requests
from io import BytesIO

def app():
    query_params = st.experimental_get_query_params()
    title = query_params.get('title', [None])[0]

    if not title:
        st.warning("Please select a movie to see its details.")
        st.stop()

    ia = IMDb()
    movies = ia.search_movie(title)
    if movies:
        movie_id = movies[0].movieID
        movie = ia.get_movie(movie_id)
        image_url = movie.get('full-size cover url', '')
        director = ', '.join([d['name'] for d in movie.get('directors', [])])
        cast = ', '.join([actor['name'] for actor in movie.get('cast', [])[:5]])
        plot_keywords = movie.get('plot outline', 'No plot available')

        st.title(movie['title'])
        if image_url:
            response = requests.get(image_url)
            img = Image.open(BytesIO(response.content))
            st.image(img, use_column_width=True)
        st.markdown(f"**Director:** {director}")
        st.markdown(f"**Cast:** {cast}")
        st.markdown(f"**Plot:** {plot_keywords}")
    else:
        st.error("Movie details not found.")