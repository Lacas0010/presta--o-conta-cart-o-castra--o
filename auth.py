"""
=============================================================================
SISTEMA DE FISCALIZAÇÃO E PRESTAÇÃO DE CONTAS - CARTÃO CASTRAÇÃO (SEPAN)
Módulo de Autenticação e Registro: auth.py
=============================================================================
Interface de controle de acesso institucional, segregando perfis de Pessoa
Jurídica (Clínicas) e Pessoa Física (Servidores).
=============================================================================
"""

import streamlit as st
from supabase import Client
from validate_docbr import CPF, CNPJ


def is_validacao_ativa(supabase: Client) -> bool:
    """Consulta no Supabase se a validação rígida de CPF/CNPJ está ativada."""
    try:
        response = (
            supabase.table("configuracoes_sistema")
            .select("valor_booleano")
            .eq("chave", "validar_documentos")
            .execute()
        )
        if response.data and len(response.data) > 0:
            return bool(response.data[0].get("valor_booleano", False))
        return False
    except Exception:
        return False


def render_auth_page(supabase: Client):
    """Renderiza a interface de login e cadastro institucional."""
    col1, col2, col3 = st.columns([1, 1.8, 1])

    with col2:
        st.markdown(
            """
            <div class="sepan-auth-header">
                <h2>Programa Cartão Castração</h2>
                <h5>Secretaria Extraordinária de Proteção Animal - SEPAN</h5>
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.container(border=True):
            tab_login, tab_signup = st.tabs(["Login", "Criar Conta"])

            with tab_login:
                _render_login_tab(supabase)

            with tab_signup:
                _render_signup_tab(supabase)

        st.markdown(
            """
            <div class="sepan-auth-footer">
                Prefeitura Municipal &bull; Sistema de Fiscalização e Prestação de Contas
            </div>
            """,
            unsafe_allow_html=True,
        )


def _render_login_tab(supabase: Client):
    """Formulário de acesso com e-mail e senha."""
    with st.form(key="form_login"):
        email = st.text_input("E-mail:", placeholder="usuario@dominio.com")
        password = st.text_input("Senha:", type="password", placeholder="••••••••")
        submit_login = st.form_submit_button("Entrar", width="stretch", type="primary")

        if submit_login:
            if not email.strip() or not password:
                st.warning("Preencha o e-mail e a senha.")
            else:
                with st.spinner("Autenticando..."):
                    try:
                        response = supabase.auth.sign_in_with_password({
                            "email": email.strip(),
                            "password": password
                        })

                        if response.user:
                            st.session_state.user = response.user
                            metadata = response.user.user_metadata or {}
                            st.session_state.role = metadata.get("role")
                            st.session_state.cnpj = metadata.get("cnpj")
                            st.rerun()
                        else:
                            st.error("Não foi possível obter a sessão do usuário.")
                    except Exception as e:
                        st.error(f"Falha na autenticação: {str(e)}")


def _render_signup_tab(supabase: Client):
    """Formulário de criação de conta com segregação por tipo de perfil."""
    tipo_perfil = st.radio(
        "Modalidade de Cadastro:",
        options=["Pessoa Jurídica (Clínica Credenciada)", "Pessoa Física (Servidor SEPAN)"],
        horizontal=True
    )

    is_pj = tipo_perfil.startswith("Pessoa Jurídica")

    if not is_pj:
        st.caption(
            "Nota: O cadastro de servidores municipais é criado inicialmente em modo restrito (Leitor) "
            "e requer homologação pela administração para acesso à Comissão de Gestão."
        )

    with st.form(key="form_signup"):
        email = st.text_input("E-mail Institucional / Profissional:", placeholder="email@dominio.com")
        password = st.text_input("Senha de Acesso:", type="password", placeholder="Mínimo 6 caracteres")

        if is_pj:
            col_a, col_b = st.columns(2)
            with col_a:
                cnpj = st.text_input("CNPJ *:", placeholder="00.000.000/0000-00")
                nome_empresarial = st.text_input("Nome Empresarial (Razão Social) *:", placeholder="Clínica Veterinária Exemplo LTDA")
                endereco_clinica = st.text_input("Endereço Completo da Clínica *:", placeholder="Logradouro, número, complemento, bairro, cidade/UF")
                nome_representante = st.text_input("Nome do Representante Legal *:", placeholder="Nome completo do responsável legal")
            with col_b:
                nome_fantasia = st.text_input("Nome Fantasia (Nome da Clínica):", placeholder="Hospital Veterinário Exemplo")
                telefone_clinica = st.text_input("Telefone de Contato *:", placeholder="(00) 00000-0000")
                cpf_representante = st.text_input("CPF do Representante Legal *:", placeholder="000.000.000-00")
        else:
            col_a, col_b = st.columns(2)
            with col_a:
                cpf = st.text_input("CPF *:", placeholder="000.000.000-00")
            with col_b:
                nome_completo = st.text_input("Nome Completo *:", placeholder="Nome do servidor")

        submit_signup = st.form_submit_button("Cadastrar", width="stretch", type="primary")

        if submit_signup:
            if not email.strip() or not password:
                st.error("Preencha o e-mail e a senha.")
                return

            if len(password) < 6:
                st.error("A senha deve conter no mínimo 6 caracteres.")
                return

            if is_pj:
                campos_obrigatorios = [
                    ("CNPJ", cnpj),
                    ("Nome Empresarial", nome_empresarial),
                    ("Endereço Completo", endereco_clinica),
                    ("Telefone de Contato", telefone_clinica),
                    ("Nome do Representante Legal", nome_representante),
                    ("CPF do Representante Legal", cpf_representante)
                ]
                faltantes = [nome for nome, val in campos_obrigatorios if not val.strip()]
                if faltantes:
                    st.error(f"Preencha todos os campos obrigatórios da clínica: {', '.join(faltantes)}. Os dados preenchidos foram preservados.")
                    return

                # Validação matemática rigorosa do CNPJ e CPF do representante se ativada nas configurações
                if is_validacao_ativa(supabase):
                    if not CNPJ().validate(cnpj.strip()):
                        st.error("⚠️ **CNPJ da clínica inválido!** Verifique os 14 dígitos informados. Os demais dados preenchidos foram preservados.")
                        return
                    if not CPF().validate(cpf_representante.strip()):
                        st.error("⚠️ **CPF do Representante Legal inválido!** Verifique os 11 dígitos informados. Os demais dados preenchidos foram preservados.")
                        return

                nome_clinica_final = nome_fantasia.strip() if nome_fantasia.strip() else nome_empresarial.strip()

                user_metadata = {
                    "role": "clinica",
                    "tipo_pessoa": "PJ",
                    "cnpj": cnpj.strip(),
                    "nome_empresarial": nome_empresarial.strip(),
                    "razao_social": nome_empresarial.strip(),
                    "nome_fantasia": nome_clinica_final,
                    "nome_clinica": nome_clinica_final,
                    "name": nome_empresarial.strip(),
                    "endereco_clinica": endereco_clinica.strip(),
                    "telefone_clinica": telefone_clinica.strip(),
                    "email_clinica": email.strip(),
                    "nome_representante": nome_representante.strip(),
                    "cpf_representante": cpf_representante.strip()
                }
            else:
                if not cpf.strip() or not nome_completo.strip():
                    st.error("Preencha o CPF e o Nome Completo. Os dados preenchidos foram preservados.")
                    return

                # Validação matemática rigorosa do CPF se ativada nas configurações
                if is_validacao_ativa(supabase):
                    if not CPF().validate(cpf.strip()):
                        st.error("⚠️ **CPF do Servidor inválido!** Verifique os 11 dígitos informados. Os demais dados preenchidos foram preservados.")
                        return

                user_metadata = {
                    "role": "leitor",
                    "tipo_pessoa": "PF",
                    "cpf": cpf.strip(),
                    "nome": nome_completo.strip(),
                    "name": nome_completo.strip()
                }

            with st.spinner("Registrando usuário..."):
                try:
                    response = supabase.auth.sign_up({
                        "email": email.strip(),
                        "password": password,
                        "options": {"data": user_metadata}
                    })

                    if response.user:
                        if is_pj:
                            st.success("Cadastro realizado com sucesso. Realize o login na aba correspondente.")
                        else:
                            st.success(
                                "Cadastro realizado. Seu usuário foi registrado como Leitor "
                                "e aguarda homologação pela administração da SEPAN."
                            )
                    else:
                        st.error("Não foi possível concluir o cadastro.")
                except Exception as ex:
                    st.error(f"Falha ao registrar: {str(ex)}")


def handle_guardrails(user):
    """Bloqueia o acesso de usuários com perfil restrito 'leitor'."""
    metadata = getattr(user, "user_metadata", {}) or {}
    role = metadata.get("role", "leitor")

    if role == "leitor":
        with st.sidebar:
            st.markdown("### Usuário")
            user_display = metadata.get("nome") or metadata.get("name") or user.email
            st.write(f"**Nome:** {user_display}")
            st.caption(f"{user.email}")
            st.markdown("**Perfil:** `Leitor (Pendente de Liberação)`")
            st.divider()
            if st.button("Sair", width="stretch"):
                st.session_state.user = None
                st.session_state.role = None
                st.rerun()

        st.markdown("### Acesso em Processo de Liberação")
        st.warning(
            f"O usuário **{metadata.get('nome', user.email)}** está cadastrado, "
            "mas seu perfil de acesso ainda não foi homologado pela Comissão de Gestão."
        )
        st.info(
            "Entre em contato com o Administrador do Sistema para habilitar suas permissões."
        )
        st.stop()


def logout_user(supabase: Client):
    """Encerra a sessão ativa do usuário."""
    try:
        supabase.auth.sign_out()
    except Exception:
        pass
    st.session_state.user = None
    st.session_state.role = None
    st.session_state.cnpj = None
    st.rerun()
