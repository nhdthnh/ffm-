import streamlit as st
import streamlit.components.v1 as components

def show():
    # CSS để ghi đè khoảng trắng mặc định của Streamlit (giúp khử thanh cuộn ngoài cùng)
    st.markdown("""
        <style>
               .block-container {
                    padding-top: 2rem;
                    padding-bottom: 0rem;
                    padding-left: 1rem;
                    padding-right: 1rem;
                }
        </style>
    """, unsafe_allow_html=True)

    iframe_html = """
    <div style="width: 100%; height: 92vh; display: flex; justify-content: center; overflow: hidden; margin-top: 1rem;">
        <iframe 
            width="100%" 
            height="100%" 
            src="https://lookerstudio.google.com/embed/reporting/e4e8d459-3b64-4dcf-8a97-7f0cddf3aa38/page/RdfrF" 
            frameborder="0" 
            style="border:0; width: 100%; height: 100%; max-width: 100%; overflow: hidden;" 
            allowfullscreen 
            sandbox="allow-storage-access-by-user-activation allow-scripts allow-same-origin allow-popups allow-popups-to-escape-sandbox">
        </iframe>
    </div>
    """
    
    st.markdown(iframe_html, unsafe_allow_html=True)
