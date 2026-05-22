import streamlit as st

st.title("I-SCEET Toolchain")
st.write("Bienvenue dans l'interface I-SCEET")

# Upload des documents
uploaded_files = st.file_uploader("Uploader les documents DO-178C", 
                                  accept_multiple_files=True)

if uploaded_files:
    st.success(f"{len(uploaded_files)} fichiers uploadés") 
