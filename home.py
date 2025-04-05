import streamlit as st

st.markdown(
    """
    <style>
        /* Global Styles */
        body {
            background-color: #f4f7f8;
            font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
        }
        /* Container for the content */
        .container {
            max-width: 900px;
            margin: auto;
            padding: 40px 20px;
            background: white;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            border-radius: 8px;
        }
        /* Logo styling */
        .logo {
            display: block;
            margin: 0 auto 20px auto;
            width: 150px;
        }
        /* Header styling */
        .header {
            text-align: center;
            margin-bottom: 30px;
        }
        .header h1 {
            font-size: 2.8em;
            color: #333;
            margin-bottom: 10px;
        }
        /* Content styling */
        .content p {
            font-size: 1.2em;
            line-height: 1.6;
            color: #555;
            margin: 15px 0;
        }
        /* Feature list styling */
        .features {
            font-size: 1.2em;
            line-height: 1.8;
            color: #444;
            margin: 20px 0;
        }
        .features b {
            color: #222;
        }
    </style>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="Human Performance Lab Data Management System">
    <div class="container">
        <div class="header">
            <h1>Welcome to the CHAMP Human Performance Lab</h1>
        </div>
        <div class="content">
            <p>
                This project/website is a Human Performance Lab Data Management System designed 
                to streamline the storage, processing, and visualization of physiological test 
                data at the CHAMP Human Performance Lab, specifically right now the VO2 Max and 
                Resting Metabolic Rate (RMR) tests. The system utilizes MongoDB for data storage, 
                Pandas for data handling, and Streamlit for an interactive web-based interface.
            </p>
            <p>
                The following features are available:
            </p>
            <p class="features">
                - <b>VO2 Max Retrieval/Report</b>: Retrieve and report VO2 Max data.<br>
                - <b>VO2 Max Uploader</b>: Upload VO2 Max protocols.
            </p>
            <p>
                Explore the sections to learn more about each feature.
            </p>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)
