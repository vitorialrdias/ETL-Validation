# Agent GCP

Este projeto valida tabelas em diferentes ambientes. O Intuito é receber a mesma tabela e o processo compara quantidade de colunas, quantidade de linhas, tipos das colunas e alguns dados para saber se há ou não inconsistências durante migrações, criações ou alterações nas tabelas

O sistema conta com uma arquitetura modular, testes unitários automatizados e uma interface amigável para o usuário.

---

## 🛠️ INSTRUÇÕES DE EXECUÇÃO

**ATENÇÃO!** Para qualquer execução abaixo, você deve estar dentro da raiz do projeto.


### 1. Para inicializar o ambiente virtual
```bash
python -m venv .venv
```
### 2. Para ativar o ambiente virtual
```bash
.venv\Scripts\activate
```
### 3. Para baixar as bibliotecas utilizadas no projeto
```bash
pip install -r requirements.txt
```
### 4. Execução pelo StreamLit
Para iniciar a interface StreamLit:
```bash
streamlit run ui_streamlit.py
```

---
## 🚀 Tecnologias Utilizadas
- Python 3.13+: Linguagem base do projeto.

- Pandas: Leitura dos dados no banco de origem e validações.

- Pytest: Framework de testes unitários com Mocks.

- Streamlit: Interface gráfica para interação.

---
## 🧪 Testes Automatizados e Qualidade

O projeto utiliza Testes Unitários com a técnica de Mocking para garantir que a lógica de negócio funcione de forma isolada, sem depender de conexões reais com o bancos de dados externos durante a fase de testes.

```bash
python -m pytest
```
---
## 🔄 Automação CI/CD
O projeto está preparado para fluxos de integração contínua:

GitHub Actions: O arquivo em .github/workflows/python-tests.yml executa os testes automaticamente a cada push ou pull request.

---
## 📁 Estrutura do Projeto
Plaintext

```
\
├── .github/workflows/   Automação de CI (GitHub Actions)
├── src/                 Módulos de lógica, ingestão e interface
├── config/              Módulos de configurações de ambiente e conexões
├── _test.py             Scripts de testes unitários (Pytest)
├── pyproject.toml       Configurações globais e ferramentas
├── requirements.txt     Dependências com versões fixas
├── architecture.drawio  Arquitetura do projeto
└── ui_streamlit.py      Script de entrada via interface gráfica

```

---
*Dúvidas ou sugestões? Entre em contato com o mantenedor do projeto.*
