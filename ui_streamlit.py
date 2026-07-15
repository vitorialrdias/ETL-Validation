from src.interface import interface

from config.logging import setup_logging
setup_logging()

if __name__ == "__main__":
    # Run the streamlit graphical interface
    # bash >> streamlit run ui_streamlit.py
    interface()