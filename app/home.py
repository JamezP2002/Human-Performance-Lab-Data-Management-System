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
    <meta name="description" content="CHAMP Human Performance Lab Data Management System">
    
    <div class="container">
        <div class="header">
            <h1>Welcome to the CHAMP Human Performance Lab Portal</h1>
        </div>
        <div class="content">
            <p>
                This portal is the Human Performance Lab Data Management System for the CHAMP Lab
                at Southern Connecticut State University. It streamlines the storage, processing,
                reporting, and visualization of physiological test data, currently supporting
                VO₂ Max tests.
            </p>
            <p>
                The system integrates MongoDB for data storage, AWS S3 for report storage, and 
                Streamlit for an interactive web-based interface.
            </p>
            <p>
                <b>Available Features:</b>
            </p>
            <p class="features">
                - <b>Upload Test Data</b>: Upload VO₂ Max test results and protocols.<br>
                - <b>Create Reports</b>: Build and save detailed lab reports with plots and comments.<br>
                - <b>View/Download Reports</b>: Search clients and download finalized reports.<br>
                - <b>Secure Cloud Storage</b>: All reports are automatically uploaded to AWS S3.
            </p>
            <p>
                Use the navigation sidebar to get started!
            </p>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)
