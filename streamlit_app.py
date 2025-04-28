import streamlit as st

vo2Max_retrevial = st.Page("VO2Max_retrevial.py", title="VO2 Max Retrevial/Report")
vo2Max_impl = st.Page("VO2Max_impl.py", title="VO2 Max Implementation")
#rmr_impl = st.Page("RMR_impl.py", title="RMR Implementation")
#rmr_retrevial = st.Page("RMR_retrevial.py", title="RMR Retrevial/Report")
home = st.Page("home.py", title="Home")

pg = st.navigation(
    {
        "🏠 HOMEPAGE": [home], 
        "📂 UPLOADER": [vo2Max_impl := st.Page("VO2Max_impl.py", title="Upload Data")],
        "📑 REPORTS": [
            report_creator_page := st.Page("report_creator_page.py", title="Create Report"),
            data_viewer := st.Page("report_viewer_page.py", title="View Report")
        ]
    }
)

st.set_page_config(page_title="CHAMP HPL SCSU", page_icon=":material/edit:", layout="wide", initial_sidebar_state="expanded")
pg.run()