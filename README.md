# Sistema de Fiscalização e Prestação de Contas - Programa Cartão Castração
**Governo do Distrito Federal (GDF)**  
**Secretaria Extraordinária de Proteção Animal (SEPAN)**

---

## 📋 Visão Geral

O **Sistema de Fiscalização e Prestação de Contas do Programa Cartão Castração** é uma plataforma institucional desenvolvida em Python e Streamlit, integrada ao Supabase (PostgreSQL, Autenticação e Row Level Security - RLS).

O sistema organiza o fluxo operacional entre as **Clínicas Veterinárias Credenciadas** e a **Comissão de Gestão e Fiscalização da SEPAN**, permitindo:
- O registro individual e auditável de procedimentos cirúrgicos executados (castração e microchipagem).
- O fechamento e envio formal de prestações de contas mensais em lotes.
- A geração automatizada de relatórios em PDF em conformidade com as normas oficiais da SEPAN e padrões do processo eletrônico (SEI).
- A fiscalização técnica detalhada, controle de conformidade cadastral (CRIA), cruzamento com notas fiscais e emissão de pareceres conclusivos.

---

## 🏛️ Estrutura e Módulos do Sistema

```
├── app.py                 # Ponto de entrada da aplicação, roteamento por perfil e painel admin
├── auth.py                # Módulo de login, criação de contas (PJ e PF) e guardrails de acesso
├── modulo_clinica.py      # Portal da Clínica (Lançamentos, Fechamento de Lote e Histórico)
├── modulo_comissao.py     # Painel de Fiscalização (Fila de Lotes, Pareceres e Auditoria Geral)
├── gerador_pdf.py         # Motor de geração de PDFs oficiais com fpdf2 (Anexo V e Parecer SEPAN)
├── gestao_usuarios.py     # Backoffice administrativo para gestão de permissões e roles
├── schema.sql             # Definição do banco de dados (Tabelas, RLS, Políticas e Índices)
├── requirements.txt       # Dependências do projeto Python
├── .gitignore             # Regras de exclusão para versionamento Git
└── .streamlit/
    └── secrets.toml       # Credenciais de acesso ao Supabase (URL e chaves de API)
```

---

## 👥 Perfis de Acesso (*Roles*)

| Perfil | Identificador | Descrição das Permissões |
| :--- | :--- | :--- |
| **Clínica Credenciada** | `clinica` | Lançamento de atendimentos individuais, consolidação de faturamento mensal (Lotes), saneamento de pendências e emissão do Relatório Mensal em PDF. |
| **Comissão de Gestão** | `comissao` | Análise técnica dos lotes recebidos, avaliação de conformidade (Itens 5 a 9), homologação com emissão de parecer para o SEI e auditoria de toda a base. |
| **Administrador** | `admin` | Controle de configurações globais (toggle de validação estrita de CPF/CNPJ) e visualização de todos os módulos. |
| **Leitor / Pendente** | `leitor` | Cadastro inicial de servidores em processo de liberação de permissões pela administração. |

---

## 📄 Documentos Oficiais em PDF Gerados

1. **Relatório Mensal de Prestação de Contas (Clínica)**:
   - Identificação cadastral completa: Nome Empresarial, Nome Fantasia, Endereço, CNPJ, Responsável, Telefones e E-mail de cadastro.
   - Resumo sintético dos procedimentos por espécie, sexo, porte e microchips implantados.
   - Relação detalhada de transações com controle por data, CPF do beneficiário, animal, valor e número de NF-e.
   - Declaração formal de responsabilidade legal com assinatura.

2. **Relatório de Prestação de Contas e Fiscalização (Comissão SEPAN / SEI)**:
   - Identificação com número de Processo SEI, fiscal responsável e período analisado.
   - Resumo executivo com indicadores do CRIA e identificação de não conformidades.
   - Apuração da movimentação financeira e varredura do intervalo de numeração de notas fiscais.
   - Seções analíticas individualizadas:
     - `5- MONITORAMENTO DOS CADASTROS NO CRIA`
     - `6- PONTOS DE ATENÇÃO`
     - `7- NOTAS PENDENTES`
     - `8- ANÁLISE DE CONFORMIDADE`
     - `9- DETERMINAÇÕES E PROVIDÊNCIAS`
   - Seção 10 com a decisão formal da Comissão (`Aprovada`, `Aprovada com Ressalvas`, `Apta com Necessidade de Saneamento`, `Não Aprovada`), fundamentação técnica e assinatura.

---

## ⚙️ Pré-requisitos e Instalação

### 1. Clonar o Repositório e Criar o Ambiente Virtual

```bash
# Criar o ambiente virtual (Python 3.10+)
python -m venv .venv

# Ativar no Windows (PowerShell)
.\.venv\Scripts\Activate.ps1

# Ativar no Linux / macOS
source .venv/bin/activate
```

### 2. Instalar Dependências

```bash
pip install -r requirements.txt
```

### 3. Configurar Segredos do Supabase

Crie o arquivo `.streamlit/secrets.toml` na raiz do projeto com as credenciais do seu projeto Supabase:

```toml
SUPABASE_URL = "https://seu-projeto.supabase.co"
SUPABASE_KEY = "sua-anon-public-key"
SUPABASE_SERVICE_ROLE_KEY = "sua-service-role-secret-key"
```

### 4. Configurar o Banco de Dados (Supabase)

Acesse o **SQL Editor** no painel do Supabase e execute o conteúdo do arquivo [`schema.sql`](schema.sql) para criar as tabelas (`configuracoes_sistema`, `lotes_prestacao`, `relacao_transacoes`), políticas de segurança (RLS) e índices.

---

## 🚀 Execução da Aplicação

Para iniciar o portal principal:

```bash
streamlit run app.py
```

Para executar o painel de backoffice de gestão de usuários (requer `SUPABASE_SERVICE_ROLE_KEY`):

```bash
streamlit run gestao_usuarios.py
```

---

## 🔒 Segurança e Integridade

- **Row Level Security (RLS)** habilitado em todas as tabelas do Supabase.
- **Validação de Documentos**: Suporte à validação matemática de dígitos verificadores de CPF e CNPJ via `validate-docbr`, com controle de ativação pelo painel administrativo.
- **Tipografia Formal**: Documentos em PDF gerados em conformidade com o padrão institucional do Governo do Distrito Federal.
