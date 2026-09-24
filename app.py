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
from auth import (
    render_auth_page,
    handle_guardrails,
    logout_user,
    render_change_password_widget,
    check_and_render_recovery_flow,
)
from modulo_clinica import render_modulo_clinica
from modulo_comissao import render_modulo_comissao


# -----------------------------------------------------------------------------
# Configuração da Página e Design System
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="SEPAN - Cartão Castração",
    layout="wide",
    initial_sidebar_state="expanded",
)


def inject_custom_css():
    """Injeta estilos CSS modernos e institucionais para o sistema SEPAN, com suporte total a Light e Dark Mode."""
    st.markdown(
        """
        <style>
        /* Import da Fonte Inter */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

        html, body, [class*="css"], .stMarkdown, .stText {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }

        /* =====================================================================
           KEYFRAMES E ANIMAÇÕES SUAVES
           ===================================================================== */
        @keyframes sepanFadeInUp {
            from {
                opacity: 0;
                transform: translateY(8px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        @keyframes sepanScaleIn {
            from {
                opacity: 0;
                transform: scale(0.98);
            }
            to {
                opacity: 1;
                transform: scale(1);
            }
        }

        @keyframes sepanPulseSubtle {
            0%, 100% {
                box-shadow: 0 0 0 0 rgba(59, 130, 246, 0.25);
            }
            50% {
                box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.08);
            }
        }

        /* Aplicação de Animação de Entrada */
        [data-testid="stAppViewContainer"] .main .block-container {
            animation: sepanFadeInUp 0.3s cubic-bezier(0.16, 1, 0.3, 1) forwards;
        }
        [data-testid="stTabs"] [data-baseweb="tab-panel"] {
            animation: sepanFadeInUp 0.24s cubic-bezier(0.16, 1, 0.3, 1) forwards;
        }

        /* =====================================================================
           CARTÕES DE MÉTRICAS (stMetric) TOTALMENTE ADAPTATIVOS
           ===================================================================== */
        [data-testid="stMetric"] {
            background-color: rgba(128, 128, 128, 0.08) !important;
            border: 1px solid rgba(128, 128, 128, 0.22) !important;
            border-radius: 8px !important;
            padding: 14px 18px !important;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04) !important;
            transition: transform 0.22s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.22s cubic-bezier(0.16, 1, 0.3, 1), border-color 0.22s ease !important;
            animation: sepanFadeInUp 0.28s cubic-bezier(0.16, 1, 0.3, 1) forwards;
        }
        [data-testid="stMetric"]:hover {
            transform: translateY(-3px) !important;
            border-color: #3b82f6 !important;
            box-shadow: 0 6px 16px rgba(0, 0, 0, 0.12) !important;
        }
        [data-testid="stMetricLabel"] {
            font-size: 0.85rem !important;
            font-weight: 600 !important;
            opacity: 0.82 !important;
        }
        [data-testid="stMetricValue"] {
            font-size: 1.55rem !important;
            font-weight: 700 !important;
        }

        /* =====================================================================
           BOTÕES COM FEEDBACK TÁTIL & HOVER
           ===================================================================== */
        [data-testid="stButton"] button {
            transition: all 0.18s cubic-bezier(0.16, 1, 0.3, 1) !important;
            border-radius: 6px !important;
            font-weight: 600 !important;
        }
        [data-testid="stButton"] button:hover {
            transform: translateY(-1px) !important;
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.12) !important;
        }
        [data-testid="stButton"] button:active {
            transform: translateY(1px) !important;
            box-shadow: 0 1px 2px rgba(0, 0, 0, 0.08) !important;
        }

        /* =====================================================================
           CONTAINERS COM BORDA
           ===================================================================== */
        [data-testid="stVerticalBlockBorderWrapper"] {
            border-radius: 8px !important;
            border: 1px solid rgba(128, 128, 128, 0.2) !important;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03);
            transition: border-color 0.2s ease, box-shadow 0.2s ease;
            animation: sepanFadeInUp 0.26s cubic-bezier(0.16, 1, 0.3, 1) forwards;
        }
        [data-testid="stVerticalBlockBorderWrapper"]:hover {
            border-color: rgba(128, 128, 128, 0.35) !important;
        }

        /* =====================================================================
           ABAS DE NAVEGAÇÃO (stTabs)
           ===================================================================== */
        [data-testid="stTabs"] [data-baseweb="tab-list"] {
            gap: 6px;
            border-bottom: 2px solid rgba(128, 128, 128, 0.2);
            padding-bottom: 2px;
        }
        [data-testid="stTabs"] [data-baseweb="tab"] {
            font-weight: 600;
            font-size: 0.95rem;
            padding: 8px 16px;
            border-radius: 6px 6px 0 0;
            transition: all 0.2s ease;
        }
        [data-testid="stTabs"] [data-baseweb="tab"]:hover {
            background-color: rgba(128, 128, 128, 0.1);
        }
        [data-testid="stTabs"] [aria-selected="true"] {
            color: #3b82f6 !important;
            border-bottom: 3px solid #3b82f6 !important;
        }

        /* =====================================================================
           BADGES DE STATUS INSTITUCIONAIS COM HOVER
           ===================================================================== */
        .sepan-badge {
            display: inline-block;
            padding: 3px 11px;
            font-size: 0.78rem;
            font-weight: 600;
            border-radius: 12px;
            letter-spacing: 0.3px;
            white-space: nowrap;
            transition: transform 0.18s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.18s ease;
        }
        .sepan-badge:hover {
            transform: scale(1.04);
        }
        .badge-green {
            background-color: rgba(34, 197, 94, 0.18) !important;
            color: #16a34a !important;
            border: 1px solid rgba(34, 197, 94, 0.45) !important;
        }
        .badge-amber {
            background-color: rgba(245, 158, 11, 0.18) !important;
            color: #d97706 !important;
            border: 1px solid rgba(245, 158, 11, 0.45) !important;
            animation: sepanPulseSubtle 3.5s infinite ease-in-out;
        }
        .badge-blue {
            background-color: rgba(59, 130, 246, 0.18) !important;
            color: #2563eb !important;
            border: 1px solid rgba(59, 130, 246, 0.45) !important;
        }
        .badge-red {
            background-color: rgba(239, 68, 68, 0.18) !important;
            color: #dc2626 !important;
            border: 1px solid rgba(239, 68, 68, 0.45) !important;
        }
        .badge-slate {
            background-color: rgba(148, 163, 184, 0.18) !important;
            color: #64748b !important;
            border: 1px solid rgba(148, 163, 184, 0.45) !important;
        }

        /* =====================================================================
           CARTÃO DE CABEÇALHO INSTITUCIONAL
           ===================================================================== */
        .sepan-header-card {
            background: linear-gradient(135deg, #1e3a8a 0%, #1e40af 100%) !important;
            border: 1px solid rgba(255, 255, 255, 0.15) !important;
            border-radius: 10px;
            padding: 20px 26px;
            margin-bottom: 20px;
            box-shadow: 0 4px 14px rgba(0, 0, 0, 0.1);
            animation: sepanScaleIn 0.3s cubic-bezier(0.16, 1, 0.3, 1) forwards;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
            color: #ffffff !important;
        }
        .sepan-header-card:hover {
            transform: translateY(-1px);
            box-shadow: 0 6px 20px rgba(0, 0, 0, 0.15);
        }
        .sepan-header-card h2, .sepan-header-card h3 {
            color: #ffffff !important;
            margin: 0 0 4px 0 !important;
            font-weight: 700;
        }
        .sepan-header-card p {
            color: #e0e7ff !important;
            margin: 0 !important;
            font-size: 0.9rem;
        }
        .sepan-header-card strong {
            color: #ffffff !important;
        }
        .sepan-header-card code {
            background: rgba(255, 255, 255, 0.18) !important;
            color: #ffffff !important;
            border: 1px solid rgba(255, 255, 255, 0.3) !important;
            padding: 2px 7px !important;
            border-radius: 4px !important;
            font-family: monospace !important;
            font-weight: 600 !important;
        }

        /* =====================================================================
           BANNER DE ETAPAS & AVISOS
           ===================================================================== */
        .sepan-step-banner {
            background-color: rgba(59, 130, 246, 0.08) !important;
            border-left: 4px solid #3b82f6 !important;
            border-top: 1px solid rgba(128, 128, 128, 0.2) !important;
            border-right: 1px solid rgba(128, 128, 128, 0.2) !important;
            border-bottom: 1px solid rgba(128, 128, 128, 0.2) !important;
            padding: 14px 18px;
            border-radius: 6px;
            margin-bottom: 18px;
            animation: sepanFadeInUp 0.28s cubic-bezier(0.16, 1, 0.3, 1) forwards;
        }
        .sepan-step-banner .step-title {
            font-weight: 700;
            color: #3b82f6 !important;
            font-size: 0.95rem;
        }
        .sepan-step-banner .step-desc {
            font-size: 0.85rem;
            opacity: 0.88;
            margin-top: 4px;
        }

        /* Banner de Estado Vazio */
        .sepan-empty-banner {
            background-color: rgba(128, 128, 128, 0.06) !important;
            border: 1px dashed rgba(128, 128, 128, 0.28) !important;
            border-radius: 8px;
            padding: 24px;
            text-align: center;
            margin-top: 15px;
            animation: sepanFadeInUp 0.28s cubic-bezier(0.16, 1, 0.3, 1) forwards;
        }
        .sepan-empty-banner .empty-title {
            font-weight: 700;
            color: #3b82f6 !important;
            font-size: 1.05rem;
        }
        .sepan-empty-banner .empty-desc {
            font-size: 0.85rem;
            opacity: 0.82;
            margin-top: 4px;
        }

        /* Alerts e Notificações com Animação */
        [data-testid="stAlert"] {
            animation: sepanFadeInUp 0.24s cubic-bezier(0.16, 1, 0.3, 1) forwards;
            border-radius: 6px !important;
        }

        /* Dataframe / Tabelas com Animação */
        [data-testid="stDataFrame"] {
            animation: sepanFadeInUp 0.26s cubic-bezier(0.16, 1, 0.3, 1) forwards;
            border-radius: 6px;
        }

        /* Identificação na Barra Lateral */
        .sepan-sidebar-brand {
            padding: 6px 0 2px 0;
            animation: sepanFadeInUp 0.3s cubic-bezier(0.16, 1, 0.3, 1) forwards;
        }
        .sepan-sidebar-brand .brand-title {
            font-size: 1.35rem;
            font-weight: 800;
            color: #3b82f6 !important;
            letter-spacing: -0.5px;
        }
        .sepan-sidebar-brand .brand-subtitle {
            font-size: 0.82rem;
            opacity: 0.8;
            font-weight: 600;
        }

        /* Auth Header & Footer */
        .sepan-auth-header {
            text-align: center;
            margin-bottom: 20px;
            animation: sepanScaleIn 0.3s cubic-bezier(0.16, 1, 0.3, 1) forwards;
        }
        .sepan-auth-header h2 {
            color: var(--sepan-primary) !important;
            margin-bottom: 4px;
            font-weight: 700;
        }
        .sepan-auth-header h5 {
            color: var(--sepan-subtext) !important;
            font-weight: normal;
            margin-top: 0;
        }
        .sepan-auth-footer {
            text-align: center;
            color: var(--sepan-subtext);
            font-size: 0.8rem;
            margin-top: 15px;
        }

        /* Títulos h4 e h5 em qualquer tema */
        h4 {
            font-weight: 600 !important;
            color: var(--text-color, inherit) !important;
            margin-top: 10px !important;
            margin-bottom: 12px !important;
        }
        h5 {
            font-weight: 600 !important;
            font-size: 0.98rem !important;
            color: var(--text-color, inherit) !important;
            margin-top: 8px !important;
            margin-bottom: 8px !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
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
            "A gestão, homologação de permissões e redefinição administrativa de senhas de usuários "
            "podem ser realizadas através do módulo administrativo isolado (gestao_usuarios.py)."
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
        st.markdown(
            """
            <div class="sepan-sidebar-brand">
                <div class="brand-title">SEPAN</div>
                <div class="brand-subtitle">Programa Cartão Castração</div>
            </div>
            """,
            unsafe_allow_html=True
        )
        st.divider()

        metadata = user.user_metadata or {}
        user_name = metadata.get("nome_fantasia") or metadata.get("nome") or metadata.get("razao_social") or metadata.get("name") or user.email.split("@")[0]
        cnpj_val = metadata.get("cnpj")

        st.markdown(f"**{user_name}**")
        st.caption(f"{user.email}")
        if cnpj_val:
            st.markdown(f"<p style='margin: 4px 0 10px 0; font-size: 0.82rem;'>CNPJ: <span style='font-family: monospace; font-weight: 600; padding: 2px 6px; background: rgba(128,128,128,0.18); border-radius: 4px;'>{cnpj_val}</span></p>", unsafe_allow_html=True)
        else:
            st.markdown("<div style='margin-bottom: 8px;'></div>", unsafe_allow_html=True)

        role_badges = {
            "clinica": ("Clínica Credenciada", "badge-blue"),
            "comissao": ("Comissão de Gestão", "badge-green"),
            "admin": ("Administrador Geral", "badge-amber"),
            "leitor": ("Leitor / Pendente", "badge-slate"),
        }
        label, badge_class = role_badges.get(role, ("Não definido", "badge-slate"))
        st.markdown(f"<span class='sepan-badge {badge_class}'>{label}</span>", unsafe_allow_html=True)

        st.divider()

        render_change_password_widget(supabase)

        st.divider()

        if st.button("Encerrar Sessão", width="stretch", type="secondary"):
            logout_user(supabase)


# -----------------------------------------------------------------------------
# Fluxo Principal
# -----------------------------------------------------------------------------
def main():
    inject_custom_css()

    # Intercepta se o usuário acessou o sistema via link de recuperação de senha por e-mail
    if check_and_render_recovery_flow(supabase):
        return

    if not st.session_state.user:
        render_auth_page(supabase)
        return

    user = st.session_state.user
    handle_guardrails(user, supabase)

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
