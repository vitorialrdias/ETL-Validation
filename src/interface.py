import streamlit as st 
import pandas as pd
from config.logging import logger

from src.read_tables import read_tables


def interface():
    """ Function to validate tables in migration process"""
    
    
    source = []
    target = []

    if "step" not in st.session_state:
        st.session_state.step = 0
    try:
        st.set_page_config(page_title="ETL Validation", layout="wide")
        st.markdown("""
            <style>
                .block-container {
                    padding-top: 2rem;
                    padding-bottom: 0rem;
                }
            </style>
        """, unsafe_allow_html=True)
        st.title("ETL Validation")
        

        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Insert the reference table and target table to validate")

            # SOURCE
            source.append(
                st.text_input(
                    "Source table (original table used as reference):",
                    placeholder='Exemple: STG_MRH'
                ).upper()
            )

            
            c1, c2 = st.columns(2)
            with c1:

                source.append(
                    st.text_input(
                        "Source server:",
                        placeholder='Exemple: (stg, dw, predial)'
                    ).lower()
                )

            
            with c2:
                source.append(
                    st.selectbox(
                        "Source Host:",
                        options=["52", "53"],
                        placeholder="Select the host"
                    )
                )
                
            st.divider()
            
            # TARGET
            target.append(
                st.text_input(
                    "Target table (Python migrated table to validate):",
                    placeholder='Exemple: STG_MRH'
                ).upper()
            )
            c1, c2 = st.columns(2)            
            with c1:

                target.append(
                    st.text_input(
                        "Target server:",
                        placeholder='Exemple: (stg, dw, predial)'
                    ).lower()
                )
            
            with c2:
                target.append(
                    st.selectbox(
                        "Target Host:",
                        options=["52", "53"],
                        placeholder="Select the host"
                    )
                )

 
            st.markdown("""
            <style>
            div.stButton > button {
                background-color: #CC00;
                color: white;
                font-size: 24px;
                font-weight: bold;
                border-radius: 10px;
            }
            </style>
            """, unsafe_allow_html=True)
            
            start_validation = st.button(
                "Start Validation",
                use_container_width=True,
                type="secondary"
            )
        with col2:
            
            if start_validation:
                if (
                    source[0]
                    and source[1]
                    and source[2]
                    and target[0]
                    and target[1]
                    and target[2]
                ):
                    df_source, df_target = read_tables(source, target)
                    
                    logger.info("Initializing validations...")

                    # ==========================================================
                    # 1. DATAFRAMES
                    # ==========================================================

                    if df_source.empty or df_target.empty:
                        st.error("❌ One or both DataFrames are empty.")
                        st.stop()

                    st.success("✔ DataFrames loaded successfully.")


                    # ==========================================================
                    # 2. NUMBER OF COLUMNS
                    # ==========================================================

                    same_num_columns = len(df_source.columns) == len(df_target.columns)

                    if same_num_columns:
                        st.success(f"✔ Number of columns validated. Source: {len(df_source.columns)} columns | Target: {len(df_target.columns)} columns")
                        logger.info("Validate number of columns")
                    else:
                        st.error(
                            f"❌ Different number of columns\n\n"
                            f"Source: {len(df_source.columns)}\n"
                            f"Target: {len(df_target.columns)}"
                        )


                    # ==========================================================
                    # 3. COLUMN NAMES
                    # ==========================================================

                    same_column_names = list(df_source.columns) == list(df_target.columns)

                    if same_column_names:
                        st.success("✔ Column names validated.")
                        logger.info("Validate column names")

                    else:

                        st.error("❌ Different column names.")

                        source_cols = set(df_source.columns)
                        target_cols = set(df_target.columns)

                        all_columns = sorted(source_cols.union(target_cols))

                        df_columns = pd.DataFrame({
                            "Column": all_columns,
                            "Source": ["✔" if c in source_cols else "" for c in all_columns],
                            "Target": ["✔" if c in target_cols else "" for c in all_columns],
                        })

                        st.dataframe(df_columns, use_container_width=True)


                    # ==========================================================
                    # 4. COLUMN TYPES
                    # ==========================================================

                    type_errors = []

                    if same_column_names:

                        for col in df_source.columns:

                            if str(df_source[col].dtype) != str(df_target[col].dtype):

                                type_errors.append({
                                    "Column": col,
                                    "Source Type": str(df_source[col].dtype),
                                    "Target Type": str(df_target[col].dtype)
                                })

                        if type_errors:

                            st.error("❌ Different column types.")

                            st.dataframe(
                                pd.DataFrame(type_errors),
                                use_container_width=True
                            )

                        else:

                            st.success("✔ Column types validated.")
                            logger.info("Validate column types")


                    # ==========================================================
                    # 5. NUMBER OF ROWS
                    # ==========================================================

                    same_rows = len(df_source) == len(df_target)

                    if same_rows:

                        st.success(f"✔ Number of rows validated. Source: {len(df_source)} rows | Target: {len(df_target)} rows")
                        logger.info("Validate number of rows")

                    else:

                        st.error(
                            f"❌ Different number of rows\n\n"
                            f"Source: {len(df_source)}\n"
                            f"Target: {len(df_target)}"
                        )


                    # ==========================================================
                    # RESULT
                    # ==========================================================

                    if (
                        same_num_columns
                        and same_column_names
                        and not type_errors
                        and same_rows
                    ):

                        st.success("✅ Metadata validation completed successfully.")

                        st.session_state["df_source"] = df_source
                        st.session_state["df_target"] = df_target
                        st.session_state.step = 1

                    else:

                        st.warning("Metadata validation finished with inconsistencies.")



                    return True
    except Exception as e:
        st.error(f"Error to upload User Interface: {e}")
        logger.error(f"Error to upload User Interface: {e}")


if __name__ == "__main__":
    interface()