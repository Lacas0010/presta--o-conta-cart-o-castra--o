"""
=============================================================================
SISTEMA DE FISCALIZAÇÃO E PRESTAÇÃO DE CONTAS - CARTÃO CASTRAÇÃO (SEPAN)
Módulo de Backoffice: gestao_usuarios.py
=============================================================================
Ferramenta de administração para atribuição e gestão dos papéis de acesso
(Roles: 'clinica', 'comissao', 'admin', 'leitor').
=============================================================================
"""

import streamlit as st
import pandas as pd
from supabase import create_client, Client


# -----------------------------------------------------------------------------
# Configuração da Página
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="SEPAN - Gestão de Usuários",
    layout="wide",
)


# -----------------------------------------------------------------------------
# Autenticação por Chave de Serviço
# -----------------------------------------------------------------------------
def get_service_role_key() -> tuple[str, str]:
    """Obtém a URL do Supabase e a SERVICE_ROLE_KEY."""
    supabase_url = st.secrets.get("SUPABASE_URL", "")
    if not supabase_url:
        supabase_url = st.text_input(
            "URL do Projeto Supabase:",
            placeholder="https://seu-projeto.supabase.co"
        )

    service_role_key = st.secrets.get("SUPABASE_SERVICE_ROLE_KEY", "")

    if not service_role_key:
        st.markdown(
            "> **Acesso Restrito ao Backoffice**  \n"
            "> Insira a Chave de Serviço (Service Role Key) para prosseguir:"
        )
        service_role_key = st.text_input(
            "Chave de Serviço (Service Role Key):",
            type="password",
            placeholder="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
        )

    if not supabase_url or not service_role_key:
        st.warning("Forneça a URL do Supabase e a Chave de Serviço para desbloquear a interface.")
        st.stop()

    return supabase_url.strip(), service_role_key.strip()


def init_admin_client(url: str, service_key: str) -> Client:
    """Instancia o cliente Supabase com a Chave de Serviço (Admin)."""
    try:
        return create_client(url, service_key)
    except Exception as e:
        st.error(f"Erro ao inicializar cliente Admin: {str(e)}")
        st.stop()


def fetch_all_users(admin_client: Client):
    """Recupera todos os usuários cadastrados no Supabase Auth."""
    try:
        response = admin_client.auth.admin.list_users()
        if isinstance(response, list):
            users = response
        elif hasattr(response, "users"):
            users = response.users
        else:
            users = list(response)
        return users
    except Exception as e:
        st.error(f"Falha ao listar usuários no Supabase: {str(e)}")
        st.stop()


# -----------------------------------------------------------------------------
# Aplicação Principal
# -----------------------------------------------------------------------------
def main():
    st.markdown("### Gestão de Perfis de Acesso - Backoffice")
    st.caption("Programa Cartão Castração - Secretaria Extraordinária de Proteção Animal (SEPAN)")

    supabase_url, service_role_key = get_service_role_key()
    admin_client = init_admin_client(supabase_url, service_role_key)

    ROLE_OPTIONS = {
        "comissao": "Comissão de Gestão (Análise e fiscalização)",
        "clinica": "Clínica Credenciada (Envio de faturas)",
        "admin": "Administrador (Gestão geral)",
        "leitor": "Leitor / Pendente (Aguardando homologação)",
    }

    users = fetch_all_users(admin_client)

    if not users:
        st.info("Nenhum usuário cadastrado encontrado no Supabase Auth.")
        return

    table_data = []
    users_dict = {}

    for u in users:
        metadata = getattr(u, "user_metadata", {}) or {}
        name = (
            metadata.get("nome")
            or metadata.get("razao_social")
            or metadata.get("name")
            or "Não informado"
        )
        tipo_pessoa = metadata.get("tipo_pessoa", "PF" if "cpf" in metadata else ("PJ" if "cnpj" in metadata else "-"))
        documento = metadata.get("cpf") or metadata.get("cnpj") or "-"
        current_role = metadata.get("role", "Não definido")
        created_at = str(getattr(u, "created_at", ""))[:19]
        last_sign_in = str(getattr(u, "last_sign_in_at", "Nunca acessou"))[:19]

        table_data.append({
            "ID": u.id,
            "E-mail": u.email,
            "Nome / Razão Social": name,
            "Tipo": tipo_pessoa,
            "Documento (CPF/CNPJ)": documento,
            "Role Atual": current_role,
            "Criado em": created_at,
            "Último Acesso": last_sign_in,
        })

        if u.email:
            users_dict[u.email] = u

    leitores_count = sum(1 for item in table_data if item["Role Atual"] == "leitor")
    if leitores_count > 0:
        st.warning(f"Existem {leitores_count} cadastro(s) em estado pendente (Role: Leitor) aguardando homologação.")

    st.markdown(f"#### Usuários Cadastrados ({len(users)})")
    df_users = pd.DataFrame(table_data)
    st.dataframe(
        df_users[["E-mail", "Nome / Razão Social", "Tipo", "Documento (CPF/CNPJ)", "Role Atual", "Criado em", "Último Acesso"]],
        width="stretch",
        hide_index=True,
    )

    st.divider()

    st.markdown("#### Atribuição de Nível de Acesso (Role)")
    user_emails = sorted(list(users_dict.keys()))

    with st.form(key="form_update_role"):
        col_user, col_role = st.columns([1.2, 1])

        with col_user:
            selected_email = st.selectbox(
                "E-mail do Usuário:",
                options=user_emails,
                index=0
            )

        target_user = users_dict[selected_email]
        target_metadata = getattr(target_user, "user_metadata", {}) or {}
        current_user_role = target_metadata.get("role", "")
        
        role_keys = list(ROLE_OPTIONS.keys())
        default_index = role_keys.index(current_user_role) if current_user_role in role_keys else 0

        with col_role:
            selected_role_key = st.selectbox(
                "Novo Nível de Acesso (Role):",
                options=role_keys,
                format_func=lambda k: ROLE_OPTIONS[k],
                index=default_index
            )

        submit_update = st.form_submit_button("Salvar Permissões", width="stretch", type="primary")

        if submit_update:
            with st.spinner("Atualizando permissões no Supabase..."):
                try:
                    existing_metadata = getattr(target_user, "user_metadata", {}) or {}
                    updated_metadata = {**existing_metadata, "role": selected_role_key}

                    admin_client.auth.admin.update_user_by_id(
                        target_user.id,
                        {"user_metadata": updated_metadata}
                    )

                    st.success(f"O usuário {selected_email} foi atualizado para '{ROLE_OPTIONS[selected_role_key]}'.")
                    st.rerun()

                except Exception as ex:
                    st.error(f"Erro ao atualizar permissões: {str(ex)}")


if __name__ == "__main__":
    main()
