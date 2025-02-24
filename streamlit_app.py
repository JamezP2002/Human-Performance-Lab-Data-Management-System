import streamlit as st

# Set the title of the homepage
st.title("Welcome to My Streamlit App")

# Add a description
st.write("""
This is the homepage of my Streamlit app. Use the sidebar to navigate to different pages.
""")

# Add a sidebar with navigation options
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Home", "Page 1", "Page 2", "Page 3"])

# Define the content of each page
if page == "Home":
    st.write("You are on the home page.")
elif page == "Page 1":
    st.write("Welcome to Page 1!")
elif page == "Page 2":
    st.write("Welcome to Page 2!")
elif page == "Page 3":
    st.write("Welcome to Page 3!")