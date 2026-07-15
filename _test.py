import pandas as pd
from unittest.mock import patch, mock_open

# Importe suas funções
from src.read_tables import read_tables
from src.interface import interface



# Simula o retorno do banco para testar se o código sabe lidar com o DF
@patch("builtins.open", new_callable=mock_open, read_data="{}")
@patch("json.load")
@patch("src.read_tables.pd.read_sql")
@patch("src.read_tables.Database") # Precisamos mocar a classe Database também!
def test_read_tables(mock_db, mock_read_sql, mock_json_load, mock_file):
    # 1. Ajustamos o JSON para ter a chave 'sql_dw' que seu código pede
    mock_json_load.return_value = {
        "sql_dw": {
            "host": "10.0.0.53",
            "database": "test_db",
            "username": "admin",
            "password": "password123"
        },
        "sql_dw_52": {
            "host": "10.0.0.52",
            "database": "test_db",
            "username": "admin",
            "password": "password123"
        }
    }

    # 2. Mocar o comportamento do Database para não tentar conectar de verdade
    mock_db_instance = mock_db.return_value
    mock_db_instance.conn_database.return_value = "fake_connection"

    # 3. Configuramos o retorno do Banco fake
    df_fake = pd.DataFrame({"id": [1], "nome": ["Teste"]})
    df_fake = pd.DataFrame({
        "id": [1],
        "nome": ["Teste"]
    })

    mock_read_sql.side_effect = [
        iter([df_fake]),  # primeira chamada
        iter([df_fake])   # segunda chamada
    ]

    # Executamos a função
    source_table = ['REFERENCE_TABLE_TESTE', 'dw', '52']
    target_table = ['TARGET_TABLE_TESTE', 'dw', '53']
    
    df_source, df_target = read_tables(source_table, target_table)

    # Verificações
    assert df_source is not None
    assert df_target is not None
    
    assert not df_source.empty
    assert not df_target.empty
    
    assert df_source.iloc[0]["nome"] == "Teste"
    assert df_target.iloc[0]["nome"] == "Teste"

# 4. Teste da Interface
# Streamlit é testado via integração:
@patch("src.interface.st") # Mock do objeto streamlit
def test_interface_calls(mock_st):
    # Simulamos que os inputs do streamlit retornam valores
    mock_st.text_area.return_value = "SELECT * FROM TABLE"
    mock_st.button.return_value = True
    
    # Aqui testamos se a função roda sem crashar
    # Nota: Testar Streamlit unitariamente é limitado
    try:
        interface()
        success = True
    except Exception:
        success = False
    
    assert success is True