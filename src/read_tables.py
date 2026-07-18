from config.logging import logger


def read_tables(reference_table, target_table):
    """
    Read and create dataframes using optimized Database class and fast execution.
    """
    try:
        
        reference_table, db_reference = reference_table
        target_table, db_target = target_table
        
        # Reading Source
        df_source = db_reference.read(reference_table)
        logger.info("Success to create REFERENCE dataframe!")

        # Reading Target
        df_target = db_target.read(target_table)
        logger.info("Success to create TARGET dataframe!\n")
        
        return df_source, df_target
    
    except Exception as e:
        logger.error(f"Error to read table: {e}")
        raise

def found_tables(db_aux, reference_job):
    """
    Search job tables using tb log
    """
    try:
        
        # Reading tables SELECT NOME_TABLE WHERE NOME_JOB =  REFERENCE JOB
        query = f"""
        SELECT DISTINCT
            UPPER(SUBSTRING(NOME_TABELA, CHARINDEX('.', NOME_TABELA) + 1, LEN(NOME_TABELA))) AS NOME_TABELA
        FROM TB_LOG_ATUALIZACAO_TABELAS
        WHERE UPPER(NOME_JOB) LIKE '%{reference_job}%'
        """

        df_job_tables = db_aux.read(query)
        logger.info("Success to create JOB TABLES dataframe!")

        return df_job_tables.orderBy('NOME_TABELA')
    
    except Exception as e:
        logger.error(f"Error to read table: {e}")
        raise
