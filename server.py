import streamlit as st
from dashboard import show_dashboard
from accueil import show_accueil
from carte import show_carte

st.set_page_config(page_title="Accidents Routiers Québec", layout="wide")

st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Accueil", "Dashboard", "Carte"])

if page == "Accueil":
    show_accueil()

elif page == "Dashboard":
    show_dashboard()

elif page == "Carte":
    show_carte()
