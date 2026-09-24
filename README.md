# Sistema de Fiscalização e Prestação de Contas - Programa Cartão Castração
**Governo do Distrito Federal (GDF)**  
**Secretaria Extraordinária de Proteção Animal (SEPAN)**

---

## Visão Geral

O **Sistema de Fiscalização e Prestação de Contas do Programa Cartão Castração** é uma plataforma institucional de governança, fiscalização e conformidade pública desenvolvida em Python e Streamlit, com persistência no Supabase (PostgreSQL, Autenticação, Row Level Security - RLS e Trilha de Auditoria).

A plataforma digitaliza e integra integralmente o fluxo de prestação de contas entre as **Clínicas Veterinárias Credenciadas** e a **Comissão de Gestão e Fiscalização da SEPAN**, assegurando rastreabilidade, celeridade na liquidação da despesa pública, validação de conformidade documental e integração direta com os processos eletrônicos do **SEI-GDF**.

---

## Estrutura do Repositório

```
├── .devcontainer/
│   └── devcontainer.json          # Configuração de ambiente de desenvolvimento em contêiner
├── .streamlit/
│   ├── config.toml                # Parâmetros de tema e interface do Streamlit
│   └── secrets.toml               # Credenciais de acesso ao Supabase (ignorado no Git)
├── components/
│   └── url_hash_reader/
│       └── index.html             # Componente leitor assíncrono de tokens para recuperação de senha
├── app.py                         # Ponto de entrada, injeção de Design System (Light/Dark) e roteamento de perfis
├── auth.py                        # Autenticação, cadastro PJ/PF, recuperação e redefinição de senha
├── modulo_clinica.py              # Portal da Clínica (Lançamentos, Fechamento, Histórico e Auditoria Própria)
├── modulo_comissao.py             # Painel da Comissão (Fiscalização, Deliberação, Pareceres e Auditoria Geral)
├── auditoria.py                   # Registro e consulta padronizada da trilha de auditoria
├── gerador_pdf.py                 # Motor de geração de PDFs oficiais (Anexo V, Parecer SEPAN e Texto SEI)
├── gestao_usuarios.py             # Módulo administrativo para homologação de perfis e gestão de acessos
├── schema.sql                     # Script SQL (Tabelas, RLS, Políticas, Triggers, Índices e Configurações)
├── requirements.txt               # Dependências do ecossistema Python
└── .gitignore                     # Diretivas de exclusão para versionamento seguro
```

---

## Perfis de Acesso (*Roles*)

| Perfil | Identificador | Atribuições e Nível de Acesso |
| :--- | :--- | :--- |
| **Clínica Credenciada** | `clinica` | Registro individual de atendimentos, saneamento e edição direta de lançamentos abertos, fechamento de lotes mensais com declaração de responsabilidade, solicitação formal de retificação e auditoria restrita aos seus procedimentos. |
| **Comissão de Gestão** | `comissao` | Fila de fiscalização de lotes, deliberação fundamentada de retificações, emissão de parecer técnico em 10 itens com trava de segurança de monitoramento no CRIA, geração de PDF e texto SEI nato-digital, auditoria geral e consulta a logs de eventos. |
| **Administrador Geral** | `admin` | Gestão de parâmetros operacionais (toggle de validação de CPF/CNPJ), homologação de perfis e acesso irrestrito às visões do sistema. |
| **Leitor / Pendente** | `leitor` | Perfil inicial atribuído a servidores recém-cadastrados, com restrição de acesso até homologação pela administração da SEPAN. |

---

## Funcionalidades do Sistema

### 1. Autenticação e Gestão de Credenciais
- **Acesso Segregado por Modalidade**: Cadastro estruturado para Pessoa Jurídica (Clínicas: CNPJ, Razão Social, Nome Fantasia, Endereço, Representante Legal) e Pessoa Física (Servidores: Nome e CPF).
- **Recuperação de Senha por E-mail**: Fluxo automatizado via Supabase Auth integrado com leitor assíncrono de tokens de acesso no navegador, viabilizando o autoatendimento seguro sem necessidade de infraestrutura SMTP externa.
- **Redefinição de Senha no Painel**: Widget dedicado na barra lateral permitindo a atualização de credenciais por usuários autenticados.
- **Guardrails Institucionais**: Bloqueio de acesso para contas inativas ou pendentes de homologação.

### 2. Portal da Clínica Credenciada
- **Registro Individual de Atendimentos**: Formulário dividido em 3 blocos (Dados do Tutor, Identificação do Animal e Dados Fiscais da NF-e), com seleção de espécies (Canina/Felina), sexos, porte, microchip e registro de intercorrências cirúrgicas ou óbitos.
- **Fechamento de Lote Mensal**:
  - Painel com 5 métricas em tempo real (Total de Procedimentos, Cães, Gatos, Óbitos e Valor Total).
  - Edição direta de qualquer atendimento em aberto diretamente na tabela antes do envio.
  - Pré-preenchimento automatizado da narrativa clínica de óbitos com identificação dos tutores e microchips envolvidos.
  - Termo formal de responsabilidade técnica e jurídica.
- **Histórico de Lotes e Retificações**:
  - Visualização com badges coloridos de status.
  - Emissão do Relatório Oficial Anexo V em PDF.
  - Solicitação formal de retificação com justificativa obrigatória e estorno seguro de atendimentos após anuência da fiscalização.
- **Auditoria Interna da Clínica**: Consulta avançada com filtros múltiplos e exportação em formato CSV.

### 3. Painel da Comissão de Gestão e Fiscalização
- **Dashboard de Topo**: Indicadores consolidados de lotes pendentes, aprovados, retificações aguardando análise e montante financeiro sob fiscalização.
- **Fila de Fiscalização de Lotes**:
  - Seleção orientada com estado neutro inicial.
  - **Deliberação de Retificações**: Aprovação (libera estorno para edição pela clínica) ou Recusa (com fundamentação formal exibida à clínica).
  - **Parecer Técnico Estruturado em 10 Itens**:
    - Item 5: Monitoramento no CRIA com validação matemática impedindo quantidade divergente do total faturado.
    - Itens 6 e 7: Identificação de pontos de atenção e notas fiscais pendentes.
    - Item 8: Análise de conformidade de serviços e valores unitários.
    - Item 9: Determinações e providências adotadas pela equipe técnica.
    - Item 10: Conclusão deliberativa (`Aprovada`, `Aprovada com Ressalvas`, `Apta com Necessidade de Saneamento`, `Não Aprovada`).
- **Geração de Documentos Oficiais (SEI-GDF)**:
  - **Relatório em PDF**: Download do Relatório Técnico Oficial de Fiscalização padronizado.
  - **Texto SEI (Nato-Digital)**: Estrutura textual pronta para inserção direta no editor do SEI-GDF para coleta de assinaturas eletrônicas dos fiscais, com trava de homologação e gravação de metadados.
- **Auditoria Geral e Trilha de Eventos**: Consulta transversal de procedimentos em todas as clínicas cadastradas e linha do tempo de auditoria imutável (`logs_auditoria`).

### 4. Backoffice Administrativo (`gestao_usuarios.py`)
- **Homologação de Contas**: Atribuição e alteração de perfis de acesso (`clinica`, `comissao`, `admin`, `leitor`).
- **Redefinição Administrativa de Senhas**: Atualização de credenciais de usuários diretamente por administradores.
- **Parametrização do Sistema**: Alternância (*toggle*) entre modo de validação rígida de documentos (CPF/CNPJ) e modo flexível para testes.

---

## Tecnologias Empregadas

- **Linguagem**: Python 3.10+
- **Framework Web**: Streamlit (Interface reativa e componentes personalizados)
- **Banco de Dados e Auth**: Supabase (PostgreSQL 15, Row Level Security, Gotrue Auth)
- **Processamento de Dados**: Pandas
- **Geração de Documentos**: FPDF2 (Relatórios em PDF)
- **Validação de Documentos**: validate-docbr
- **Design System**: Vanilla CSS institucional com suporte a temas Claro e Escuro, tipografia Inter e microanimações.

---

## Configuração e Instalação Local

### 1. Clonar o Repositório e Configurar o Ambiente Virtual

```bash
git clone https://github.com/Lacas0010/presta--o-conta-cart-o-castra--o.git
cd presta--o-conta-cart-o-castra--o

# Criação do ambiente virtual
python -m venv .venv

# Ativação no Windows (PowerShell)
.\.venv\Scripts\Activate.ps1

# Ativação no Linux / macOS
source .venv/bin/activate
```

### 2. Instalar Dependências

```bash
pip install -r requirements.txt
```

### 3. Configurar Segredos Institucionais (`secrets.toml`)

Crie o arquivo `.streamlit/secrets.toml` contendo as credenciais do Supabase e a URL da aplicação:

```toml
SUPABASE_URL = "https://seu-projeto.supabase.co"
SUPABASE_KEY = "sua-anon-public-key"
SUPABASE_SERVICE_ROLE_KEY = "sua-service-role-secret-key"
APP_URL = "https://cartao-castracao.streamlit.app"
```

### 4. Configurar o Banco de Dados

Acesse a ferramenta **SQL Editor** no console do Supabase e execute as instruções contidas no arquivo [`schema.sql`](schema.sql) para estruturar as tabelas, políticas de segurança por linha (RLS), funções e gatilhos de auditoria.

---

## Execução da Aplicação

Para iniciar o portal institucional principal:

```bash
streamlit run app.py
```

Para executar o painel de backoffice para homologação e administração de usuários:

```bash
streamlit run gestao_usuarios.py
```

---

## Segurança e Conformidade

- **Row Level Security (RLS)**: Aplicação rigorosa de isolamento de dados por perfil no nível do banco de dados.
- **Trilha de Auditoria**: Registro permanente de eventos críticos (criação, edição, exclusão, envio, deliberação e homologação) com carimbo de data/hora, identificação de usuário e endereço IP.
- **Nato-Digital SEI-GDF**: Estruturação de pareceres técnicos pronta para instrução processual eletrônica formal.
