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
           VARIÁVEIS DE TEMA (LIGHT / DARK AWARE)
           ===================================================================== */
        :root {
            --sepan-primary: #1e40af;
            --sepan-brand: #1e3a8a;
            --sepan-subtext: #475569;
            --sepan-card-bg: var(--secondary-background-color, #f8fafc);
            --sepan-card-border: rgba(128, 128, 128, 0.2);
            --sepan-header-gradient: linear-gradient(135deg, #1e3a8a 0%, #1e40af 100%);
            --sepan-header-text: #ffffff;
            --sepan-header-sub: #e0e7ff;
            
            /* Badges Light */
            --badge-green-bg: #dcfce7;
            --badge-green-text: #166534;
            --badge-green-border: #bbf7d0;
            
            --badge-amber-bg: #fef3c7;
            --badge-amber-text: #92400e;
            --badge-amber-border: #fde68a;
            
            --badge-blue-bg: #e0e7ff;
            --badge-blue-text: #3730a3;
            --badge-blue-border: #c7d2fe;
            
            --badge-red-bg: #fee2e2;
            --badge-red-text: #991b1b;
            --badge-red-border: #fecaca;
            
            --badge-slate-bg: #f1f5f9;
            --badge-slate-text: #475569;
            --badge-slate-border: #e2e8f0;
        }

        @media (prefers-color-scheme: dark) {
            :root {
                --sepan-primary: #60a5fa;
                --sepan-brand: #93c5fd;
                --sepan-subtext: #94a3b8;
                --sepan-card-bg: var(--secondary-background-color, #1e293b);
                --sepan-card-border: rgba(255, 255, 255, 0.12);
                --sepan-header-gradient: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
                --sepan-header-text: #f8fafc;
                --sepan-header-sub: #94a3b8;
                
                /* Badges Dark */
                --badge-green-bg: rgba(34, 197, 94, 0.18);
                --badge-green-text: #4ade80;
                --badge-green-border: rgba(34, 197, 94, 0.35);
                
                --badge-amber-bg: rgba(245, 158, 11, 0.18);
                --badge-amber-text: #fbbf24;
                --badge-amber-border: rgba(245, 158, 11, 0.35);
                
                --badge-blue-bg: rgba(59, 130, 246, 0.18);
                --badge-blue-text: #93c5fd;
                --badge-blue-border: rgba(59, 130, 246, 0.35);
                
                --badge-red-bg: rgba(239, 68, 68, 0.18);
                --badge-red-text: #f87171;
                --badge-red-border: rgba(239, 68, 68, 0.35);
                
                --badge-slate-bg: rgba(148, 163, 184, 0.18);
                --badge-slate-text: #cbd5e1;
                --badge-slate-border: rgba(148, 163, 184, 0.35);
            }
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
           CARTÕES DE MÉTRICAS (stMetric) COM MICRO-ANIMAÇÃO
           ===================================================================== */
        [data-testid="stMetric"] {
            background-color: var(--sepan-card-bg) !important;
            border: 1px solid var(--sepan-card-border) !important;
            border-radius: 8px !important;
            padding: 14px 18px !important;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05) !important;
            transition: transform 0.22s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.22s cubic-bezier(0.16, 1, 0.3, 1), border-color 0.22s ease !important;
            animation: sepanFadeInUp 0.28s cubic-bezier(0.16, 1, 0.3, 1) forwards;
        }
        [data-testid="stMetric"]:hover {
            transform: translateY(-3px) !important;
            border-color: var(--sepan-primary) !important;
            box-shadow: 0 6px 16px rgba(0, 0, 0, 0.1) !important;
        }
        [data-testid="stMetricLabel"] {
            font-size: 0.85rem !important;
            font-weight: 500 !important;
            color: var(--text-color, inherit) !important;
            opacity: 0.85;
            transition: color 0.2s ease;
        }
        [data-testid="stMetricValue"] {
            font-size: 1.55rem !important;
            font-weight: 700 !important;
            color: var(--text-color, inherit) !important;
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
            border: 1px solid var(--sepan-card-border) !important;
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
            border-bottom: 2px solid var(--sepan-card-border);
            padding-bottom: 2px;
        }
        [data-testid="stTabs"] [data-baseweb="tab"] {
            font-weight: 600;
            font-size: 0.95rem;
            padding: 8px 16px;
            border-radius: 6px 6px 0 0;
            transition: all 0.2s ease;
            color: var(--text-color, inherit);
        }
        [data-testid="stTabs"] [data-baseweb="tab"]:hover {
            background-color: var(--sepan-card-bg);
        }
        [data-testid="stTabs"] [aria-selected="true"] {
            color: var(--sepan-primary) !important;
            border-bottom: 3px solid var(--sepan-primary) !important;
        }

        /* =====================================================================
           BADGES DE STATUS INSTITUCIONAIS COM HOVER
           ===================================================================== */
        .sepan-badge {
            display: inline-block;
            padding: 3px 10px;
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
            background-color: var(--badge-green-bg) !important;
            color: var(--badge-green-text) !important;
            border: 1px solid var(--badge-green-border) !important;
        }
        .badge-amber {
            background-color: var(--badge-amber-bg) !important;
            color: var(--badge-amber-text) !important;
            border: 1px solid var(--badge-amber-border) !important;
            animation: sepanPulseSubtle 3.5s infinite ease-in-out;
        }
        .badge-blue {
            background-color: var(--badge-blue-bg) !important;
            color: var(--badge-blue-text) !important;
            border: 1px solid var(--badge-blue-border) !important;
        }
        .badge-red {
            background-color: var(--badge-red-bg) !important;
            color: var(--badge-red-text) !important;
            border: 1px solid var(--badge-red-border) !important;
        }
        .badge-slate {
            background-color: var(--badge-slate-bg) !important;
            color: var(--badge-slate-text) !important;
            border: 1px solid var(--badge-slate-border) !important;
        }

        /* =====================================================================
           CARTÃO DE CABEÇALHO INSTITUCIONAL
           ===================================================================== */
        .sepan-header-card {
            background: var(--sepan-header-gradient) !important;
            border: 1px solid var(--sepan-card-border);
            border-radius: 10px;
            padding: 18px 24px;
            margin-bottom: 20px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
            animation: sepanScaleIn 0.3s cubic-bezier(0.16, 1, 0.3, 1) forwards;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        .sepan-header-card:hover {
            transform: translateY(-1px);
            box-shadow: 0 6px 18px rgba(0, 0, 0, 0.16);
        }
        .sepan-header-card h2, .sepan-header-card h3 {
            color: var(--sepan-header-text) !important;
            margin: 0 0 4px 0 !important;
            font-weight: 700;
        }
        .sepan-header-card p {
            color: var(--sepan-header-sub) !important;
            margin: 0 !important;
            font-size: 0.9rem;
        }

        /* =====================================================================
           BANNER DE ETAPAS & AVISOS
           ===================================================================== */
        .sepan-step-banner {
            background-color: var(--sepan-card-bg) !important;
            border-left: 4px solid var(--sepan-primary) !important;
            border-top: 1px solid var(--sepan-card-border);
            border-right: 1px solid var(--sepan-card-border);
            border-bottom: 1px solid var(--sepan-card-border);
            padding: 12px 16px;
            border-radius: 4px;
            margin-bottom: 18px;
            animation: sepanFadeInUp 0.28s cubic-bezier(0.16, 1, 0.3, 1) forwards;
        }
        .sepan-step-banner .step-title {
            font-weight: 600;
            color: var(--sepan-primary);
            font-size: 0.92rem;
        }
        .sepan-step-banner .step-desc {
            font-size: 0.82rem;
            color: var(--sepan-subtext);
            margin-top: 3px;
        }

        /* Banner de Estado Vazio */
        .sepan-empty-banner {
            background-color: var(--sepan-card-bg);
            border: 1px dashed var(--sepan-card-border);
            border-radius: 8px;
            padding: 24px;
            text-align: center;
            margin-top: 15px;
            animation: sepanFadeInUp 0.28s cubic-bezier(0.16, 1, 0.3, 1) forwards;
        }
        .sepan-empty-banner .empty-title {
            font-weight: 600;
            color: var(--sepan-primary);
            font-size: 1.05rem;
        }
        .sepan-empty-banner .empty-desc {
            font-size: 0.85rem;
            color: var(--sepan-subtext);
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
            padding: 8px 0 4px 0;
            animation: sepanFadeInUp 0.3s cubic-bezier(0.16, 1, 0.3, 1) forwards;
        }
        .sepan-sidebar-brand .brand-title {
            font-size: 1.25rem;
            font-weight: 700;
            color: var(--sepan-primary);
            letter-spacing: -0.5px;
        }
        .sepan-sidebar-brand .brand-subtitle {
            font-size: 0.8rem;
            color: var(--sepan-subtext);
            font-weight: 500;
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
            st.caption(f"CNPJ: `{cnpj_val}`")

        role_badges = {
            "clinica": ("Clínica Credenciada", "badge-blue"),
            "comissao": ("Comissão de Gestão", "badge-green"),
            "admin": ("Administrador Geral", "badge-amber"),
            "leitor": ("Leitor / Pendente", "badge-slate"),
        }
        label, badge_class = role_badges.get(role, ("Não definido", "badge-slate"))
        st.markdown(f"<span class='sepan-badge {badge_class}'>{label}</span>", unsafe_allow_html=True)

        st.divider()

        if st.button("Encerrar Sessão", width="stretch", type="secondary"):
            logout_user(supabase)


# -----------------------------------------------------------------------------
# Fluxo Principal
# -----------------------------------------------------------------------------
def main():
    inject_custom_css()

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
