import streamlit as st

# Initialize session state 
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""

#  Login Form 
if not st.session_state.logged_in:
    st.title("🔐 Login Page")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Log in"):
        if username in users and users[username] == password:
            st.session_state.logged_in = True
            st.session_state.username = username
            st.success(f"Welcome, {username}!")
            st.rerun()
        else:
            st.error("Incorrect username or password.")

else:
    # User is logged in 
    st.sidebar.success(f"✅ Logged in as {st.session_state.username}")
    
    if st.sidebar.button("Log out"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.success("Logged out.")
        st.rerun()

    st.title("🏠 Welcome to the Home Page")
    st.write(f"Hello, **{st.session_state.username}**! You are now logged in.")
