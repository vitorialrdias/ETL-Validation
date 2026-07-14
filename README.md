# ETL Validation

Essa é uma ferramenta para a validação de integridade de dados entre diferentes ambientes (ex: Pentaho para Python). O projeto compara automaticamente esquemas e dados (linhas, colunas, tipos e valores) para identificar inconsistências decorrentes de migrações ou transformações.

## 🚀 Funcionalidades Principais
- **Validação de Schema:** Comparação estrutural de tabelas (quantidade e tipos de colunas).
- **Validação de Dados:** Contagem de linhas e verificação de amostras para garantir consistência.
- **Arquitetura Modular:** Código desacoplado, facilitando a manutenção e expansão.
- **Interface Amigável:** Painel via Streamlit para execução e visualização de resultados.
- **Qualidade Assegurada:** Cobertura de testes automatizados com `pytest` e `mocks`.
---

## 🛠️ INSTRUÇÕES DE EXECUÇÃO

Certifique-se de estar na **raiz do projeto** antes de prosseguir.

### 1. Preparação do Ambiente
Crie e ative o ambiente virtual para manter as dependências isoladas:

```bash
# Criar o ambiente virtual
python -m venv .venv

# Ativar no Windows (PowerShell/CMD)
.venv\Scripts\activate
```

### 2. Dependencias
Instale as bibliotecas necessárias listadas no requirements.txt:
```bash
pip install -r requirements.txt
```
### 3. Execução via StreamLit
Inicie a aplicação web para rodar as validações:
```bash
streamlit run ui_streamlit.py
```
---
## 🧪 Testes Automatizados e Qualidade

O projeto utiliza Testes Unitários com a técnica de Mocking para garantir que a lógica de negócio funcione de forma isolada, sem depender de conexões reais com o bancos de dados externos durante a fase de testes.

```bash
python -m pytest
```
---
## 📁 Estrutura do Projeto
Plaintext

```
\
├── .github/workflows/    # CI/CD: Automação com GitHub Actions
├── config/               # Gerenciamento de credenciais e logs
├── src/                  # Módulos de lógica central e processamento
├── tests/                # Testes unitários com Pytest
├── ui_streamlit.py       # Ponto de entrada da interface gráfica
├── pyproject.toml        # Configuração do projeto
├── requirements.txt      # Dependências e versões
└── architecture.drawio   # Diagrama de arquitetura
```

---
## 🏗️ Stack Tecnológica
- Python 3.13+: Linguagem base do projeto.
- Pandas: Leitura dos dados no banco de origem e validações.
- Conectividade: SQLAlchemy (Otimizado com fast_executemany)
- Streamlit: Interface gráfica para interação.
- Pytest: Framework de testes unitários com Mocks.

---
## 🔄 CI/CD
O projeto está preparado para fluxos de integração contínua:

GitHub Actions: O arquivo em .github/workflows/python-tests.yml executa os testes automaticamente a cada push ou pull request.


---
*Dúvidas ou sugestões? Entre em contato.*
