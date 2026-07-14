import pandas as pd
from unittest.mock import patch, mock_open

# Importe suas funções
from src.read_tables import read_origin_table
from src.interface import interface



# Simula o retorno do banco para testar se o código sabe lidar com o DF
@patch("builtins.open", new_callable=mock_open, read_data='{}')
@patch("json.load")
@patch("src.read_origin_table.pd.read_sql")
@patch("src.read_origin_table.Database") # Precisamos mocar a classe Database também!
def test_read_origin_table(mock_db, mock_read_sql, mock_json_load, mock_file):
    # 1. Ajustamos o JSON para ter a chave 'sql_dw' que seu código pede
    mock_json_load.return_value = {
        'sql_dw': {
            'host': 'localhost',
            'database': 'test_db',
            'username': 'admin',
            'password': 'password123'
        }
    }

    # 2. Mocar o comportamento do Database para não tentar conectar de verdade
    mock_db_instance = mock_db.return_value
    mock_db_instance.conn_database.return_value = "fake_connection"

    # 3. Configuramos o retorno do Banco fake
    df_fake = pd.DataFrame({"id": [1], "nome": ["Teste"]})
    mock_read_sql.return_value = df_fake

    # Executamos a função
    query_test = "SELECT * FROM TABELA"
    df = read_origin_table(query_test)

    # Verificações
    assert df is not None
    assert not df.empty
    assert df.iloc[0]["nome"] == "Teste"

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