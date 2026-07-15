import streamlit as st
from config.logging import logger
from src.read_tables import read_tables
from src.etl_validation import Validate

# Page configuration
st.set_page_config(page_title="ETL Validation", layout="wide", page_icon="🔍")

def interface():
    """Main interface for ETL validation process."""
    
    if "step" not in st.session_state:
        st.session_state.step = 0

    st.title("ETL Validation")
    st.caption("Compare a reference table with a target table to validate data migration.")

    col1, col2 = st.columns(2, gap="large")

    with col1:
        st.subheader("Reference Table and Target Table Configuration")
        
        # Reference Table fields
        reference_table = st.text_input("Reference table:", placeholder='STG_MRH').upper()
        c1, c2 = st.columns(2)
        reference_server = c1.text_input("Reference server:", placeholder='stg, dw').lower()
        reference_host = c2.selectbox("Reference host:", options=["52", "53"])

        st.divider()

        # Target fields
        target_table = st.text_input("Target table (to validate):", placeholder='STG_MRH').upper()
        c3, c4 = st.columns(2)
        target_server = c3.text_input("Target server:", placeholder='stg, dw').lower()
        target_host = c4.selectbox("Target host:", options=["52", "53"])

        start_validation = st.button("Start validation", use_container_width=True)

    result_container = st.container()
    with col2:
        st.subheader("Validation result")
        
        if start_validation:
            # Check if all fields are filled
            if all([reference_table, reference_server, reference_host, target_table, target_server, target_host]):
                try:
                    df_reference, df_target = read_tables(
                        [reference_table, reference_server, reference_host], 
                        [target_table, target_server, target_host]
                    )
                    
                    logger.info("Initializing validations...")
                    validator = Validate(df_reference, df_target)
                    
                    # Run validations
                    same_column_names = validator.validate_column_names()
                    is_metadata_valid = all([
                        validator.validate_number_columns(),
                        same_column_names,
                        not validator.validate_column_types(),
                        validator.validate_number_rows()
                    ])
                    
                    # Show data sample if columns match
                    if is_metadata_valid:
                        st.divider()
                        with result_container:
                            with st.expander("Sample viewer", expanded=True):
                                data_validation = validator.validate_data()
                    
                    # Final result
                    if is_metadata_valid and data_validation:
                        st.success("✅ Metadata validation completed successfully.")
                        st.session_state.step = 1
                    else:
                        st.warning("⚠ Metadata validation finished with inconsistencies.")
                        
                except Exception as e:
                    logger.error(f"Validation process error: {e}")
                    st.error("WARNING! Check the SERVER or TABLE NAME.\n\n"
                             f"Validation process error: {e}")
            else:
                st.error("Please fill in all reference tableand target fields before starting.")
        else:
            st.info("Fill in the fields on the left and click **Start validation** to see results here.")

if __name__ == "__main__":
    interface()