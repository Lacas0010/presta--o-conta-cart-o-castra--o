"""
=============================================================================
SISTEMA DE FISCALIZAÇÃO E PRESTAÇÃO DE CONTAS - CARTÃO CASTRAÇÃO (SEPAN)
Módulo da Clínica Credenciada: modulo_clinica.py
=============================================================================
Responsável por:
1. Inserção individual de procedimentos cirúrgicos com validação de CPF.
2. Fechamento mensal de prestação de contas (Lote) e exclusão de itens abertos.
3. Consulta de histórico de lotes e estorno para saneamento de apontamentos.
=============================================================================
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date
import calendar
import re
from supabase import Client
from validate_docbr import CPF
from auth import is_validacao_ativa
from gerador_pdf import gerar_pdf_anexo_v
from auditoria import registrar_log_auditoria


def init_session_state():
    """Inicializa as variáveis de controle da sessão da clínica."""
    if "lista_conferencia" not in st.session_state:
        st.session_state.lista_conferencia = []


def render_modulo_clinica(supabase: Client):
    """Renderiza o portal da clínica credenciada."""
    init_session_state()

    cnpj = st.session_state.get("cnpj")
    if not cnpj and "user" in st.session_state and st.session_state.user:
        metadata = getattr(st.session_state.user, "user_metadata", {}) or {}
        cnpj = metadata.get("cnpj")
        if cnpj:
            st.session_state["cnpj"] = cnpj

    if not cnpj:
        st.error("CNPJ da clínica não identificado na sessão. Realize login novamente.")
        st.stop()

    metadata = getattr(st.session_state.get("user"), "user_metadata", {}) or {}
    nome_empresarial = metadata.get("nome_empresarial") or metadata.get("razao_social") or metadata.get("name") or cnpj
    nome_clinica = metadata.get("nome_fantasia") or metadata.get("nome_clinica") or nome_empresarial

    st.markdown(
        f"""
        <div class="sepan-header-card">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;">
                <div>
                    <h2 style="margin: 0; font-size: 1.45rem; color: #ffffff;">{nome_clinica}</h2>
                    <p style="margin-top: 4px; font-size: 0.88rem; color: #e0e7ff;">
                        Razão Social: <strong style="color: #ffffff;">{nome_empresarial}</strong> &bull; CNPJ: <span style="font-family: monospace; font-weight: 600; padding: 2px 7px; background: rgba(255,255,255,0.18); border: 1px solid rgba(255,255,255,0.3); border-radius: 4px; color: #ffffff;">{cnpj}</span>
                    </p>
                </div>
                <div>
                    <span style="display: inline-block; background: rgba(255,255,255,0.18); color: #ffffff; border: 1px solid rgba(255,255,255,0.35); padding: 4px 12px; border-radius: 12px; font-size: 0.8rem; font-weight: 600; letter-spacing: 0.3px;">
                        Clínica Credenciada &bull; SEPAN
                    </span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    tab_insercao, tab_fechamento, tab_historico, tab_auditoria = st.tabs([
        "Lançamento de Atendimentos",
        "Fechamento de Lote Mensal",
        "Histórico de Lotes",
        "Auditoria de Atendimentos"
    ])

    with tab_insercao:
        _render_tab_insercao(supabase, cnpj, nome_clinica)

    with tab_fechamento:
        _render_tab_fechamento(supabase, cnpj, nome_clinica, nome_empresarial)

    with tab_historico:
        _render_tab_historico(supabase, cnpj)

    with tab_auditoria:
        _render_tab_auditoria_clinica(supabase, cnpj, nome_clinica)


# -----------------------------------------------------------------------------
# ABA 1: Inserção Individual de Atendimentos
# -----------------------------------------------------------------------------
def _render_tab_insercao(supabase: Client, cnpj: str, nome_clinica: str):
    """Lançamento unitário de procedimentos cirúrgicos executados."""
    with st.container(border=True):
        st.markdown("#### Registro Individual de Atendimento")
        st.caption("Preencha as informações do tutor, do animal e do faturamento para registrar a castração.")

        if "msg_sucesso_atendimento" in st.session_state:
            st.success(st.session_state.pop("msg_sucesso_atendimento"))

        form_version = st.session_state.get("form_atendimento_version", 0)
        with st.form(key=f"form_cadastro_atendimento_{form_version}", clear_on_submit=False):
            st.markdown("##### 1. Dados do Beneficiário / Tutor")
            col1, col2, col3 = st.columns([1, 1.2, 1.8])
            with col1:
                data_atendimento = st.date_input(
                    "Data da Castração *",
                    value=date.today(),
                    format="DD/MM/YYYY"
                )
            with col2:
                cpf_beneficiario = st.text_input("CPF do Beneficiário *", placeholder="000.000.000-00", help="Informe os 11 dígitos do CPF do tutor")
            with col3:
                nome_beneficiario = st.text_input("Nome Completo do Beneficiário *", placeholder="Nome completo do tutor")

            st.markdown("##### 2. Identificação do Animal")
            col4, col5, col6, col7, col8 = st.columns([1, 1, 1, 1.2, 1])
            with col4:
                especie = st.selectbox("Espécie *", options=["Canina", "Felina"])
            with col5:
                sexo = st.radio("Sexo *", options=["Macho", "Fêmea"], horizontal=True)
            with col6:
                porte = st.selectbox("Porte *", options=["Pequeno", "Médio", "Grande"])
            with col7:
                numero_microchip = st.text_input("Nº do Microchip *", placeholder="Número do microchip implantado")
            with col8:
                obito_opcao = st.radio("Veio a Óbito? *", options=["Não", "Sim"], index=0, horizontal=True)

            st.markdown("##### 3. Faturamento e Documento Fiscal")
            col9, col10 = st.columns([1, 1])
            with col9:
                valor_transacao = st.number_input(
                    "Valor do Procedimento (R$) *",
                    min_value=0.0,
                    value=0.0,
                    step=10.0,
                    format="%.2f",
                    help="Valor contratual correspondente ao procedimento realizado"
                )
            with col10:
                nfe_referencia = st.text_input("NF-e / Nota Fiscal *", placeholder="Número e série da NF-e")

            st.caption("* Campos de preenchimento obrigatório.")
            submit_atendimento = st.form_submit_button("Gravar Atendimento", width="stretch", type="primary")

            if submit_atendimento:
                erros = []
                if not cpf_beneficiario.strip():
                    erros.append("CPF do Beneficiário")
                if not nome_beneficiario.strip():
                    erros.append("Nome do Beneficiário")
                if not numero_microchip.strip():
                    erros.append("Número do Microchip")
                if valor_transacao <= 0:
                    erros.append("Valor do Procedimento")
                if not nfe_referencia.strip():
                    erros.append("NF-e / Nota Fiscal")

                if erros:
                    st.error(f"Campos obrigatórios não preenchidos: {', '.join(erros)}. Os demais dados preenchidos foram preservados.")
                else:
                    # Validação matemática de CPF se configurada no sistema
                    if is_validacao_ativa(supabase):
                        if not CPF().validate(cpf_beneficiario.strip()):
                            st.error("⚠️ **CPF do Beneficiário inválido!** Verifique os dígitos informados. Os demais dados preenchidos foram preservados.")
                            return

                    veio_a_obito = (obito_opcao == "Sim")
                    dados_transacao = {
                        "data_atendimento": data_atendimento.isoformat(),
                        "cnpj_clinica": cnpj.strip(),
                        "nome_clinica": nome_clinica,
                        "cpf_beneficiario": cpf_beneficiario.strip(),
                        "nome_beneficiario": nome_beneficiario.strip(),
                        "especie": especie,
                        "sexo": sexo,
                        "porte": porte,
                        "numero_microchip": numero_microchip.strip(),
                        "obito": veio_a_obito,
                        "valor_transacao": float(valor_transacao),
                        "nfe_referencia": nfe_referencia.strip(),
                    }

                    with st.spinner("Gravando atendimento..."):
                        try:
                            try:
                                supabase.table("relacao_transacoes").insert(dados_transacao).execute()
                            except Exception as ex_ins:
                                err_s = str(ex_ins)
                                if "PGRST204" in err_s or "Could not find" in err_s or "obito" in err_s:
                                    payload_seguro = {k: v for k, v in dados_transacao.items() if k != "obito"}
                                    supabase.table("relacao_transacoes").insert(payload_seguro).execute()
                                else:
                                    raise ex_ins

                            st.session_state.lista_conferencia.insert(0, dados_transacao)
                            registrar_log_auditoria(
                                supabase, cnpj, nome_clinica,
                                tipo_entidade="atendimento",
                                acao="criacao",
                                descricao=f"Atendimento registrado para {nome_beneficiario.strip()} (Microchip: {numero_microchip.strip()}, Espécie: {especie}, Valor: R$ {float(valor_transacao):.2f})",
                                detalhes=dados_transacao
                            )
                            st.session_state.form_atendimento_version = form_version + 1
                            st.session_state["msg_sucesso_atendimento"] = f"Atendimento de {nome_beneficiario.strip()} gravado com sucesso."
                            st.rerun()
                        except Exception as e:
                            st.error(f"Falha ao registrar atendimento: {str(e)}")

    st.divider()

    total_sessao = len(st.session_state.lista_conferencia)
    col_sess_title, col_sess_badge = st.columns([3, 1])
    with col_sess_title:
        st.markdown(f"#### Atendimentos Gravados nesta Sessão ({total_sessao})")
    with col_sess_badge:
        if total_sessao > 0:
            st.markdown(f"<div style='text-align: right;'><span class='sepan-badge badge-green'>{total_sessao} novos lançamentos</span></div>", unsafe_allow_html=True)

    if st.session_state.lista_conferencia:
        df_conferencia = pd.DataFrame(st.session_state.lista_conferencia)
        if "obito" in df_conferencia.columns:
            df_conferencia["obito_view"] = df_conferencia["obito"].apply(
                lambda o: "Sim" if o is True or str(o).lower() in ["true", "sim", "1"] else "Não"
            )
            colunas_exibicao = {
                "data_atendimento": "Data",
                "nome_beneficiario": "Beneficiário",
                "especie": "Espécie",
                "obito_view": "Óbito",
                "valor_transacao": "Valor (R$)",
                "nfe_referencia": "NF-e",
            }
        else:
            colunas_exibicao = {
                "data_atendimento": "Data",
                "nome_beneficiario": "Beneficiário",
                "especie": "Espécie",
                "valor_transacao": "Valor (R$)",
                "nfe_referencia": "NF-e",
            }
        cols_validas = [c for c in colunas_exibicao.keys() if c in df_conferencia.columns]
        df_view = df_conferencia[cols_validas].copy()
        if "valor_transacao" in df_view.columns:
            df_view["valor_transacao"] = df_view["valor_transacao"].apply(
                lambda v: f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            )
        if "data_atendimento" in df_view.columns:
            df_view["data_atendimento"] = pd.to_datetime(df_view["data_atendimento"]).dt.strftime("%d/%m/%Y")
        df_view = df_view.rename(columns=colunas_exibicao)

        st.dataframe(df_view, width="stretch", hide_index=True)
    else:
        st.info("Nenhum atendimento registrado nesta sessão de trabalho.")


# -----------------------------------------------------------------------------
# ABA 2: Fechamento Mensal de Lote e Exclusão de Itens
# -----------------------------------------------------------------------------
def _render_tab_fechamento(supabase: Client, cnpj: str, nome_clinica: str, nome_empresarial: str = ""):
    """Consolidação mensal, visualização e exclusão de transações abertas."""
    st.markdown("#### Fechamento de Prestação de Contas")
    st.caption("Consolidação dos procedimentos executados no período para envio formal e emissão de parecer da SEPAN.")

    st.markdown(
        """
        <div class="sepan-step-banner">
            <div class="step-title">Fluxo Operacional de Fechamento do Lote</div>
            <div class="step-desc">
                <strong>1. Conferência e Ajustes:</strong> Revise e altere dados se necessário &bull; 
                <strong>2. Declarações e Ocorrências:</strong> Confirme o relatório de intercorrências e óbitos &bull; 
                <strong>3. Consolidação e Envio:</strong> Submeta formalmente para fiscalização da SEPAN
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    hoje = date.today()
    meses_opcoes = []
    for i in range(12):
        ano = hoje.year if hoje.month - i > 0 else hoje.year - 1
        mes = hoje.month - i if hoje.month - i > 0 else 12 + (hoje.month - i)
        nomes_meses = ["", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
                       "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
        rotulo = f"{mes:02d}/{ano} - {nomes_meses[mes]}/{ano}"
        meses_opcoes.append((f"{mes:02d}/{ano}", rotulo, ano, mes))

    col_mes, _ = st.columns([1.5, 2])
    with col_mes:
        escolha_mes = st.selectbox(
            "Mês de Referência:",
            options=meses_opcoes,
            format_func=lambda x: x[1],
            index=0
        )

    mes_codigo, mes_rotulo, ref_ano, ref_mes = escolha_mes
    _, ultimo_dia = calendar.monthrange(ref_ano, ref_mes)
    dt_inicio_mes = f"{ref_ano}-{ref_mes:02d}-01"
    dt_fim_mes = f"{ref_ano}-{ref_mes:02d}-{ultimo_dia:02d}"

    try:
        query_pendentes = (
            supabase.table("relacao_transacoes")
            .select("*")
            .eq("cnpj_clinica", cnpj)
            .gte("data_atendimento", dt_inicio_mes)
            .lte("data_atendimento", dt_fim_mes)
            .is_("lote_id", "null")
            .order("data_atendimento", desc=False)
            .execute()
        )
        transacoes_abertas = query_pendentes.data or []
    except Exception as ex:
        st.error(f"Erro ao consultar atendimentos do período: {str(ex)}")
        transacoes_abertas = []

    total_abertas = len(transacoes_abertas)
    valor_total_aberto = sum(float(t.get("valor_transacao", 0)) for t in transacoes_abertas)
    total_caes = sum(1 for t in transacoes_abertas if str(t.get("especie", "")).strip().capitalize() == "Canina")
    total_gatos = sum(1 for t in transacoes_abertas if str(t.get("especie", "")).strip().capitalize() == "Felina")
    total_obitos = sum(1 for t in transacoes_abertas if t.get("obito") is True or str(t.get("obito", "")).lower() in ["true", "sim", "1"])

    col_r1, col_r2, col_r3, col_r4, col_r5 = st.columns(5)
    with col_r1:
        st.metric("Procedimentos Pendentes", total_abertas)
    with col_r2:
        st.metric("Cães Castrados", total_caes)
    with col_r3:
        st.metric("Gatos Castrados", total_gatos)
    with col_r4:
        st.metric("Óbitos Registrados", total_obitos)
    with col_r5:
        st.metric(
            "Valor Total Acumulado",
            f"R$ {valor_total_aberto:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        )

    if total_abertas == 0:
        st.info(f"Não há atendimentos avulsos pendentes de fechamento para a competência {mes_rotulo}.")
        return

    # Visualização prévia dos atendimentos abertos
    st.divider()
    with st.expander(f"Visualizar os {total_abertas} atendimentos deste período", expanded=True):
        df_preview = pd.DataFrame(transacoes_abertas)
        if "obito" in df_preview.columns:
            df_preview["obito_view"] = df_preview["obito"].apply(
                lambda o: "Sim" if o is True or str(o).lower() in ["true", "sim", "1"] else "Não"
            )
            cols_preview = ["data_atendimento", "nome_beneficiario", "cpf_beneficiario", "especie", "numero_microchip", "obito_view", "valor_transacao", "nfe_referencia"]
            cols_map_preview = {
                "data_atendimento": "Data",
                "nome_beneficiario": "Beneficiário",
                "cpf_beneficiario": "CPF",
                "especie": "Espécie",
                "numero_microchip": "Microchip",
                "obito_view": "Óbito",
                "valor_transacao": "Valor (R$)",
                "nfe_referencia": "NF-e"
            }
        else:
            cols_preview = ["data_atendimento", "nome_beneficiario", "cpf_beneficiario", "especie", "numero_microchip", "valor_transacao", "nfe_referencia"]
            cols_map_preview = {
                "data_atendimento": "Data",
                "nome_beneficiario": "Beneficiário",
                "cpf_beneficiario": "CPF",
                "especie": "Espécie",
                "numero_microchip": "Microchip",
                "valor_transacao": "Valor (R$)",
                "nfe_referencia": "NF-e"
            }
        cols_presentes = [c for c in cols_preview if c in df_preview.columns]
        df_show = df_preview[cols_presentes].copy()
        if "data_atendimento" in df_show.columns:
            df_show["data_atendimento"] = pd.to_datetime(df_show["data_atendimento"]).dt.strftime("%d/%m/%Y")
        if "valor_transacao" in df_show.columns:
            df_show["valor_transacao"] = df_show["valor_transacao"].apply(
                lambda v: f"R$ {float(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            )
        df_show = df_show.rename(columns=cols_map_preview)
        st.dataframe(df_show, width="stretch", hide_index=True)

        # ---------------------------------------------------------------------
        # Funcionalidade de Alteração e Exclusão de Atendimentos Abertos
        # ---------------------------------------------------------------------
        st.markdown("##### Gerenciar e Ajustar Atendimentos do Período")
        st.caption("Caso algum atendimento contenha dados incorretos, altere os campos diretamente ou exclua o registro antes do fechamento:")

        dict_transacoes = {
            f"{t.get('data_atendimento', '')} | {t.get('nome_beneficiario', '')} (CPF: {t.get('cpf_beneficiario', '-')}, Microchip: {t.get('numero_microchip', '-')})": t
            for t in transacoes_abertas
        }
        labels_transacoes = list(dict_transacoes.keys())

        tab_editar_item, tab_excluir_item = st.tabs(["Alterar Dados do Atendimento", "Excluir Atendimento"])

        with tab_editar_item:
            item_edicao_label = st.selectbox(
                "Selecione o atendimento para editar:",
                options=labels_transacoes,
                key=f"sel_edit_{mes_codigo}"
            )

            transacao_selecionada = dict_transacoes[item_edicao_label]
            transacao_id = transacao_selecionada["id"]

            dt_atual = date.today()
            if transacao_selecionada.get("data_atendimento"):
                try:
                    dt_atual = datetime.strptime(str(transacao_selecionada["data_atendimento"])[:10], "%Y-%m-%d").date()
                except Exception:
                    dt_atual = date.today()

            val_esp = transacao_selecionada.get("especie", "Canina")
            idx_esp = 0 if val_esp == "Canina" else 1

            val_sex = transacao_selecionada.get("sexo", "Macho")
            idx_sex = 0 if val_sex == "Macho" else 1

            val_porte = transacao_selecionada.get("porte", "Pequeno")
            idx_porte = ["Pequeno", "Médio", "Grande"].index(val_porte) if val_porte in ["Pequeno", "Médio", "Grande"] else 0

            val_obito = transacao_selecionada.get("obito")
            is_obito_val = (val_obito is True or str(val_obito).lower() in ["true", "sim", "1"])
            idx_obito = 1 if is_obito_val else 0

            with st.form(key=f"form_editar_transacao_{transacao_id}"):
                col_e1, col_e2, col_e3 = st.columns([1, 1.2, 1.8])
                with col_e1:
                    edit_data = st.date_input(
                        "Data da Castração *",
                        value=dt_atual,
                        format="DD/MM/YYYY",
                        key=f"edit_dt_{transacao_id}"
                    )
                with col_e2:
                    edit_cpf = st.text_input(
                        "CPF do Beneficiário *",
                        value=str(transacao_selecionada.get("cpf_beneficiario") or ""),
                        key=f"edit_cpf_{transacao_id}"
                    )
                with col_e3:
                    edit_nome = st.text_input(
                        "Nome do Beneficiário *",
                        value=str(transacao_selecionada.get("nome_beneficiario") or ""),
                        key=f"edit_nome_{transacao_id}"
                    )

                col_e4, col_e5, col_e6, col_e7, col_e8 = st.columns([1, 1, 1, 1.2, 1])
                with col_e4:
                    edit_especie = st.selectbox(
                        "Espécie *",
                        options=["Canina", "Felina"],
                        index=idx_esp,
                        key=f"edit_esp_{transacao_id}"
                    )
                with col_e5:
                    edit_sexo = st.radio(
                        "Sexo *",
                        options=["Macho", "Fêmea"],
                        index=idx_sex,
                        horizontal=True,
                        key=f"edit_sex_{transacao_id}"
                    )
                with col_e6:
                    edit_porte = st.selectbox(
                        "Porte *",
                        options=["Pequeno", "Médio", "Grande"],
                        index=idx_porte,
                        key=f"edit_porte_{transacao_id}"
                    )
                with col_e7:
                    edit_microchip = st.text_input(
                        "Nº do Microchip *",
                        value=str(transacao_selecionada.get("numero_microchip") or ""),
                        key=f"edit_chip_{transacao_id}"
                    )
                with col_e8:
                    edit_obito_opcao = st.radio(
                        "Veio a Óbito? *",
                        options=["Não", "Sim"],
                        index=idx_obito,
                        horizontal=True,
                        key=f"edit_obito_{transacao_id}"
                    )

                col_e9, col_e10 = st.columns([1, 1])
                with col_e9:
                    edit_valor = st.number_input(
                        "Valor do Procedimento (R$) *",
                        min_value=0.0,
                        value=float(transacao_selecionada.get("valor_transacao") or 0.0),
                        step=10.0,
                        format="%.2f",
                        key=f"edit_val_{transacao_id}"
                    )
                with col_e10:
                    edit_nfe = st.text_input(
                        "NF-e / Nota Fiscal *",
                        value=str(transacao_selecionada.get("nfe_referencia") or ""),
                        key=f"edit_nfe_{transacao_id}"
                    )

                submit_edit = st.form_submit_button("Salvar Alterações do Atendimento", width="stretch", type="primary")

                if submit_edit:
                    erros_edit = []
                    if not edit_cpf.strip():
                        erros_edit.append("CPF do Beneficiário")
                    if not edit_nome.strip():
                        erros_edit.append("Nome do Beneficiário")
                    if not edit_microchip.strip():
                        erros_edit.append("Número do Microchip")
                    if edit_valor <= 0:
                        erros_edit.append("Valor do Procedimento")
                    if not edit_nfe.strip():
                        erros_edit.append("NF-e / Nota Fiscal")

                    if erros_edit:
                        st.error(f"Campos obrigatórios não preenchidos: {', '.join(erros_edit)}. As alterações foram mantidas.")
                    else:
                        if is_validacao_ativa(supabase):
                            if not CPF().validate(edit_cpf.strip()):
                                st.error("⚠️ **CPF do Beneficiário inválido!** Verifique os dígitos informados. As alterações foram mantidas.")
                                return

                        dados_editados = {
                            "data_atendimento": edit_data.isoformat(),
                            "cpf_beneficiario": edit_cpf.strip(),
                            "nome_beneficiario": edit_nome.strip(),
                            "especie": edit_especie,
                            "sexo": edit_sexo,
                            "porte": edit_porte,
                            "numero_microchip": edit_microchip.strip(),
                            "obito": (edit_obito_opcao == "Sim"),
                            "valor_transacao": float(edit_valor),
                            "nfe_referencia": edit_nfe.strip(),
                        }

                        with st.spinner("Salvando alterações..."):
                            try:
                                try:
                                    supabase.table("relacao_transacoes").update(dados_editados).eq("id", transacao_id).execute()
                                except Exception as ex_up_item:
                                    err_s = str(ex_up_item)
                                    if "PGRST204" in err_s or "Could not find" in err_s or "obito" in err_s:
                                        payload_seguro = {k: v for k, v in dados_editados.items() if k != "obito"}
                                        supabase.table("relacao_transacoes").update(payload_seguro).eq("id", transacao_id).execute()
                                    else:
                                        raise ex_up_item

                                registrar_log_auditoria(
                                    supabase, cnpj, nome_clinica,
                                    tipo_entidade="atendimento",
                                    acao="alteracao",
                                    descricao=f"Atendimento ID {str(transacao_id)[:8]} alterado (Tutor: {edit_nome.strip()}, Microchip: {edit_microchip.strip()}, Espécie: {edit_especie}, Valor: R$ {float(edit_valor):.2f})",
                                    referencia_id=transacao_id,
                                    detalhes=dados_editados
                                )
                                st.success("Atendimento alterado com sucesso.")
                                st.rerun()
                            except Exception as ex_edit:
                                st.error(f"Erro ao atualizar atendimento: {str(ex_edit)}")

        with tab_excluir_item:
            item_excluir_label = st.selectbox(
                "Selecione o registro para exclusão definitiva:",
                options=labels_transacoes,
                key=f"sel_exc_{mes_codigo}"
            )
            if st.button("Excluir Atendimento Selecionado", key=f"btn_exc_{mes_codigo}", width="stretch", type="secondary"):
                id_para_excluir = dict_transacoes[item_excluir_label]["id"]
                try:
                    supabase.table("relacao_transacoes").delete().eq("id", id_para_excluir).execute()
                    registrar_log_auditoria(
                        supabase, cnpj, nome_clinica,
                        tipo_entidade="atendimento",
                        acao="exclusao",
                        descricao=f"Atendimento ID {str(id_para_excluir)[:8]} ({dict_transacoes[item_excluir_label].get('nome_beneficiario', '')}) excluído do período {mes_codigo}",
                        referencia_id=id_para_excluir
                    )
                    st.success("Registro excluído com sucesso.")
                    st.rerun()
                except Exception as ex:
                    st.error(f"Erro ao excluir registro: {str(ex)}")

    st.divider()

    st.markdown("#### Dados do Fechamento e Representante Legal")

    user_meta = getattr(st.session_state.get("user"), "user_metadata", {}) or {}
    user_email = getattr(st.session_state.get("user"), "email", "")
    def_nome_fantasia = str(user_meta.get("nome_fantasia") or user_meta.get("nome_clinica") or nome_clinica)
    def_endereco = str(user_meta.get("endereco_clinica") or "")
    def_telefone = str(user_meta.get("telefone_clinica") or "")
    def_nome_rep = str(user_meta.get("nome_representante") or "")
    def_cpf_rep = str(user_meta.get("cpf_representante") or "")

    # Análise automática de óbitos para pré-preenchimento do relato
    transacoes_com_obito = [
        t for t in transacoes_abertas
        if t.get("obito") is True or str(t.get("obito", "")).lower() in ["true", "sim", "1"]
    ]

    if transacoes_com_obito:
        st.warning(
            f"Atenção: Foram identificados {len(transacoes_com_obito)} registro(s) de óbito nos atendimentos deste período. "
            "O campo de 'Óbitos e Intercorrências Cirúrgicas' abaixo foi pré-preenchido automaticamente com esses dados para sua revisão."
        )
        linhas_obito = []
        for t in transacoes_com_obito:
            esp = t.get("especie", "Animal")
            sex = t.get("sexo", "")
            chip = t.get("numero_microchip", "Não informado")
            tutor = t.get("nome_beneficiario", "Não informado")
            dt_raw = str(t.get("data_atendimento", ""))
            try:
                dt_fmt = pd.to_datetime(dt_raw).strftime("%d/%m/%Y")
            except Exception:
                dt_fmt = dt_raw[:10]
            linhas_obito.append(f"- O animal ({esp}, {sex}, Microchip nº {chip}), tutor(a) {tutor}, atendido em {dt_fmt}, veio a óbito.")

        texto_padrao_obitos = (
            "Registros de óbito identificados nos atendimentos deste lote:\n"
            + "\n".join(linhas_obito)
            + "\n\nObservações clínicas e intercorrências adicionais:"
        )
    else:
        texto_padrao_obitos = "Sem óbitos ou intercorrências cirúrgicas registradas no período."

    with st.form(key=f"form_lote_{mes_codigo}"):
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            nome_fantasia_form = st.text_input(
                "Nome Fantasia da Clínica:",
                value=def_nome_fantasia,
                placeholder="Hospital Veterinário Exemplo"
            )
            endereco_clinica = st.text_input(
                "Endereço Completo da Clínica *",
                value=def_endereco,
                placeholder="Logradouro, número, complemento, bairro, cidade/UF"
            )
            nome_representante = st.text_input(
                "Nome do Responsável pela Empresa *",
                value=def_nome_rep,
                placeholder="Nome completo do responsável legal"
            )
        with col_c2:
            st.text_input(
                "E-mail para Contato (E-mail de Cadastro):",
                value=user_email,
                disabled=True,
                help="O e-mail para contato utilizado no relatório é o e-mail da conta cadastrada da clínica."
            )
            telefone_clinica = st.text_input(
                "Telefones de Contato *",
                value=def_telefone,
                placeholder="(00) 00000-0000"
            )
            cpf_representante = st.text_input(
                "CPF do Responsável Legal *",
                value=def_cpf_rep,
                placeholder="000.000.000-00"
            )

        st.markdown("##### Relato de Ocorrências")
        obitos_relato = st.text_area(
            "Óbitos e Intercorrências Cirúrgicas:",
            value=texto_padrao_obitos,
            placeholder="Descreva eventuais intercorrências ou confirme o relato...",
            help="Preenchido automaticamente com base nos atendimentos com óbito marcado no lote. O campo permanece editável para você adicionar mais observações."
        )

        reclamacoes_relato = st.text_area(
            "Reclamações de Beneficiários:",
            placeholder="Descreva eventuais queixas de tutores ou informe 'Nenhuma reclamação registrada'."
        )

        declaracao = st.checkbox(
            "Declaro a veracidade das informações prestadas, a efetiva realização dos procedimentos cirúrgicos, "
            "a regular emissão das Notas Fiscais correspondentes e a não cobrança de qualquer valor adicional dos beneficiários.",
            value=False
        )

        submit_lote = st.form_submit_button("Consolidar e Enviar Lote", width="stretch", type="primary")

        if submit_lote:
            if not declaracao:
                st.error("É necessário confirmar a Declaração de Responsabilidade.")
            elif not obitos_relato.strip() or not reclamacoes_relato.strip():
                st.error("Preencha os campos de intercorrências e reclamações.")
            elif not nome_representante.strip() or not cpf_representante.strip():
                st.error("Preencha o Nome e o CPF do Representante Legal.")
            else:
                if is_validacao_ativa(supabase):
                    if not CPF().validate(cpf_representante.strip()):
                        st.error("⚠️ **CPF do Representante Legal inválido!** Verifique os dígitos informados. Os dados preenchidos foram preservados.")
                        return

                with st.spinner("Enviando lote..."):
                    try:
                        dados_lote = {
                            "cnpj_clinica": cnpj,
                            "nome_clinica": nome_fantasia_form.strip() if nome_fantasia_form else nome_clinica,
                            "nome_empresarial": nome_empresarial or nome_clinica,
                            "nome_fantasia": nome_fantasia_form.strip() if nome_fantasia_form else def_nome_fantasia,
                            "endereco_clinica": endereco_clinica.strip(),
                            "telefone_clinica": telefone_clinica.strip(),
                            "email_clinica": user_email.strip(),
                            "nome_representante": nome_representante.strip(),
                            "cpf_representante": cpf_representante.strip(),
                            "mes_referencia": mes_codigo,
                            "total_procedimentos": total_abertas,
                            "valor_total": float(valor_total_aberto),
                            "obitos_relato": obitos_relato.strip(),
                            "reclamacoes_relato": reclamacoes_relato.strip(),
                            "declaracao_responsabilidade": True,
                            "status": "Enviado para Análise"
                        }

                        try:
                            res_lote = supabase.table("lotes_prestacao").insert(dados_lote).execute()
                        except Exception as ex_insert:
                            err_msg = str(ex_insert)
                            if "PGRST204" in err_msg or "Could not find" in err_msg:
                                # Fallback: se alguma coluna recente ainda não foi criada no banco, tenta sem as novas colunas
                                colunas_novas = ["email_clinica", "nome_fantasia", "nome_empresarial"]
                                payload_seguro = {k: v for k, v in dados_lote.items() if k not in colunas_novas}
                                res_lote = supabase.table("lotes_prestacao").insert(payload_seguro).execute()
                            else:
                                raise ex_insert

                        lote_criado = res_lote.data[0] if res_lote.data else None

                        if not lote_criado:
                            st.error("Não foi possível registrar o lote.")
                            return

                        lote_id = lote_criado["id"]
                        ids_transacoes = [t["id"] for t in transacoes_abertas]

                        supabase.table("relacao_transacoes").update({"lote_id": lote_id}).in_("id", ids_transacoes).execute()

                        registrar_log_auditoria(
                            supabase, cnpj, nome_fantasia_form.strip() if nome_fantasia_form else nome_clinica,
                            tipo_entidade="lote",
                            acao="criacao",
                            descricao=f"Prestação de contas ({mes_codigo}) enviada com {total_abertas} atendimentos no valor total de R$ {float(valor_total_aberto):.2f}",
                            referencia_id=lote_id,
                            detalhes=dados_lote
                        )

                        st.success(f"Prestação de contas ({mes_codigo}) enviada com sucesso para a SEPAN (Lote ID: {lote_id[:8]}).")
                        st.rerun()

                    except Exception as ex:
                        st.error(f"Falha ao enviar lote: {str(ex)}")


# -----------------------------------------------------------------------------
# ABA 3: Histórico de Lotes e Estorno para Saneamento
# -----------------------------------------------------------------------------
def _render_tab_historico(supabase: Client, cnpj: str):
    """Consulta de lotes, solicitação de retificação e estorno para saneamento."""
    st.markdown("#### Histórico de Lotes Enviados")

    try:
        res = (
            supabase.table("lotes_prestacao")
            .select("*")
            .eq("cnpj_clinica", cnpj)
            .order("created_at", desc=True)
            .execute()
        )
        lotes = res.data or []
    except Exception as ex:
        st.error(f"Erro ao carregar histórico: {str(ex)}")
        lotes = []

    if not lotes:
        st.info("Nenhuma prestação de contas enviada até o momento.")
        return

    for lote in lotes:
        status = lote.get("status", "Enviado para Análise")
        lote_id = lote.get("id", "")
        mes_ref = lote.get("mes_referencia", "")
        total_proc = lote.get("total_procedimentos", 0)
        valor_tot = float(lote.get("valor_total", 0.0))
        data_envio = str(lote.get("created_at", ""))[:10]
        status_retificacao = lote.get("status_retificacao")
        motivo_retificacao = lote.get("motivo_retificacao")
        motivo_recusa = lote.get("motivo_recusa_retificacao")

        # Mapeamento do status para badge visual
        if status in ["Aprovada", "Homologado"]:
            badge_class = "badge-green"
        elif status in ["Aprovada com Ressalvas", "Apta com Necessidade de Saneamento", "Retificação Aprovada pela SEPAN"]:
            badge_class = "badge-amber"
        elif status in ["Solicitação de Retificação Pendente", "Enviado para Análise"]:
            badge_class = "badge-blue"
        elif status in ["Não Aprovada", "Retificação Recusada pela SEPAN"]:
            badge_class = "badge-red"
        else:
            badge_class = "badge-slate"

        with st.container(border=True):
            col_h1, col_h2, col_h3, col_h4 = st.columns([1.5, 1.2, 1.1, 1.2])
            with col_h1:
                st.markdown(f"**Competência:** `{mes_ref}`")
                st.caption(f"ID: {lote_id[:8]} &bull; Envio: {data_envio}")
            with col_h2:
                st.write(f"Procedimentos: **{total_proc}**")
                st.write(f"Valor Total: **R$ {valor_tot:,.2f}**".replace(",", "X").replace(".", ",").replace("X", "."))
            with col_h3:
                st.markdown(f"<div style='margin-top: 6px;'><span class='sepan-badge {badge_class}'>{status}</span></div>", unsafe_allow_html=True)
            with col_h4:
                # Busca as transações vinculadas ao lote para gerar o PDF
                try:
                    res_t = (
                        supabase.table("relacao_transacoes")
                        .select("*")
                        .eq("lote_id", lote_id)
                        .order("data_atendimento", desc=False)
                        .execute()
                    )
                    transacoes_do_lote = res_t.data or []
                except Exception:
                    transacoes_do_lote = []

                if transacoes_do_lote:
                    try:
                        user_email_sessao = getattr(st.session_state.get("user"), "email", "")
                        user_meta_sessao = getattr(st.session_state.get("user"), "user_metadata", {}) or {}
                        
                        lote_enriquecido = {
                            **lote,
                            "email_clinica": lote.get("email_clinica") or user_meta_sessao.get("email_clinica") or user_email_sessao,
                            "nome_fantasia": lote.get("nome_fantasia") or user_meta_sessao.get("nome_fantasia") or user_meta_sessao.get("nome_clinica") or lote.get("nome_clinica"),
                            "nome_empresarial": lote.get("nome_empresarial") or user_meta_sessao.get("nome_empresarial") or user_meta_sessao.get("razao_social") or lote.get("nome_clinica"),
                            "endereco_clinica": lote.get("endereco_clinica") or user_meta_sessao.get("endereco_clinica"),
                            "telefone_clinica": lote.get("telefone_clinica") or user_meta_sessao.get("telefone_clinica"),
                            "nome_representante": lote.get("nome_representante") or user_meta_sessao.get("nome_representante"),
                            "cpf_representante": lote.get("cpf_representante") or user_meta_sessao.get("cpf_representante"),
                        }
                        
                        pdf_bytes = gerar_pdf_anexo_v(lote_enriquecido, transacoes_do_lote)
                        mes_arquivo = mes_ref.replace("/", "_")
                        st.download_button(
                            label="Baixar Relatório (PDF)",
                            data=pdf_bytes,
                            file_name=f"Relatorio_{mes_arquivo}.pdf",
                            mime="application/pdf",
                            key=f"pdf_{lote_id}",
                            width="stretch",
                            type="secondary"
                        )
                    except Exception as err_pdf:
                        st.caption(f"Erro no PDF: {str(err_pdf)}")
                else:
                    st.caption("Sem transações vinculadas.")

            # Parecer técnico da comissão SEPAN (se emitido e não substituído por status de retificação pendente)
            parecer = lote.get("parecer_comissao")
            apontamentos = lote.get("apontamentos_comissao")
            if parecer and status not in ["Solicitação de Retificação Pendente", "Retificação Recusada pela SEPAN"]:
                st.divider()
                if status == "Apta com Necessidade de Saneamento":
                    st.warning(f"**Parecer Técnico:** {parecer}\n\n**Apontamentos:** {apontamentos}")
                elif status == "Aprovada":
                    st.success(f"**Parecer Técnico:** {parecer}\n\n{apontamentos or 'Homologado sem ressalvas.'}")
                elif status == "Aprovada com Ressalvas":
                    st.info(f"**Parecer Técnico:** {parecer}\n\n**Observações:** {apontamentos}")
                elif status == "Não Aprovada":
                    st.error(f"**Parecer Técnico:** {parecer}\n\n**Motivação:** {apontamentos}")

            # -----------------------------------------------------------------
            # Fluxo de Retificação e Estorno do Lote
            # -----------------------------------------------------------------
            st.divider()

            if status == "Retificado pela Clínica" or (not transacoes_do_lote and status not in ["Enviado para Análise", "Solicitação de Retificação Pendente"]):
                st.info("Este lote foi retificado/estornado. Os procedimentos cirúrgicos retornaram para a aba de Fechamento de Lote Mensal para consolidação de uma nova prestação de contas.")
            
            elif status == "Solicitação de Retificação Pendente" or status_retificacao == "pendente":
                st.info(
                    f"**Solicitação de Retificação em Análise pela SEPAN**\n\n"
                    f"**Justificativa apresentada:** {motivo_retificacao or 'Não especificada.'}\n\n"
                    f"Aguardando a análise e deliberação dos servidores da SEPAN para liberação do lote."
                )

            elif status in ["Retificação Aprovada pela SEPAN", "Apta com Necessidade de Saneamento"] or status_retificacao == "aprovada":
                st.success(
                    "**Retificação Autorizada pela SEPAN**\n\n"
                    "A comissão autorizou a retificação deste lote. Clique no botão abaixo para estornar os atendimentos, efetuar as correções necessárias na aba de Fechamento de Lote Mensal e reenviar a prestação de contas."
                )
                if st.button("Estornar Lote para Correção", key=f"estorno_{lote_id}", width="stretch", type="primary"):
                    with st.spinner("Estornando lote para saneamento..."):
                        try:
                            # 1. Desvincula os atendimentos para que fiquem abertos novamente (lote_id = null)
                            supabase.table("relacao_transacoes").update({"lote_id": None}).eq("lote_id", lote_id).execute()

                            # 2. Atualiza o status do lote
                            payload_estorno = {
                                "status": "Retificado pela Clínica",
                                "solicitacao_retificacao": False,
                                "status_retificacao": "concluido",
                                "parecer_bloqueado": False
                            }
                            try:
                                supabase.table("lotes_prestacao").update(payload_estorno).eq("id", lote_id).execute()
                            except Exception:
                                supabase.table("lotes_prestacao").update({"status": "Retificado pela Clínica"}).eq("id", lote_id).execute()

                            registrar_log_auditoria(
                                supabase, cnpj, lote.get("nome_clinica") or cnpj,
                                tipo_entidade="lote",
                                acao="estorno",
                                descricao=f"Lote {mes_ref} estornado pela clínica para saneamento e correção de atendimentos",
                                referencia_id=lote_id
                            )

                            st.success("Lote estornado com sucesso. Os atendimentos já estão disponíveis na aba de Fechamento de Lote Mensal para correções.")
                            st.rerun()
                        except Exception as ex:
                            st.error(f"Erro ao estornar lote: {str(ex)}")

            elif status_retificacao == "recusada" or status == "Retificação Recusada pela SEPAN":
                st.error(
                    f"**Aviso: Solicitação de Retificação Recusada pela SEPAN**\n\n"
                    f"A comissão da SEPAN analisou e recusou o pedido de retificação deste lote.\n\n"
                    f"**Motivo da recusa informado pela SEPAN:** {motivo_recusa or 'Sem justificativa informada.'}"
                )

                # Permite à clínica submeter um novo pedido com esclarecimentos complementares
                with st.expander("Solicitar Novo Pedido de Retificação"):
                    st.caption("Caso possua novos esclarecimentos ou comprovações, formalize um novo pedido com a devida justificativa.")
                    nova_justificativa = st.text_area(
                        "Nova Justificativa da Retificação *",
                        placeholder="Descreva detalhadamente a necessidade de retificação deste lote...",
                        key=f"nova_just_{lote_id}"
                    )
                    if st.button("Enviar Novo Pedido de Retificação", key=f"btn_novo_retif_{lote_id}", type="secondary"):
                        if not nova_justificativa.strip():
                            st.error("Informe a justificativa para formalizar a retificação.")
                        else:
                            with st.spinner("Enviando solicitação à SEPAN..."):
                                try:
                                    payload_nova_retif = {
                                        "status": "Solicitação de Retificação Pendente",
                                        "solicitacao_retificacao": True,
                                        "status_retificacao": "pendente",
                                        "motivo_retificacao": nova_justificativa.strip(),
                                        "data_solicitacao_retificacao": datetime.now().isoformat()
                                    }
                                    try:
                                        supabase.table("lotes_prestacao").update(payload_nova_retif).eq("id", lote_id).execute()
                                    except Exception:
                                        supabase.table("lotes_prestacao").update({
                                            "status": "Solicitação de Retificação Pendente",
                                            "motivo_retificacao": nova_justificativa.strip()
                                        }).eq("id", lote_id).execute()

                                    st.success("Novo pedido de retificação enviado com sucesso aos servidores da SEPAN.")
                                    st.rerun()
                                except Exception as ex_nova:
                                    st.error(f"Erro ao enviar pedido de retificação: {str(ex_nova)}")

            else:
                # Lote enviado para análise ou aprovado/rejeitado sem pedido ativo de retificação
                with st.expander("Solicitar Retificação do Lote"):
                    st.caption(
                        "Caso necessite corrigir informações cadastrais, notas fiscais, microchips ou atendimentos deste lote já enviado, "
                        "formalize o pedido de retificação para análise e autorização dos servidores da SEPAN."
                    )
                    justificativa_retif = st.text_area(
                        "Justificativa / Motivo da Retificação *",
                        placeholder="Descreva detalhadamente o motivo da solicitação de retificação (ex: correção de microchip, ajuste de NF-e, remoção de atendimento incorreto)...",
                        key=f"just_retif_{lote_id}"
                    )
                    if st.button("Enviar Pedido de Retificação", key=f"btn_retif_{lote_id}", type="secondary"):
                        if not justificativa_retif.strip():
                            st.error("A justificativa é obrigatória para formalizar a solicitação de retificação.")
                        else:
                            with st.spinner("Enviando solicitação de retificação à SEPAN..."):
                                try:
                                    payload_req = {
                                        "status": "Solicitação de Retificação Pendente",
                                        "solicitacao_retificacao": True,
                                        "status_retificacao": "pendente",
                                        "motivo_retificacao": justificativa_retif.strip(),
                                        "data_solicitacao_retificacao": datetime.now().isoformat()
                                    }
                                    try:
                                        supabase.table("lotes_prestacao").update(payload_req).eq("id", lote_id).execute()
                                    except Exception:
                                        supabase.table("lotes_prestacao").update({
                                            "status": "Solicitação de Retificação Pendente",
                                            "motivo_retificacao": justificativa_retif.strip()
                                        }).eq("id", lote_id).execute()

                                    registrar_log_auditoria(
                                        supabase, cnpj, lote.get("nome_clinica") or cnpj,
                                        tipo_entidade="retificacao",
                                        acao="solicitacao_retificacao",
                                        descricao=f"Solicitação de retificação formalizada para o lote {mes_ref}. Justificativa: {justificativa_retif.strip()}",
                                        referencia_id=lote_id
                                    )

                                    st.success("Pedido de retificação enviado com sucesso. Aguarde a deliberação dos servidores da SEPAN.")
                                    st.rerun()
                                except Exception as ex_req:
                                    st.error(f"Erro ao enviar pedido de retificação: {str(ex_req)}")


# -----------------------------------------------------------------------------
# ABA 4: Auditoria e Consulta Geral de Atendimentos da Clínica
# -----------------------------------------------------------------------------
def fetch_transacoes_clinica(_supabase: Client, cnpj: str) -> pd.DataFrame:
    """Busca todas as transações da clínica credenciada no Supabase."""
    try:
        response = (
            _supabase.table("relacao_transacoes")
            .select("*")
            .eq("cnpj_clinica", cnpj)
            .order("data_atendimento", desc=True)
            .execute()
        )
        data = response.data or []
        if not data:
            return pd.DataFrame()

        df = pd.DataFrame(data)
        if "data_atendimento" in df.columns:
            df["data_atendimento"] = pd.to_datetime(df["data_atendimento"], errors="coerce")
        if "valor_transacao" in df.columns:
            df["valor_transacao"] = pd.to_numeric(df["valor_transacao"], errors="coerce").fillna(0.0)
        return df
    except Exception as e:
        st.error(f"Erro ao consultar atendimentos da clínica: {str(e)}")
        return pd.DataFrame()


def _render_tab_auditoria_clinica(supabase: Client, cnpj: str, nome_clinica: str):
    """Busca avançada e filtros estruturados em toda a base de atendimentos da clínica."""
    st.markdown("#### Auditoria e Consulta de Atendimentos")
    st.caption(f"Histórico e pesquisa avançada de todos os procedimentos cirúrgicos realizados por {nome_clinica}.")

    with st.spinner("Carregando atendimentos..."):
        df_raw = fetch_transacoes_clinica(supabase, cnpj)

    if df_raw.empty:
        st.info("Não foram encontrados atendimentos registrados para esta clínica.")
        return

    # --- Container de Filtros Estruturado ---
    with st.expander("Filtros de Pesquisa", expanded=True):
        # 1. Período, Status e Vínculo com Lote
        st.markdown("##### Período, Status e Vínculo")
        col_f1, col_f2, col_f3 = st.columns([1.4, 1, 1])

        with col_f1:
            min_date = df_raw["data_atendimento"].min().date() if not df_raw.empty and pd.notna(df_raw["data_atendimento"].min()) else date.today()
            max_date = df_raw["data_atendimento"].max().date() if not df_raw.empty and pd.notna(df_raw["data_atendimento"].max()) else date.today()
            periodo_selecionado = st.date_input(
                "Período de Atendimento:",
                value=(min_date, max_date),
                format="DD/MM/YYYY",
                key="clinica_auditoria_filtro_periodo"
            )

        with col_f2:
            status_disp = ["pendente", "aprovado", "rejeitado"]
            if "status_validacao" in df_raw.columns:
                vals_status = [str(s).lower() for s in df_raw["status_validacao"].dropna().unique().tolist() if str(s).strip()]
                status_disp = sorted(list(set(status_disp + vals_status)))

            filtro_status = st.multiselect(
                "Status de Validação:",
                options=status_disp,
                format_func=lambda s: str(s).capitalize(),
                placeholder="Todos os status",
                key="clinica_auditoria_filtro_status"
            )

        with col_f3:
            filtro_vinculo_lote = st.selectbox(
                "Vínculo com Lote:",
                options=["Todos", "Vinculados a Lote", "Avulsos (Sem Lote)"],
                index=0,
                key="clinica_auditoria_filtro_vinculo"
            )

        st.divider()

        # 2. Dados do Tutor / Beneficiário
        st.markdown("##### Beneficiário")
        col_t1, col_t2 = st.columns([1.5, 1])

        with col_t1:
            filtro_tutor_nome = st.text_input(
                "Nome do Beneficiário:",
                placeholder="Digite o nome completo ou parte...",
                key="clinica_auditoria_filtro_tutor_nome"
            )

        with col_t2:
            filtro_tutor_cpf = st.text_input(
                "CPF do Beneficiário:",
                placeholder="Digite o CPF com ou sem pontuação...",
                key="clinica_auditoria_filtro_tutor_cpf"
            )

        st.divider()

        # 3. Características do Animal
        st.markdown("##### Animal")
        col_a1, col_a2, col_a3, col_a4 = st.columns([1, 1, 1, 1.3])

        with col_a1:
            filtro_especie = st.multiselect(
                "Espécie:",
                options=["Canina", "Felina"],
                placeholder="Todas as espécies",
                key="clinica_auditoria_filtro_especie"
            )

        with col_a2:
            filtro_sexo = st.multiselect(
                "Sexo:",
                options=["Macho", "Fêmea"],
                placeholder="Todos os sexos",
                key="clinica_auditoria_filtro_sexo"
            )

        with col_a3:
            filtro_porte = st.multiselect(
                "Porte:",
                options=["Pequeno", "Médio", "Grande"],
                placeholder="Todos os portes",
                key="clinica_auditoria_filtro_porte"
            )

        with col_a4:
            filtro_microchip = st.text_input(
                "Nº do Microchip:",
                placeholder="Digite o número do microchip...",
                key="clinica_auditoria_filtro_microchip"
            )

        st.divider()

        # 4. Documentos & Busca Livre
        st.markdown("##### Documentação Fiscal e Busca Geral")
        col_d1, col_d2, col_d3 = st.columns([1.2, 1.8, 1])

        with col_d1:
            filtro_nfe = st.text_input(
                "NF-e / Nota Fiscal:",
                placeholder="Digite o número da NF-e...",
                key="clinica_auditoria_filtro_nfe"
            )

        with col_d2:
            filtro_geral = st.text_input(
                "Busca Geral:",
                placeholder="Digite qualquer termo para buscar...",
                key="clinica_auditoria_filtro_geral"
            )

        with col_d3:
            st.write("")
            st.write("")
            if st.button("Limpar Filtros", width="stretch", type="secondary", key="clinica_auditoria_btn_limpar"):
                for k in [
                    "clinica_auditoria_filtro_status", "clinica_auditoria_filtro_vinculo",
                    "clinica_auditoria_filtro_tutor_nome", "clinica_auditoria_filtro_tutor_cpf",
                    "clinica_auditoria_filtro_especie", "clinica_auditoria_filtro_sexo",
                    "clinica_auditoria_filtro_porte", "clinica_auditoria_filtro_microchip",
                    "clinica_auditoria_filtro_nfe", "clinica_auditoria_filtro_geral",
                    "clinica_auditoria_filtro_periodo"
                ]:
                    if k in st.session_state:
                        del st.session_state[k]
                st.rerun()

    # --- Aplicação dos Filtros ---
    df_filtered = df_raw.copy()

    # 1. Filtro Período
    if isinstance(periodo_selecionado, (tuple, list)) and len(periodo_selecionado) == 2:
        dt_inicio, dt_fim = periodo_selecionado
        df_filtered = df_filtered[
            (df_filtered["data_atendimento"].dt.date >= dt_inicio) &
            (df_filtered["data_atendimento"].dt.date <= dt_fim)
        ]

    # 2. Filtro Status de Validação
    if filtro_status:
        df_filtered = df_filtered[df_filtered["status_validacao"].astype(str).str.lower().isin(filtro_status)]

    # 3. Filtro Vínculo Lote
    if filtro_vinculo_lote == "Vinculados a Lote":
        df_filtered = df_filtered[df_filtered["lote_id"].notna() & (df_filtered["lote_id"].astype(str) != "")]
    elif filtro_vinculo_lote == "Avulsos (Sem Lote)":
        df_filtered = df_filtered[df_filtered["lote_id"].isna() | (df_filtered["lote_id"].astype(str) == "")]

    # 4. Filtro Tutor - Nome
    if filtro_tutor_nome and filtro_tutor_nome.strip():
        termo_nome = filtro_tutor_nome.strip().lower()
        df_filtered = df_filtered[
            df_filtered["nome_beneficiario"].astype(str).str.lower().str.contains(termo_nome, na=False)
        ]

    # 5. Filtro Tutor - CPF
    if filtro_tutor_cpf and filtro_tutor_cpf.strip():
        cpf_buscado_limpo = re.sub(r"[^\w\d]", "", filtro_tutor_cpf.strip())
        if cpf_buscado_limpo:
            df_filtered = df_filtered[
                df_filtered["cpf_beneficiario"].astype(str).apply(
                    lambda x: cpf_buscado_limpo in re.sub(r"[^\w\d]", "", str(x))
                )
            ]

    # 6. Filtro Animal - Espécie
    if filtro_especie:
        especies_lower = [e.lower() for e in filtro_especie]
        df_filtered = df_filtered[
            df_filtered["especie"].astype(str).str.lower().isin(especies_lower)
        ]

    # 7. Filtro Animal - Sexo
    if filtro_sexo:
        sexos_lower = [s.lower() for s in filtro_sexo]
        df_filtered = df_filtered[
            df_filtered["sexo"].astype(str).str.lower().isin(sexos_lower)
        ]

    # 8. Filtro Animal - Porte
    if filtro_porte:
        portes_lower = [p.lower() for p in filtro_porte]
        df_filtered = df_filtered[
            df_filtered["porte"].astype(str).str.lower().isin(portes_lower)
        ]

    # 9. Filtro Animal - Microchip
    if filtro_microchip and filtro_microchip.strip():
        chip_termo = filtro_microchip.strip().lower()
        df_filtered = df_filtered[
            df_filtered["numero_microchip"].astype(str).str.lower().str.contains(chip_termo, na=False)
        ]

    # 10. Filtro NF-e
    if filtro_nfe and filtro_nfe.strip():
        nfe_termo = filtro_nfe.strip().lower()
        df_filtered = df_filtered[
            df_filtered["nfe_referencia"].astype(str).str.lower().str.contains(nfe_termo, na=False)
        ]

    # 11. Filtro Busca Geral
    if filtro_geral and filtro_geral.strip():
        termo_geral = filtro_geral.strip().lower()
        termo_geral_limpo = re.sub(r"[^\w\d]", "", termo_geral)

        def match_geral_clinica(row):
            for col in ["cpf_beneficiario", "nome_beneficiario", "nfe_referencia", "numero_microchip", "especie", "porte", "sexo"]:
                if col in row and pd.notna(row[col]):
                    val_s = str(row[col]).lower()
                    if termo_geral in val_s:
                        return True
                    if termo_geral_limpo and termo_geral_limpo in re.sub(r"[^\w\d]", "", val_s):
                        return True
            return False

        df_filtered = df_filtered[df_filtered.apply(match_geral_clinica, axis=1)]

    # --- KPIs de Atendimentos Filtrados ---
    total_proc = len(df_filtered)
    valor_tot = df_filtered["valor_transacao"].sum() if not df_filtered.empty else 0.0
    total_caes = (df_filtered["especie"].astype(str).str.strip().str.capitalize() == "Canina").sum() if not df_filtered.empty else 0
    total_gatos = (df_filtered["especie"].astype(str).str.strip().str.capitalize() == "Felina").sum() if not df_filtered.empty else 0
    total_femeas = (df_filtered["sexo"].astype(str).str.strip().str.capitalize() == "Fêmea").sum() if not df_filtered.empty else 0
    total_machos = (df_filtered["sexo"].astype(str).str.strip().str.capitalize() == "Macho").sum() if not df_filtered.empty else 0

    col_kpi1, col_kpi2, col_kpi3, col_kpi4, col_kpi5 = st.columns(5)
    with col_kpi1:
        st.metric("Total de Atendimentos", f"{total_proc:,}".replace(",", "."))
    with col_kpi2:
        st.metric("Valor Total (R$)", f"R$ {valor_tot:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    with col_kpi3:
        st.metric("Cães Castrados", f"{total_caes:,}".replace(",", "."))
    with col_kpi4:
        st.metric("Gatos Castrados", f"{total_gatos:,}".replace(",", "."))
    with col_kpi5:
        st.metric("Fêmeas / Machos", f"{total_femeas} / {total_machos}")

    st.divider()

    col_subt, col_exp = st.columns([2.5, 1])
    with col_subt:
        st.markdown(f"#### Atendimentos Localizados ({total_proc})")

    with col_exp:
        if not df_filtered.empty:
            csv_export = df_filtered.to_csv(index=False, sep=";", encoding="utf-8-sig")
            st.download_button(
                label="Exportar Relatório (CSV)",
                data=csv_export,
                file_name=f"relatorio_atendimentos_{cnpj.replace('.', '').replace('/', '').replace('-', '')}_{date.today().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                width="stretch",
                type="primary",
                key="btn_export_csv_clinica"
            )

    if df_filtered.empty:
        st.warning("Nenhum atendimento atende aos filtros selecionados.")
    else:
        df_display = df_filtered.copy()
        if "obito" in df_display.columns:
            df_display["obito_view"] = df_display["obito"].apply(
                lambda o: "Sim" if o is True or str(o).lower() in ["true", "sim", "1"] else "Não"
            )
            colunas_map = {
                "data_atendimento": "Data",
                "nome_beneficiario": "Tutor / Beneficiário",
                "cpf_beneficiario": "CPF Tutor",
                "especie": "Espécie",
                "sexo": "Sexo",
                "porte": "Porte",
                "numero_microchip": "Microchip",
                "obito_view": "Óbito",
                "valor_transacao": "Valor (R$)",
                "nfe_referencia": "NF-e",
                "status_validacao": "Status",
                "lote_id": "ID Lote"
            }
        else:
            colunas_map = {
                "data_atendimento": "Data",
                "nome_beneficiario": "Tutor / Beneficiário",
                "cpf_beneficiario": "CPF Tutor",
                "especie": "Espécie",
                "sexo": "Sexo",
                "porte": "Porte",
                "numero_microchip": "Microchip",
                "valor_transacao": "Valor (R$)",
                "nfe_referencia": "NF-e",
                "status_validacao": "Status",
                "lote_id": "ID Lote"
            }
        cols_to_show = [col for col in colunas_map.keys() if col in df_display.columns]
        df_display = df_display[cols_to_show].copy()

        if "data_atendimento" in df_display.columns:
            df_display["data_atendimento"] = df_display["data_atendimento"].dt.strftime("%d/%m/%Y")
        if "valor_transacao" in df_display.columns:
            df_display["valor_transacao"] = df_display["valor_transacao"].apply(
                lambda v: f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            )
        if "lote_id" in df_display.columns:
            df_display["lote_id"] = df_display["lote_id"].apply(
                lambda x: str(x)[:8] if pd.notna(x) and str(x).strip() else "Avulso"
            )
        if "status_validacao" in df_display.columns:
            df_display["status_validacao"] = df_display["status_validacao"].apply(
                lambda s: str(s).capitalize() if pd.notna(s) else "Pendente"
            )

        df_display = df_display.rename(columns=colunas_map)

        st.dataframe(df_display, width="stretch", hide_index=True)
