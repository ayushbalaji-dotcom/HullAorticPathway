import streamlit as st

st.set_page_config(page_title="AS Intervention Pathway Decision Tool", layout="wide")

# Read the HTML file directly from the local directory
with open("AS_Decision_Tool.html", "r", encoding="utf-8") as f:
    html_code = f.read()

# Render it inside an isolated Iframe component
st.components.v1.html(html_code, height=900, scrolling=True)
