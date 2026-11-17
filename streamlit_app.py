# Replace the <style> block near the top of streamlit_app.py with this:
st.markdown("""
<style>
.block-container {
    padding-top: 2.8rem !important;
    padding-bottom: 1rem !important;
}
div[data-testid="stHorizontalBlock"] {
    flex-wrap: nowrap !important;
    gap: 0.25rem !important;
}
div[data-testid="stHorizontalBlock"] > div {
    min-width: 0 !important;
}
</style>
""", unsafe_allow_html=True)
