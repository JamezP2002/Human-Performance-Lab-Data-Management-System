import streamlit as st

vo2Max_retrevial = st.Page("VO2Max_retrevial.py", title="VO2 Max Retrevial/Report")
vo2Max_impl = st.Page("VO2Max_impl.py", title="VO2 Max Implementation")
#rmr_impl = st.Page("RMR_impl.py", title="RMR Implementation")
#rmr_retrevial = st.Page("RMR_retrevial.py", title="RMR Retrevial/Report")
home = st.Page("home.py", title="Home")

pg = st.navigation(
    {
        "Homepage": [home], 
        "Uploader": [vo2Max_impl],
        "Report Creator": [report_creator_page := st.Page("searchFunctionalityTest.py", title="Report Creator")],
    }
)

st.set_page_config(page_title="CHAMP HPL SCSU", page_icon=":material/edit:", layout="wide", initial_sidebar_state="expanded")
pg.run()