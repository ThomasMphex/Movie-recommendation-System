from pages.signin import app as signin_app
from pages.signup import app as signup_app
from pages.home import app as home_app
from pages.detail import app as detail_app
import streamlit as st
from multipage import MultiPage

# Create an instance of the app
app = MultiPage()

# Title of the main page
st.title("Movie Recommender System")

# Add all your applications (pages) here
app.add_page("Sign In", signin_app)
app.add_page("Sign Up", signup_app)
app.add_page("Home", home_app)
app.add_page("Detail", detail_app)

# The main app
app.run()
