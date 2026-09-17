"""
=============================================================================
SISTEMA DE FISCALIZAÇÃO E PRESTAÇÃO DE CONTAS - CARTÃO CASTRAÇÃO (SEPAN)
Arquivo Principal: app.py
=============================================================================
Ponto de entrada da aplicação. Integra o módulo de autenticação,
controle de sessão e roteamento por nível de acesso.
=============================================================================
"""

import streamlit as st
from supabase import create_client, Client
from auth import render_auth_page, handle_guardrails, logout_user
from modulo_clinica import render_modulo_clinica
from modulo_comissao import render_modulo_comissao


# -----------------------------------------------------------------------------
# Configuração da Página
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="SEPAN - Cartão Castração",
    layout="wide",
    initial_sidebar_state="expanded",
)


# -----------------------------------------------------------------------------
# Inicialização do Cliente Supabase
# -----------------------------------------------------------------------------
@st.cache_resource
def get_supabase_client() -> Client:
    """Inicializa o cliente Supabase utilizando credenciais institucionais."""
    try:
        supabase_url = st.secrets["SUPABASE_URL"]
        supabase_key = st.secrets["SUPABASE_KEY"]
    except KeyError as e:
        st.error(f"Configuração ausente no secrets.toml: {e}")
        st.stop()

    return create_client(supabase_url, supabase_key)


supabase = get_supabase_client()


# -----------------------------------------------------------------------------
# Inicialização do Estado da Sessão
# -----------------------------------------------------------------------------
if "user" not in st.session_state:
    st.session_state.user = None

if "role" not in st.session_state:
    st.session_state.role = None

if "cnpj" not in st.session_state:
    st.session_state.cnpj = None


# -----------------------------------------------------------------------------
# Visões por Perfil
# -----------------------------------------------------------------------------
def render_clinica_view(user):
    """Módulo operacional para Clínicas Credenciadas."""
    metadata = user.user_metadata or {}
    cnpj = metadata.get("cnpj", "Não informado")
    st.session_state["cnpj"] = cnpj
    render_modulo_clinica(supabase)


def render_comissao_view(user):
    """Módulo de análise para a Comissão de Gestão."""
    render_modulo_comissao(supabase)


def render_admin_view(user):
    """Módulo de administração geral."""
    tab_auditoria, tab_parametros = st.tabs(["Auditoria e Fiscalização", "Administração"])

    with tab_auditoria:
        render_modulo_comissao(supabase)

    with tab_parametros:
        st.markdown("### Administração Geral do Sistema")
        st.caption(f"Usuário: {user.email} | Perfil: Administrador")
        
        st.markdown("#### Configurações do Sistema e Modo de Teste")
        
        # Consulta o status atual da validação no Supabase
        try:
            res_cfg = (
                supabase.table("configuracoes_sistema")
                .select("valor_booleano")
                .eq("chave", "validar_documentos")
                .execute()
            )
            valor_atual = res_cfg.data[0]["valor_booleano"] if res_cfg.data else False
        except Exception:
            valor_atual = False

        toggle_validacao = st.toggle(
            "Habilitar Validação Rígida de CPF/CNPJ",
            value=valor_atual,
            help="Quando desativado, o sistema permite o preenchimento de CPFs/CNPJs fictícios para testes."
        )

        # Se houver alteração no estado do toggle, persiste no Supabase
        if toggle_validacao != valor_atual:
            try:
                supabase.table("configuracoes_sistema").upsert({
                    "chave": "validar_documentos",
                    "valor_booleano": toggle_validacao,
                    "descricao": "Habilita ou desabilita a validação matemática rigorosa de CPF e CNPJ"
                }).execute()
                st.success(f"Configuração atualizada: Validação de documentos {'habilitada' if toggle_validacao else 'desabilitada'}.")
                st.rerun()
            except Exception as ex:
                st.error(f"Erro ao salvar configuração: {str(ex)}")

        st.divider()

        st.info(
            "A gestão e homologação de permissões de usuários deve ser realizada "
            "através do módulo administrativo isolado (gestao_usuarios.py)."
        )


def render_unassigned_role_view(user):
    """Visão para usuários sem perfil definido."""
    st.markdown("### Perfil em Análise")
    st.warning(f"O usuário {user.email} não possui um perfil de acesso atribuído.")
    st.info("Entre em contato com a Comissão de Gestão da SEPAN para liberação do acesso.")


# -----------------------------------------------------------------------------
# Barra Lateral
# -----------------------------------------------------------------------------
def render_sidebar(user, role):
    """Barra lateral institucional com identificação e logout."""
    with st.sidebar:
        st.markdown("### SEPAN")
        st.caption("Programa Cartão Castração")
        st.divider()

        metadata = user.user_metadata or {}
        user_name = metadata.get("nome") or metadata.get("razao_social") or metadata.get("name") or user.email.split("@")[0]

        st.markdown(f"**Usuário:** {user_name}")
        st.caption(f"{user.email}")

        role_labels = {
            "clinica": "Clínica Credenciada",
            "comissao": "Comissão de Gestão",
            "admin": "Administrador",
            "leitor": "Leitor / Pendente",
        }
        role_label = role_labels.get(role, "Não definido")
        st.markdown(f"**Perfil:** `{role_label}`")

        st.divider()

        if st.button("Sair", width="stretch", type="secondary"):
            logout_user(supabase)


# -----------------------------------------------------------------------------
# Fluxo Principal
# -----------------------------------------------------------------------------
def main():
    if not st.session_state.user:
        render_auth_page(supabase)
        return

    user = st.session_state.user
    handle_guardrails(user)

    role = st.session_state.role
    render_sidebar(user, role)

    if role == "clinica":
        render_clinica_view(user)
    elif role == "comissao":
        render_comissao_view(user)
    elif role == "admin":
        render_admin_view(user)
    else:
        render_unassigned_role_view(user)


if __name__ == "__main__":
    main()
