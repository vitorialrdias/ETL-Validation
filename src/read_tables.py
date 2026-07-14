import pandas as pd
import json
from sqlalchemy import text
from config.logging import logger
from config.bd_connection import Database

def carregar_credenciais(arquivo_json):
    with open(arquivo_json, 'r') as f:
        return json.load(f)

def buscar_credencial_por_host(credenciais, host_desejado, ambiente):
    prefixo = f"sql_{ambiente}"
    for nome, config in credenciais.items():
        if nome.startswith(prefixo) and config.get("host") == host_desejado:
            return config
    raise ValueError(f"No credentials found for host '{host_desejado}' in '{prefixo}'.")

def fetch_dataframe(table_info, credenciais):
    """
    Função auxiliar para ler dados de forma otimizada.
    """
    table_name, env, host_suffix = table_info
    
    # Monta o host e busca as credenciais
    base_host = credenciais[f"sql_{env}"]["host"]
    target_host = base_host[:-2] + host_suffix
    cred = buscar_credencial_por_host(credenciais, target_host, env)
    
    # Inicializa a classe Database
    db = Database(
        cred["host"], 
        cred["database"], 
        cred["username"], 
        cred["password"]
    )
    
    query = f"SELECT * FROM {table_name}"
    
    try:
        chunks = pd.read_sql(text(query), db.engine, chunksize=50000)
        df = pd.concat(chunks, ignore_index=True)
        return df
    finally:
        # Garante o fechamento das conexões do pool após a leitura
        db.engine.dispose()

def read_tables(source_table, target_table):
    """
    Read and create dataframes using optimized Database class and fast execution.
    """
    try:
        credenciais = carregar_credenciais('config/credenciais.env')
        
        # Leitura da Source
        df_source = fetch_dataframe(source_table, credenciais)
        logger.info("Success to create SOURCE dataframe!")

        # Leitura da Target
        df_target = fetch_dataframe(target_table, credenciais)
        logger.info("Success to create TARGET dataframe!\n")
        
        return df_source, df_target
    
    except Exception as e:
        logger.error(f"Error to read table: {e}")
        raise