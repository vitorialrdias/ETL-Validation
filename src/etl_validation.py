import pandas as pd
import streamlit as st 
from config.logging import logger



class Validate:
    def __init__(self, df_reference, df_target):
        self.df_reference = df_reference
        self.df_target = df_target

        try:
            # ==========================================================
            # 1. DATAFRAMES
            # ==========================================================

            if self.df_reference.empty or self.df_target.empty:
                st.error("❌ One or both DataFrames are empty.")
                st.stop()

            st.success("✔ DataFrames loaded successfully.")
            
        except Exception as e:
            logger.info(f"Error: One or both DataFrames are empty. {e}")
            
    def validate_number_columns(self):
        try:


            # ==========================================================
            # 2. NUMBER OF COLUMNS
            # ==========================================================

            same_num_columns = len(self.df_reference.columns) == len(self.df_target.columns)

            if same_num_columns:
                st.success(f"✔ Number of columns validated. Source: {len(self.df_reference.columns)} columns | Target: {len(self.df_target.columns)} columns")
                logger.info("Validate number of columns")
            else:
                st.error(
                    f"❌ Different number of columns\n\n"
                    f"Source: {len(self.df_reference.columns)}\n"
                    f"Target: {len(self.df_target.columns)}"
                )
                
            return same_num_columns

        except Exception as e:
            logger.info(f"Error: Different number of columns. {e}")

    def validate_column_names(self):
        try:
            
            # ==========================================================
            # 3. COLUMN NAMES
            # ==========================================================

            same_column_names = list(self.df_reference.columns) == list(self.df_target.columns)

            if same_column_names:
                st.success("✔ Column names validated.")
                logger.info("Validate column names")

            else:

                st.error("❌ Different column names.")

                reference_cols = set(self.df_reference.columns)
                target_cols = set(self.df_target.columns)

                all_columns = sorted(reference_cols.union(target_cols))

                df_columns = pd.DataFrame({
                    "Column": all_columns,
                    "Source": ["✔" if c in reference_cols else "" for c in all_columns],
                    "Target": ["✔" if c in target_cols else "" for c in all_columns],
                })

                st.dataframe(df_columns, use_container_width=True)
                
            return same_column_names
        except Exception as e:
            logger.info(f"Error: Different column names. {e}")

    
    def validate_column_types(self):
        
        try:
            # ==========================================================
            # 4. COLUMN TYPES
            # ==========================================================

            type_errors = []


            for col in self.df_reference.columns:

                if str(self.df_reference[col].dtype) != str(self.df_target[col].dtype):

                    type_errors.append({
                        "Column": col,
                        "Source Type": str(self.df_reference[col].dtype),
                        "Target Type": str(self.df_target[col].dtype)
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
        
            return type_errors
            
        except Exception as e:
            logger.info(f"Error: Different column types. {e}")


    def validate_number_rows(self):
        
        try:
            
            # ==========================================================
            # 5. NUMBER OF ROWS
            # ==========================================================

            same_rows = len(self.df_reference) == len(self.df_target)

            if same_rows:

                st.success(f"✔ Number of rows validated. Source: {len(self.df_reference)} rows | Target: {len(self.df_target)} rows")
                logger.info("Validate number of rows")

            else:

                st.error(
                    f"❌ Different number of rows\n\n"
                    f"Source: {len(self.df_reference)}\n"
                    f"Target: {len(self.df_target)}"
                )
            
            return same_rows
        except Exception as e:
            logger.info(f"Error: Different number of rows. {e}")

    def validate_data(self):
        try:

            # ==========================================================
            # 5. CHECK DATA
            # ==========================================================


            common_cols = sorted(list(set(self.df_reference.columns) & set(self.df_target.columns)))
            
            def create_hash(df):
                return df[common_cols].fillna("").astype(str).agg("|".join, axis=1)

            reference = self.df_reference[common_cols].copy()
            target = self.df_target[common_cols].copy()
            
            reference["_row_hash"] = create_hash(reference)
            target["_row_hash"] = create_hash(target)

            # Found divergent
            missing_in_target = set(reference["_row_hash"]) - set(target["_row_hash"])
            missing_in_reference = set(target["_row_hash"]) - set(reference["_row_hash"])

            if not missing_in_target and not missing_in_reference:
                st.success("✔ Data sample validated.")
                sample = reference.drop(columns=["_row_hash"]).sample(n=min(4, len(reference)), random_state=42)
                st.subheader("Sample (4 examples)")
                st.dataframe(sample, use_container_width=True)
                return True

            # Show divergents
            st.error("❌ Divergent data found.")
            
            def get_diff_df(df, hash_list):
                return df[df["_row_hash"].isin(hash_list)].drop(columns=["_row_hash"]).sort_values(common_cols).reset_index(drop=True)

            diff_reference = get_diff_df(reference, missing_in_target)
            diff_target = get_diff_df(target, missing_in_reference)

            def show_diff(df_to_show, ref_df, title, is_target=False):
                st.subheader(title)
                
                if df_to_show.empty:
                    st.caption(f"No conflicting records found in {title.split(' ')[0].lower()}.")
                elif len(df_to_show) == len(ref_df):
                    # Define a cor baseada no tipo de tabela
                    # Verde (#22C55E) para referência, Amarelo (#EAB308) para erro no target
                    color = "#22C55E" if not is_target else "#EAB308"
                    
                    def style_row(row):
                        return [f"background-color: {color}33; color: {color}; font-weight: 600;" 
                                if str(val) != str(ref_df.loc[row.name, col]) else "" 
                                for col, val in row.items()]
                    
                    st.dataframe(df_to_show.style.apply(style_row, axis=1), use_container_width=True)
                else:
                    st.caption("⚠ Unable to perform cell-by-cell comparison (different record counts).")
                    st.dataframe(df_to_show, use_container_width=True)

            # Chamada das funções
            show_diff(diff_reference, diff_target, "Source - reference records", is_target=False)
            show_diff(diff_target, diff_reference, "Target - incorrect records", is_target=True)
                        
            return False

        except Exception as e:
            msg = f"Structural validation error: {e}"
            logger.error(msg)
            st.error(msg)
            return False