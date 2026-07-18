import json
import pandas as pd
import streamlit as st
from config.logging import logger
from src.read_tables import read_tables, found_tables
from src.etl_validation import Validate
from config.bd_connection import Database
from typing import Optional, Tuple

# --- Cache de Configurações ---
@st.cache_data
def carregar_credenciais(arquivo_json):
    with open(arquivo_json, 'r') as f:
        return json.load(f)

def buscar_credencial_por_host(credenciais, host_desejado, ambiente):
    prefixo = f"sql_{ambiente}"
    for nome, config in credenciais.items():
        if nome.startswith(prefixo) and config.get("host") == host_desejado:
            return config
    raise ValueError(f"No credentials found for host '{host_desejado}' in '{prefixo}'.")

def fetch_dataframe(env, host_suffix, credenciais):
    """Function to read data in an optimized way using Spark JDBC."""
    base_host = credenciais[f"sql_{env}"]["host"]
    target_host = base_host[:-2] + host_suffix

    logger.info(f"Attempting to connect to host: {host_suffix}")
    
    cred = buscar_credencial_por_host(
        credenciais,
        target_host,
        env
    )

    # Initializes the Database class.
    db = Database(
        cred["host"],
        cred["database"],
        cred["username"],
        cred["password"]
    )
    
    db.get_connection()
    return db

# --- Helpers de Estilização Visual (Boas Práticas de UI) ---
def render_column_names_style(row, names_target, names_ref):
    col = row["Column"]
    if col in names_target and col not in names_ref:
        return ["", "background-color:#FEE2E2; color:#DC2626; font-weight:600;", ""]
    if col in names_ref and col not in names_target:
        return ["", "", "background-color:#DCFCE7; color:#16A34A; font-weight:600;"]
    return ["", "", ""]

def show_data_diff_ui(df_to_show: pd.DataFrame, ref_df: pd.DataFrame, title: str, is_target: bool = False):
    st.markdown(f"###### {title}")
    if df_to_show.empty:
        st.caption("No conflicting records found.")
        return

    if len(df_to_show) == len(ref_df):
        color = "#22C55E" if not is_target else "#EAB308"
        style_str = f"background-color: {color}33; color: {color}; font-weight: 600;"

        def style_row(row):
            return [
                style_str if Validate._normalize_value(val) != Validate._normalize_value(ref_df.loc[row.name, col]) else ""
                for col, val in row.items()
            ]

        st.dataframe(df_to_show.style.apply(style_row, axis=1), width='stretch')
    else:
        st.caption("⚠ Unable to perform cell-by-cell comparison (different record counts).")
        st.dataframe(df_to_show, width='stretch')


# --- Configuração de Página ---
st.set_page_config(page_title="ETL Validation", layout="wide", page_icon="🔍")

# ------------------------------------------------------------------------
# Constantes
# ------------------------------------------------------------------------
 
# Mapeia o prefixo da tabela (antes do primeiro "_") para o servidor padrão.
SERVER_DICT = {"STG": "stg", "DM": "dw", "FT": "dw", "ODS": "ods"}
 
# Hosts disponíveis para seleção (usado tanto para referência quanto alvo).
HOST_OPTIONS = ["52", "53"]
 
# Host fixo usado na consulta auxiliar de tabelas por job.
AUX_TABLES_HOST = "53"
 
SERVER_PLACEHOLDER = "stg, dw, ods"
 
 
# ------------------------------------------------------------------------
# Funções auxiliares (lógica de negócio)
# ------------------------------------------------------------------------
 
def discover_server(table_name: str, server_dict: dict) -> str:
    """Descobre o servidor padrão a partir do prefixo do nome da tabela.
 
    Ex.: 'STG_MRH' -> 'stg' (via server_dict); se o prefixo não estiver
    mapeado, retorna 'dw' como padrão. Se table_name for vazio ou não
    contiver '_', retorna string vazia.
    """
    if table_name and "_" in table_name:
        prefix = table_name.split("_")[0].upper()  # Pega o que vem antes do primeiro '_'
        return server_dict.get(prefix, "dw")  # Retorna o mapeamento ou 'dw' como padrão se não achar
    return ""
 
 
def init_session_state() -> None:
    """Inicializa o session_state para evitar quebras de fluxo e manter
    os valores padrão entre reruns do Streamlit."""
    defaults = {
        "step": 0,
        "reference_job": None,
        "reference_table": "",
        "reference_host": "53",
        "reference_server": "dw",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
 
 
# ------------------------------------------------------------------------
# Blocos de UI (widgets)
# ------------------------------------------------------------------------
 
def render_host_server_inputs(
    col_server, col_host, *, label_prefix: str, auto_server: str, key_suffix: Optional[str] = None
) -> Tuple[str, str]:
    """Renderiza o par de inputs (servidor + host) usado tanto para a
    referência quanto para o alvo, evitando duplicação de código.
 
    `label_prefix` deve ser "Reference" ou "Target".
    `key_suffix`, quando informado, é usado como `key` dos widgets
    (necessário para os campos de referência, que usam session_state).
    """
    server_kwargs = {"key": f"{key_suffix}_server"} if key_suffix else {}
    host_kwargs = {"key": f"{key_suffix}_host"} if key_suffix else {}
 
    server = col_server.text_input(
        f"{label_prefix} server:",
        value=auto_server,
        placeholder=SERVER_PLACEHOLDER,
        **server_kwargs,
    ).lower()
 
    host = col_host.selectbox(
        f"{label_prefix} host:",
        options=HOST_OPTIONS,
        **host_kwargs,
    )
 
    return server, host
 
 
def render_reference_table_input() -> Tuple[str, str, str]:
    """Renderiza o input de tabela de referência + servidor/host,
    reaproveitado nos dois modos (Buscar por Job / Inserir Manualmente).
    """
    reference_table = st.text_input(
        "Reference - expected records:",
        placeholder="DM_MRH",
        key="reference_table",
    ).upper()
 
    auto_ref_server = discover_server(reference_table, SERVER_DICT)
    c1, c2 = st.columns(2)
    reference_server, reference_host = render_host_server_inputs(
        c1,
        c2,
        label_prefix="Reference",
        auto_server=auto_ref_server,
        key_suffix="reference",
    )
 
    return reference_table, reference_server, reference_host
 
 
def render_job_search_mode(credenciais) -> dict:
    """Renderiza o modo 'Buscar por Job': busca tabelas associadas a um
    job e permite selecionar a tabela alvo, além da tabela de referência.
 
    Retorna um dicionário com as variáveis relevantes para o restante do
    fluxo (target_table, target_server, target_host, reference_table,
    reference_server, reference_host), preenchendo com None quando ainda
    não definidas pelo usuário.
    """
    st.markdown("### Job Search & Reference")
 
    result = {
        "target_table": None,
        "target_server": None,
        "target_host": None,
    }
 
    reference_job = st.text_input(
        "Insert job to search tables:",
        placeholder="Conciliacao_Financeira",
        key="job_job",
    ).upper()
 
    if reference_job:
        db_aux = fetch_dataframe("aux_tables", AUX_TABLES_HOST, credenciais)
        df_tables = found_tables(db_aux, reference_job)
        tables = [row["NOME_TABELA"] for row in df_tables.select("NOME_TABELA").collect()]
 
        if tables:
            target_table = st.selectbox(
                "Search tables by job:",
                options=tables,
                key="job_tables",
            )
 
            auto_target_server = discover_server(target_table, SERVER_DICT)
 
            if target_table:
                st.session_state.reference_table = target_table.upper()
 
                c3, c4 = st.columns(2)
                target_server, target_host = render_host_server_inputs(
                    c3,
                    c4,
                    label_prefix="Target",
                    auto_server=auto_target_server,
                )
 
                result["target_table"] = target_table
                result["target_server"] = target_server
                result["target_host"] = target_host
        else:
            st.warning("Nenhuma tabela encontrada para este Job.")
 
    reference_table, reference_server, reference_host = render_reference_table_input()
    result["reference_table"] = reference_table
    result["reference_server"] = reference_server
    result["reference_host"] = reference_host
 
    return result
 
 
def render_manual_mode() -> dict:
    """Renderiza o modo 'Inserir Manualmente': tabela alvo e tabela de
    referência são digitadas diretamente pelo usuário.
 
    Retorna um dicionário com as mesmas chaves de `render_job_search_mode`.
    """
    st.markdown("### Target Configuration")
    target_table = st.text_input(
        "Target - table to validate:",
        placeholder="STG_MRH",
    ).upper()
 
    auto_target_server = discover_server(target_table, SERVER_DICT)
    c3, c4 = st.columns(2)
    target_server, target_host = render_host_server_inputs(
        c3,
        c4,
        label_prefix="Target",
        auto_server=auto_target_server,
    )
 
    st.divider()
 
    if target_table and (
        st.session_state.reference_table == ""
        or st.session_state.reference_table == st.session_state.get("last_target_table", "")
    ):
        st.session_state.reference_table = target_table
 
    st.session_state.last_target_table = target_table
 
    st.markdown("### Reference Configuration")
    reference_table, reference_server, reference_host = render_reference_table_input()
 
    return {
        "target_table": target_table,
        "target_server": target_server,
        "target_host": target_host,
        "reference_table": reference_table,
        "reference_server": reference_server,
        "reference_host": reference_host,
    }
 
 
# ------------------------------------------------------------------------
# Interface principal
# ------------------------------------------------------------------------
 
def interface() -> None:
    """Main interface for ETL validation process."""
 
    credenciais = carregar_credenciais("config/credentials.env")
 
    init_session_state()
 
    st.title("🔍 ETL Validation")
    st.caption("Compare a reference table with a target table to validate data migration.")
    st.write("---")
 
    col1, col2 = st.columns([1, 1.2], gap="large")  # Dando uma leve vantagem de espaço para a coluna de resultados
 
    with col1:
        st.subheader("📋 Configuration")
 
        input_mode = st.radio(
            "Como deseja definir a tabela de referência?",
            options=["Buscar por Job", "Inserir Manualmente"],
            horizontal=True,
        )
 
        st.divider()
 
        # ==================================================================
        # BUSCAR POR JOB / BUSCA MANUAL
        # ==================================================================
        if input_mode == "Buscar por Job":
            config = render_job_search_mode(credenciais)
        else:
            config = render_manual_mode()
 
        target_table = config["target_table"]
        target_server = config["target_server"]
        target_host = config["target_host"]
        reference_table = config["reference_table"]
        reference_server = config["reference_server"]
        reference_host = config["reference_host"]
        st.write("##")
        start_validation = st.button("🚀 Start validation", width='stretch', type="primary")

    with col2:
        st.subheader("📊 Validation Result")
        
        if start_validation:
            if all([reference_table, reference_server, reference_host, target_table, target_server, target_host]):
                
                db_reference = None
                db_target = None
                
                try:
                    # Uso do st.status para envelopar as chamadas pesadas do PySpark/Banco
                    with st.status("Running ETL validation process...", expanded=False) as status_indicator:
                        

                        st.write("🔌 Establishing database connections...")
                        db_target = fetch_dataframe(target_server, target_host, credenciais)
                        db_reference = fetch_dataframe(reference_server, reference_host, credenciais)

                        st.write("📥 Reading dataframes from targets...")
                        df_reference, df_target = read_tables(
                            [reference_table, db_reference], 
                            [target_table, db_target]
                        )

                        st.write("⚙ Initializing validation engine...")
                        logger.info("Initializing validations...")
                        validator = Validate(
                            df_reference,
                            df_target,
                            reference_host,
                            target_host,
                        )
                        
                        st.write("📐 Checking schema metadata and row volumetric...")
                        is_num_cols_valid, cols_ref, cols_target = validator.validate_number_columns()
                        same_column_names, diff_names_df, names_ref, names_target = validator.validate_column_names()
                        is_types_valid, diff_types_df = validator.validate_column_types()
                        is_rows_valid = validator.validate_number_rows()
                        
                        is_metadata_valid = all([is_num_cols_valid, same_column_names, is_types_valid, is_rows_valid])

                        data_validation = None
                        if same_column_names:
                            st.write("🔍 Running granular data discrepancy audit...")
                            data_validation = validator.validate_data()
                        
                        status_indicator.update(label="Analysis completed successfully!", state="complete", expanded=False)

                    # --- Criação de Abas para Organização do Visual ---
                    tab_struct, tab_data = st.tabs(["📋 Structural Checklist", "🔍 Data Audit"])
                    
                    with tab_struct:
                        # 1. Quantidade de Colunas
                        if is_num_cols_valid:
                            st.success(f"✔ Column count validated: {cols_ref}")
                        else:
                            st.error(f"❌ Column count mismatch. Target: {cols_target} | Reference: {cols_ref}")
                        
                        # 2. Nomes das Colunas
                        if same_column_names:
                            st.success("✔ Column names validated.")
                        else:
                            st.error("❌ Different column names found.")
                            if diff_names_df is not None:
                                with st.expander("View Column Name Discrepancies", expanded=True):
                                    st.dataframe(
                                        diff_names_df.style.apply(render_column_names_style, args=(names_target, names_ref), axis=1),
                                        width='stretch'
                                    )
                        
                        # 3. Tipos de Dados
                        if is_types_valid:
                            st.success("✔ Column types validated.")
                        else:
                            st.error("❌ Type mismatch found.")
                            if diff_types_df is not None:
                                with st.expander("View Type Mismatches", expanded=True):
                                    st.dataframe(diff_types_df, width='stretch')
                                
                        # 4. Volumetria de Linhas
                        if is_rows_valid:
                            st.success(f"✔ Row count validated: {validator.count_ref}")
                        else:
                            st.error(f"❌ Row count mismatch. {reference_host}: {validator.count_ref} | {target_host}: {validator.count_target}")

                    with tab_data:
                        # --- Amostragem e Divergência de Células ---
                        if same_column_names and data_validation:
                            
                            if data_validation.get("id_col"):
                                st.info(f"🔑 Using `{data_validation['id_col']}` as the matching key.")
                            else:
                                st.warning("⚠ No ID column found — matching by similarity.")

                            if data_validation["status"] == "success":
                                st.markdown("##### Sample Viewer (4 random examples)")
                                st.dataframe(
                                    data_validation["sample_df"].sample(n=min(4, len(data_validation["sample_df"])), random_state=42),
                                    width='stretch'
                                )
                            elif data_validation["status"] == "divergent":
                                st.error("❌ Divergent data found. "
                                )
                                
                                # Organizando os DataFrames de divergência dentro de sub-expanders limpos
                                with st.expander("Show Mismatched / Unexpected Records", expanded=True):
                                    ##print(data_validation["diff_reference"].head())
                                    show_data_diff_ui(
                                        data_validation["diff_target"], 
                                        data_validation["diff_reference"], 
                                        f"Target host ({target_host})", 
                                        is_target=True
                                    )
                                    st.write("---")
                                    show_data_diff_ui(
                                        data_validation["diff_reference"], 
                                        data_validation["diff_target"], 
                                        f"Reference ({reference_host})", 
                                        is_target=False
                                    )
                                
                        else:
                            st.caption("No data check performed or schema mismatched.")

                    # --- Veredito Final de Sucesso (Fica fixo embaixo dos resultados da Coluna 2) ---
                    st.divider()
                    is_data_success = data_validation and data_validation.get("status") == "success"
                    if is_metadata_valid and is_data_success:
                        st.success("✅ **Validation Completed Successfully!** Metadata and Data match.")
                        st.session_state.step = 1
                    else:
                        st.warning("⚠ **Validation finished with inconsistencies.** Check the details in the tabs above.")

                except Exception as e:
                    logger.error(f"Validation process error: {e}")
                    st.error(f"WARNING! Check the SERVER or TABLE NAME.\n\nValidation process error: {e}")
                    raise ValueError(f"Validation process error: {e}")
                
                finally:
                    if db_target:
                        db_target.dispose()
                    if db_reference:
                        db_reference.dispose()
            else:
                st.error("Please fill in all reference table and target fields before starting.")
        else:
            st.info("💡 Fill in the fields on the left and click **Start validation** to see results here.")

if __name__ == "__main__":
    interface()