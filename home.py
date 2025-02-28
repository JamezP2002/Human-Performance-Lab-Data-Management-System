import streamlit as st
st.markdown(
    """
    <div style="text-align: center;">
        <h1><b>Welcome to the CHAMP Human Performance Lab</b></h1>
    </div>
    <div style="text-align: left;">
        <p style="font-size: 20px;">
            This project/website is a Human Performance Lab Data Management System designed 
            to streamline the storage, processing, and visualization of physiological test 
            data at the CHAMP Human Performance Lab, specifically right now the VO2 Max and 
            Resting Metabolic Rate (RMR) tests. The system utilizes MongoDB for data storage, 
            Pandas for data handling, and Streamlit for an interactive web-based interface.
        </p>
        <p style="font-size: 20px;">
            The following features are available:
        </p>
        <p style="font-size: 20px;">
            - <b>VO2 Max Retrevial/Report</b>: Retrieve and report VO2 Max data.<br>
            - <b>VO2 Max Implementation</b>: Implement VO2 Max protocols.
        </p>
        <p style="font-size: 20px;">
            Explore the sections to learn more about each feature.
        </p>
    </div>
    """,
    unsafe_allow_html=True
)