# validator.py
from functools import reduce
from operator import and_
import pandas as pd
from pyspark.sql import functions as F

class Validate:
    def __init__(self, df_reference, df_target, host_ref, host_target):
        self.df_ref_spark = df_reference
        self.df_target_spark = df_target
        
        self.host_ref = host_ref
        self.host_target = host_target
        
        self.count_ref = df_reference.count()
        self.count_target = df_target.count()

        if self.count_ref == 0 or self.count_target == 0:
            raise ValueError("One or both DataFrames are empty.")

    def validate_number_columns(self):
        cols_ref = len(self.df_ref_spark.columns)
        cols_target = len(self.df_target_spark.columns)
        return cols_ref == cols_target, cols_ref, cols_target

    def validate_column_names(self):
        names_ref = set(self.df_ref_spark.columns)
        names_target = set(self.df_target_spark.columns)

        if names_ref == names_target:
            return True, None, names_ref, names_target

        all_cols = sorted(names_ref.union(names_target))

        diff_df = pd.DataFrame({
            "Column": all_cols,
            f"Target host ({self.host_target})": ["✔" if c in names_target else "" for c in all_cols],
            f"Reference host ({self.host_ref})": ["✔" if c in names_ref else "" for c in all_cols],
        })

        return False, diff_df, names_ref, names_target

    def validate_column_types(self):
        types_ref = dict(self.df_ref_spark.dtypes)
        types_target = dict(self.df_target_spark.dtypes)
        
        type_errors = [
            {"Column": col, "Reference": types_ref[col], "Target": types_target[col]}
            for col in self.df_ref_spark.columns
            if col in types_target and types_ref[col] != types_target[col]
        ]
        
        if not type_errors:
            return True, None
        
        return False, pd.DataFrame(type_errors)

    def validate_number_rows(self):
        return self.count_ref == self.count_target

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _detect_id_column(cols):
        lower_map = {c.lower(): c for c in cols}

        if "id" in lower_map:
            return lower_map["id"]

        id_like = [c for c in cols if c.lower().endswith("_id")]
        if len(id_like) == 1:
            return id_like[0]

        return None


    @staticmethod
    def _normalize_value(v):

        if v is None:
            return None

        if isinstance(v, bool):
            return v

        if isinstance(v, int):
            return v

        if isinstance(v, float):
            return round(v, 6)

        if hasattr(v, "isoformat"):
            return v.isoformat()

        if isinstance(v, str):
            return None if v.strip() == "" else v.strip()

        return v


    def _normalize_row(self, row, cols):
        return {
            c: self._normalize_value(row.get(c))
            for c in cols
        }


    # ------------------------------------------------------------------
    # Procura registro correspondente na referência
    # ------------------------------------------------------------------

    def _find_reference(self, target_row, cols, id_col):

        # Caso exista ID
        if id_col:

            rows = (
                self.df_ref_spark
                .filter(F.col(id_col) == target_row[id_col])
                .limit(1)
                .collect()
            )

            if rows:
                return rows[0].asDict()

            return None

        # -------------------------------------------------------
        # Sem ID -> usa chave composta
        # -------------------------------------------------------

        key_columns = [
            c for c in cols
            if self._normalize_value(target_row.get(c)) not in (None, "")
        ]

        if not key_columns:
            return None

        filtro = reduce(
            and_,
            [
                F.col(c) == target_row[c]
                for c in key_columns
            ]
        )

        rows = (
            self.df_ref_spark
            .filter(filtro)
            .limit(1)
            .collect()
        )

        if rows:
            return rows[0].asDict()

        return None


    # ------------------------------------------------------------------
    # Validação
    # ------------------------------------------------------------------

    def validate_data(self):

        self.df_ref_spark = self.df_ref_spark.drop(
            "DT_ATUALIZACAO",
            "DATA_ATUALIZACAO",
            "DT_INCLUSAO",
            "DATA_INCLUSAO"
        )

        self.df_target_spark = self.df_target_spark.drop(
            "DT_ATUALIZACAO",
            "DATA_ATUALIZACAO",
            "DT_INCLUSAO",
            "DATA_INCLUSAO"
        )

        target_rows = self.df_target_spark.limit(10).collect()

        if not target_rows:
            return {
                "status": "empty_sample",
                "message": "No rows found."
            }

        cols = self.df_target_spark.columns

        id_col = self._detect_id_column(cols)

        divergent_target = []
        divergent_reference = []

        for target in target_rows:

            target_dict = target.asDict()

            ref_dict = self._find_reference(
                target_dict,
                cols,
                id_col
            )

            # Não encontrou na referência
            if ref_dict is None:

                divergent_target.append(target_dict)

                divergent_reference.append(
                    {c: None for c in cols}
                )

                continue

            norm_target = self._normalize_row(
                target_dict,
                cols
            )

            norm_ref = self._normalize_row(
                ref_dict,
                cols
            )

            if norm_target != norm_ref:

                divergent_target.append(target_dict)

                divergent_reference.append(ref_dict)

        if not divergent_target:

            return {
                "status": "success",
                "id_col": id_col,
                "sample_df": pd.DataFrame(
                    [r.asDict() for r in target_rows]
                )
            }

        return {

            "status": "divergent",
            "id_col": id_col,
            "count_mismatched": len(divergent_target),
            "diff_target": pd.DataFrame(
                divergent_target,
                columns=cols
            ),
            "diff_reference": pd.DataFrame(
                divergent_reference,
                columns=cols
            ),
            "cols": cols

        }