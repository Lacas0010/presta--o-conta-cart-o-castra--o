# Sistema de Fiscalização e Prestação de Contas - Programa Cartão Castração
**Governo do Distrito Federal (GDF)**  
**Secretaria Extraordinária de Proteção Animal (SEPAN)**

---

## Visão Geral

O **Sistema de Fiscalização e Prestação de Contas do Programa Cartão Castração** é uma plataforma institucional de gestão e conformidade pública desenvolvida em Python e Streamlit, integrada ao Supabase (PostgreSQL, Autenticação e Row Level Security - RLS).

O sistema estrutura todo o ciclo de prestação de contas entre as **Clínicas Veterinárias Credenciadas** e a **Comissão de Gestão e Fiscalização da SEPAN**, garantindo rastreabilidade, integridade documental, auditoria em tempo real e integração direta com os processos eletrônicos do **SEI-GDF**.

---

## Estrutura e Módulos do Sistema

```
├── app.py                 # Ponto de entrada, injeção de Design System (Light/Dark) e roteamento de perfis
├── auth.py                # Autenticação institucional, cadastro PJ/PF e guardrails de acesso
├── modulo_clinica.py      # Portal da Clínica (Lançamentos, Fechamento, Histórico e Auditoria Própria)
├── modulo_comissao.py     # Painel de Fiscalização (Fila de Lotes, Deliberação de Retificações, Pareceres e Logs)
├── auditoria.py           # Trilha de auditoria e gravação padronizada de eventos de rastreabilidade
├── gerador_pdf.py         # Motor de geração de PDFs oficiais (Anexo V, Pareceres SEPAN e Texto SEI)
├── gestao_usuarios.py     # Backoffice administrativo para homologação e gestão de roles
├── schema.sql             # Definição do banco de dados (Tabelas, RLS, Políticas, Logs e Índices)
├── requirements.txt       # Dependências organizadas do projeto Python
├── .gitignore             # Regras de exclusão para versionamento Git seguro
└── .streamlit/
    └── secrets.toml       # Credenciais de acesso ao Supabase (URL e chaves de API)
```

---

## Perfis de Acesso (*Roles*)

| Perfil | Identificador | Descrição das Permissões |
| :--- | :--- | :--- |
| **Clínica Credenciada** | `clinica` | Registro individual de procedimentos, alteração direta e saneamento de atendimentos, fechamento de lotes mensais, solicitação de retificação, estorno e auditoria restrita aos seus atendimentos. |
| **Comissão de Gestão** | `comissao` | Fila de fiscalização de lotes, deliberação de retificações (aceite/recusa fundamentada), emissão de pareceres em 10 itens com teto de CRIA, geração de PDF e texto SEI nato-digital, auditoria geral e consulta de logs. |
| **Administrador** | `admin` | Controle de configurações globais do sistema (toggle de validação de CPF/CNPJ), homologação de usuários e acesso irrestrito. |
| **Leitor / Pendente** | `leitor` | Cadastro inicial de servidores em processo de liberação de permissões pela administração da SEPAN. |

---

## Principais Funcionalidades

### 1. Portal da Clínica Credenciada
- **Registro Individual de Atendimentos**: Lançamento com separação visual em 3 blocos (Tutor, Animal e NF-e), validação matemática opcional de CPF e registro de intercorrência cirúrgica / óbito (`Sim` / `Não`).
- **Fechamento de Lote Mensal**:
  - Guia operacional em 3 etapas e grid com 5 métricas consolidadas (Total, Cães, Gatos, Óbitos e Valor Total).
  - **Edição Direta**: Alteração de qualquer campo do atendimento aberto diretamente no painel sem necessidade de exclusão e relançamento.
  - **Relato de Óbitos Automatizado**: Pré-preenchimento automático da narrativa com microchips e tutores dos animais com óbito registrado no período, mantendo campo aberto para notas clínicas adicionais.
  - **Declaração Formal de Responsabilidade Legal**.
- **Histórico de Lotes & Retificação**:
  - Acompanhamento com badges coloridos de status.
  - Download do Relatório Oficial Anexo V em PDF.
  - **Fluxo de Retificação**: Solicitação formal de retificação de lotes já enviados à SEPAN com justificativa.
  - **Estorno Seguro**: Desvinculação dos atendimentos para correções na aba de fechamento após autorização da comissão.
- **Auditoria de Atendimentos da Clínica**: Pesquisa avançada multi-critério restrita aos atendimentos do estabelecimento com exportação em CSV.

---

### 2. Painel da Comissão de Gestão (Servidores SEPAN)
- **Dashboard de Topo**: Indicadores em tempo real (Lotes Pendentes, Homologados, Retificações Solicitadas e Valor em Análise).
- **Fila de Fiscalização de Lotes**:
  - Seleção limpa com estado vazio orientativo (`index=None`).
  - **Deliberação de Retificações**: Painel para Aceitar (libera estorno para a clínica) ou Recusar o pedido de retificação (com fundamentação formal exibida para a clínica).
  - **Parecer Técnico em 10 Itens**:
    - `Item 5`: Monitoramento no CRIA com trava de segurança impedindo quantidade superior ao total do lote.
    - `Itens 6 e 7`: Pontos de Atenção e Notas Pendentes de envio.
    - `Item 8`: Análise de Conformidade dos serviços e valores.
    - `Item 9`: Determinações e Providências adotadas.
    - `Item 10`: Decisão Final (`Aprovada`, `Aprovada com Ressalvas`, `Apta com Necessidade de Saneamento`, `Não Aprovada`).
- **Geração de Documentos Oficiais (SEI-GDF)**:
  - **Aba PDF**: Download do Relatório Técnico Oficial de Fiscalização.
  - **Aba Texto SEI (Nato-Digital)**: Texto estruturado para cópia e colagem direta no editor de documentos do SEI, viabilizando a assinatura eletrônica dos fiscais no processo, com botão de homologação e bloqueio de integridade.
- **Auditoria Geral de Atendimentos**: Busca global com filtros por clínica, período, tutor, animal, microchip, NF-e e status, com métricas e exportação CSV.
- **Histórico de Auditoria (Logs)**: Linha do tempo cronológica de rastreabilidade de todas as ações e alterações no sistema.

---

### 3. Design System & Acessibilidade Visual
- **Tipografia Moderna**: Fonte `Inter` (Google Fonts) em toda a aplicação.
- **Suporte Total a Light Mode e Dark Mode**: Ajuste automático de contrastes, variáveis CSS dinâmicas, fundos adaptáveis e badges de status luminosos no tema escuro.

---

## Pré-requisitos e Instalação

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

Acesse o **SQL Editor** no painel do Supabase e execute o conteúdo do arquivo [`schema.sql`](schema.sql) para criar as tabelas (`configuracoes_sistema`, `lotes_prestacao`, `relacao_transacoes`, `logs_auditoria`), políticas de segurança (RLS), triggers e índices.

---

## Execução da Aplicação

Para iniciar o portal principal:

```bash
streamlit run app.py
```

Para executar o painel de backoffice de gestão de usuários (requer `SUPABASE_SERVICE_ROLE_KEY`):

```bash
streamlit run gestao_usuarios.py
```

---

## Segurança e Conformidade Pública

- **Row Level Security (RLS)** ativo em todas as tabelas do banco de dados.
- **Trilha de Auditoria Imutável**: Gravação de eventos de criação, edição, exclusão, estorno, deliberação de retificação e homologação de pareceres.
- **Validação Rigorosa de Documentos**: Validação de CPF e CNPJ via `validate-docbr`.
- **Compatibilidade SEI-GDF**: Documentos nato-digitais estruturados para assinatura eletrônica direta no processo administrativo.

