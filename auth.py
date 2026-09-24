"""
=============================================================================
SISTEMA DE FISCALIZAÇÃO E PRESTAÇÃO DE CONTAS - CARTÃO CASTRAÇÃO (SEPAN)
Módulo de Autenticação e Registro: auth.py
=============================================================================
Interface de controle de acesso institucional, segregando perfis de Pessoa
Jurídica (Clínicas) e Pessoa Física (Servidores).
=============================================================================
"""

import os
import urllib.parse
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


def get_app_redirect_url() -> str:
    """Retorna a URL base de redirecionamento da aplicação para recuperação."""
    base_url = str(st.secrets.get("APP_URL", "http://localhost:8501")).rstrip("/")
    return base_url


def check_and_render_recovery_flow(supabase: Client) -> bool:
    """
    Verifica se o usuário acessou a aplicação através de um link de recuperação
    de senha do Supabase Auth e renderiza a tela dedicada para definição da nova senha.
    Retorna True se estiver em processo de redefinição, pausando a renderização normal.
    """
    # 1. Se já estiver no estado de redefinição ativo nesta sessão
    if st.session_state.get("is_resetting_password"):
        print("[AUTH DEBUG LOG] -> Sessão de redefinição ativa. Renderizando tela de nova senha.")
        _render_new_password_screen(supabase)
        return True

    query_params = st.query_params

    # Log de diagnóstico no terminal do servidor
    params_dict = dict(query_params)
    print(f"\n[AUTH DEBUG LOG] =========================================")
    print(f"[AUTH DEBUG LOG] Query Params recebidos no Streamlit: {params_dict}")
    print(f"[AUTH DEBUG LOG] is_resetting_password: {st.session_state.get('is_resetting_password')}")
    print(f"[AUTH DEBUG LOG] recovery_user: {st.session_state.get('recovery_user')}")
    print(f"[AUTH DEBUG LOG] =========================================\n")

    # 2. Tratamento de mensagens de erro emitidas pelo Supabase (ex: link expirado)
    error_msg = query_params.get("error_description") or query_params.get("error")
    if error_msg:
        print(f"[AUTH DEBUG LOG] -> Erro identificado nos query params: {error_msg}")
        st.error(f"Erro no link de recuperação do Supabase: {error_msg}")
        st.query_params.clear()
        return False

    # 3. Código PKCE de recuperação oficial (?code=...)
    code = query_params.get("code")
    if code:
        print(f"[AUTH DEBUG LOG] -> Código PKCE detectado: {code[:10]}...")
        with st.spinner("Validando link de recuperação institucional..."):
            try:
                res = supabase.auth.exchange_code_for_session({"auth_code": code})
                if res.user:
                    print(f"[AUTH DEBUG LOG] -> Sessão PKCE autenticada com sucesso para usuário: {res.user.email}")
                    st.session_state.is_resetting_password = True
                    st.session_state.recovery_user = res.user
                    st.query_params.clear()
                    st.rerun()
            except Exception as ex:
                print(f"[AUTH DEBUG LOG] -> Falha no exchange_code_for_session: {str(ex)}")
                st.error(f"O link de recuperação informado é inválido ou já expirou: {str(ex)}")
                st.query_params.clear()
                return False

    # 4. Token de Acesso (?access_token=...&refresh_token=...)
    access_token = query_params.get("access_token")
    if access_token:
        print(f"[AUTH DEBUG LOG] -> Token de acesso detectado: {access_token[:15]}...")
        refresh_token = query_params.get("refresh_token") or ""
        with st.spinner("Validando token de recuperação institucional..."):
            try:
                res = supabase.auth.set_session(access_token, refresh_token)
                if res.user:
                    print(f"[AUTH DEBUG LOG] -> Sessão set_session autenticada com sucesso para: {res.user.email}")
                    st.session_state.is_resetting_password = True
                    st.session_state.recovery_user = res.user
                    st.query_params.clear()
                    st.rerun()
            except Exception as ex:
                print(f"[AUTH DEBUG LOG] -> Falha no set_session: {str(ex)}")
                st.error(f"Não foi possível autenticar o token de recuperação: {str(ex)}")
                st.query_params.clear()
                return False

    # 5. Token ou Token Hash (?token=... ou ?token_hash=...)
    token = query_params.get("token") or query_params.get("token_hash")
    if token:
        print(f"[AUTH DEBUG LOG] -> Token/Token Hash detectado: {token[:15]}...")
        with st.spinner("Validando token de recuperação..."):
            try:
                res = supabase.auth.verify_otp({"token_hash": token, "type": "recovery"})
                if res.user:
                    print(f"[AUTH DEBUG LOG] -> Sessão verify_otp autenticada com sucesso para: {res.user.email}")
                    st.session_state.is_resetting_password = True
                    st.session_state.recovery_user = res.user
                    st.query_params.clear()
                    st.rerun()
            except Exception as ex:
                print(f"[AUTH DEBUG LOG] -> Falha no verify_otp: {str(ex)}")
                st.error(f"Não foi possível validar o token de recuperação: {str(ex)}")
                st.query_params.clear()
                return False

    return False


def _render_new_password_screen(supabase: Client):
    """Renderiza a tela dedicada para definição de nova senha após clicar no link do e-mail."""
    col1, col2, col3 = st.columns([1, 1.8, 1])

    with col2:
        st.markdown(
            """
            <div class="sepan-auth-header">
                <h2>Programa Cartão Castração</h2>
                <h5>Redefinição de Senha Institucional</h5>
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.container(border=True):
            st.markdown("#### Cadastro de Nova Senha")
            st.caption(
                "Acesso validado por meio do link institucional de recuperação. "
                "Defina sua nova credencial de acesso abaixo:"
            )

            with st.form(key="form_new_password_from_email_link"):
                nova_senha = st.text_input("Nova Senha:", type="password", placeholder="Mínimo 6 caracteres")
                confirma_senha = st.text_input("Confirmar Nova Senha:", type="password", placeholder="Repita a nova senha")
                submit_nova_senha = st.form_submit_button("Salvar Nova Senha", width="stretch", type="primary")

                if submit_nova_senha:
                    if not nova_senha or not confirma_senha:
                        st.warning("Preencha a nova senha e a confirmação.")
                    elif len(nova_senha) < 6:
                        st.error("A nova senha deve possuir no mínimo 6 caracteres.")
                    elif nova_senha != confirma_senha:
                        st.error("As senhas informadas não conferem.")
                    else:
                        with st.spinner("Atualizando credencial institucional..."):
                            try:
                                supabase.auth.update_user({"password": nova_senha})
                                try:
                                    supabase.auth.sign_out()
                                except Exception:
                                    pass
                                st.session_state.is_resetting_password = False
                                st.session_state.recovery_user = None
                                st.session_state.user = None
                                st.success("Senha redefinida com sucesso. Prossiga com a autenticação regular.")
                                st.rerun()
                            except Exception as ex:
                                st.error(f"Não foi possível atualizar a senha: {str(ex)}")

            if st.button("Cancelar e Voltar ao Início", width="stretch", type="secondary"):
                try:
                    supabase.auth.sign_out()
                except Exception:
                    pass
                st.session_state.is_resetting_password = False
                st.session_state.recovery_user = None
                st.session_state.user = None
                st.rerun()


def render_auth_page(supabase: Client):
    """Renderiza a interface de login, cadastro e recuperação de senha institucional."""
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
            tab_login, tab_signup, tab_forgot = st.tabs(["Login", "Criar Conta", "Esqueci a Senha"])

            with tab_login:
                _render_login_tab(supabase)

            with tab_signup:
                _render_signup_tab(supabase)

            with tab_forgot:
                _render_forgot_password_tab(supabase)

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


def _render_forgot_password_tab(supabase: Client):
    """Formulário para solicitação de recuperação de senha via e-mail no Supabase Auth."""
    st.markdown("##### Recuperação de Senha")
    st.caption(
        "Informe seu e-mail cadastrado para receber o link oficial de redefinição de senha "
        "enviado pelo Supabase."
    )

    with st.form(key="form_forgot_password"):
        email_recup = st.text_input("E-mail Cadastrado:", placeholder="usuario@dominio.com")
        submit_recup = st.form_submit_button("Enviar E-mail de Recuperação", width="stretch", type="primary")

        if submit_recup:
            if not email_recup.strip():
                st.warning("Por favor, informe seu endereço de e-mail.")
            else:
                with st.spinner("Solicitando recuperação de senha..."):
                    try:
                        redirect_target = get_app_redirect_url()
                        supabase.auth.reset_password_for_email(
                            email_recup.strip(),
                            options={"redirect_to": redirect_target}
                        )
                        st.success(
                            f"Instruções e link de recuperação enviados para **{email_recup.strip()}**! "
                            "Verifique sua caixa de entrada e pasta de spam."
                        )
                    except Exception as ex:
                        st.error(f"Não foi possível enviar o e-mail de recuperação: {str(ex)}")


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
                    st.error(f"Campos obrigatórios não preenchidos: {', '.join(faltantes)}. Os dados informados foram mantidos.")
                    return

                # Validação matemática rigorosa do CNPJ e CPF do representante se ativada nas configurações
                if is_validacao_ativa(supabase):
                    if not CNPJ().validate(cnpj.strip()):
                        st.error("CNPJ da clínica inválido. Verifique os 14 dígitos informados. Os dados informados foram mantidos.")
                        return
                    if not CPF().validate(cpf_representante.strip()):
                        st.error("CPF do Representante Legal inválido. Verifique os 11 dígitos informados. Os dados informados foram mantidos.")
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
                    st.error("Preencha o CPF e o Nome Completo. Os dados informados foram mantidos.")
                    return

                # Validação matemática rigorosa do CPF se ativada nas configurações
                if is_validacao_ativa(supabase):
                    if not CPF().validate(cpf.strip()):
                        st.error("CPF do Servidor inválido. Verifique os 11 dígitos informados. Os dados informados foram mantidos.")
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


def handle_guardrails(user, supabase: Client = None):
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
            if supabase:
                render_change_password_widget(supabase)
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


def render_change_password_widget(supabase: Client):
    """Widget de alteração/redefinição de senha para usuários autenticados via Supabase Auth."""
    with st.expander("Redefinir / Alterar Senha", expanded=False):
        st.caption("Altere sua credencial de acesso ao sistema.")
        with st.form(key="form_change_password_auth"):
            nova_senha = st.text_input("Nova Senha:", type="password", placeholder="Mínimo 6 caracteres")
            confirma_senha = st.text_input("Confirmar Nova Senha:", type="password", placeholder="Repita a nova senha")
            btn_alterar = st.form_submit_button("Atualizar Senha", width="stretch", type="primary")

            if btn_alterar:
                if not nova_senha or not confirma_senha:
                    st.warning("Preencha todos os campos obrigatórios.")
                elif len(nova_senha) < 6:
                    st.error("A nova senha deve possuir no mínimo 6 caracteres.")
                elif nova_senha != confirma_senha:
                    st.error("As senhas informadas não conferem.")
                else:
                    with st.spinner("Atualizando credencial institucional..."):
                        try:
                            supabase.auth.update_user({"password": nova_senha})
                            st.success("Senha atualizada com sucesso.")
                        except Exception as ex:
                            st.error(f"Erro ao redefinir senha: {str(ex)}")


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

