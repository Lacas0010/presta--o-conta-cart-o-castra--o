"""
=============================================================================
SISTEMA DE FISCALIZAÇÃO E PRESTAÇÃO DE CONTAS - CARTÃO CASTRAÇÃO (SEPAN)
Módulo da Comissão de Gestão: modulo_comissao.py
=============================================================================
Responsável por:
1. Fila de trabalho e homologação de Lotes Mensais de Prestação de Contas.
2. Emissão de pareceres técnicos da Comissão de Gestão da SEPAN.
3. Auditoria geral com filtros e exportação de relatórios para o SEI.
=============================================================================
"""

import streamlit as st
import pandas as pd
import re
from datetime import datetime, date
from supabase import Client
from gerador_pdf import gerar_pdf_anexo_v, gerar_pdf_parecer_sepan, gerar_texto_parecer_sepan
from auditoria import registrar_log_auditoria, fetch_logs_auditoria


# -----------------------------------------------------------------------------
# 1. Consultas de Dados
# -----------------------------------------------------------------------------
@st.cache_data(ttl=120, show_spinner=False)
def fetch_transacoes(_supabase: Client) -> pd.DataFrame:
    """Busca todas as transações cadastradas na tabela 'relacao_transacoes'."""
    try:
        response = (
            _supabase.table("relacao_transacoes")
            .select("*")
            .order("data_atendimento", desc=True)
            .execute()
        )
        data = response.data or []
        if not data:
            return pd.DataFrame()

        df = pd.DataFrame(data)
        if "data_atendimento" in df.columns:
            df["data_atendimento"] = pd.to_datetime(df["data_atendimento"])
        if "valor_transacao" in df.columns:
            df["valor_transacao"] = pd.to_numeric(df["valor_transacao"], errors="coerce").fillna(0.0)
        if "created_at" in df.columns:
            df["created_at"] = pd.to_datetime(df["created_at"])
        return df

    except Exception as e:
        st.error(f"Erro ao consultar atendimentos: {str(e)}")
        return pd.DataFrame()


def fetch_lotes(_supabase: Client) -> pd.DataFrame:
    """Busca todos os lotes de prestação de contas submetidos."""
    try:
        response = (
            _supabase.table("lotes_prestacao")
            .select("*")
            .order("created_at", desc=True)
            .execute()
        )
        data = response.data or []
        if not data:
            return pd.DataFrame()

        df = pd.DataFrame(data)
        if "valor_total" in df.columns:
            df["valor_total"] = pd.to_numeric(df["valor_total"], errors="coerce").fillna(0.0)
        if "created_at" in df.columns:
            df["created_at"] = pd.to_datetime(df["created_at"])
        return df

    except Exception as e:
        st.error(f"Erro ao consultar lotes: {str(e)}")
        return pd.DataFrame()


def _bloquear_parecer_lote(supabase: Client, lote_id: str, processo_sei: str, membro_comissao: str):
    """Bloqueia alterações no parecer técnico após a emissão do documento oficial."""
    try:
        payload = {
            "parecer_bloqueado": True,
            "processo_sei": (processo_sei or "").strip(),
            "membro_analise": (membro_comissao or "").strip(),
            "data_bloqueio_parecer": datetime.now().isoformat()
        }
        try:
            supabase.table("lotes_prestacao").update(payload).eq("id", lote_id).execute()
        except Exception as ex_db:
            err_msg = str(ex_db)
            if "PGRST204" in err_msg or "Could not find" in err_msg or "parecer_bloqueado" in err_msg:
                pass
            else:
                raise ex_db
        st.session_state[f"parecer_bloqueado_{lote_id}"] = True
        registrar_log_auditoria(
            supabase, "", "",
            tipo_entidade="parecer",
            acao="bloqueio_parecer",
            descricao=f"Parecer técnico do lote ID {lote_id[:8]} homologado e bloqueado para emissão do documento SEI (Processo: {processo_sei or 'Não informado'})",
            referencia_id=lote_id
        )
        st.cache_data.clear()
    except Exception as ex:
        st.session_state[f"parecer_bloqueado_{lote_id}"] = True


# -----------------------------------------------------------------------------
# 2. Renderização Principal da Comissão
# -----------------------------------------------------------------------------
def render_modulo_comissao(supabase: Client):
    """Renderiza a interface da Comissão com abas de Análise e Auditoria."""
    col_title, col_btn = st.columns([3, 1])
    with col_title:
        st.markdown("### Painel de Fiscalização - SEPAN")
        st.caption("Homologação de prestações de contas e auditoria do Programa Cartão Castração")

    with col_btn:
        st.write("")
        if st.button("Atualizar Dados", width="stretch"):
            st.cache_data.clear()
            st.rerun()

    tab_lotes, tab_auditoria, tab_logs = st.tabs([
        "Prestações de Contas (Lotes)",
        "Auditoria de Atendimentos",
        "Histórico de Auditoria (Logs)"
    ])

    with tab_lotes:
        _render_tab_lotes(supabase)

    with tab_auditoria:
        _render_tab_auditoria(supabase)

    with tab_logs:
        _render_tab_historico_auditoria(supabase)


# -----------------------------------------------------------------------------
# ABA 1: Fila de Lotes e Pareceres Oficiais
# -----------------------------------------------------------------------------
def _render_tab_lotes(supabase: Client):
    """Análise técnica e emissão de parecer sobre os lotes mensais."""
    st.markdown("#### Fila de Prestações de Contas")

    df_lotes = fetch_lotes(supabase)

    if df_lotes.empty:
        st.info("Nenhum lote de prestação de contas submetido até o momento.")
        return

    pendentes_count = len(df_lotes[df_lotes["status"].isin(["Enviado para Análise", "Apta com Necessidade de Saneamento"])])
    aprovados_count = len(df_lotes[df_lotes["status"].isin(["Aprovada", "Aprovada com Ressalvas"])])
    retif_count = len(df_lotes[df_lotes["status"].isin(["Solicitação de Retificação Pendente"]) | (df_lotes.get("status_retificacao") == "pendente")]) if "status_retificacao" in df_lotes.columns else len(df_lotes[df_lotes["status"].isin(["Solicitação de Retificação Pendente"])])
    valor_pendente = df_lotes[df_lotes["status"].isin(["Enviado para Análise", "Apta com Necessidade de Saneamento", "Solicitação de Retificação Pendente"])]["valor_total"].sum()

    col_k1, col_k2, col_k3, col_k4 = st.columns(4)
    with col_k1:
        st.metric("Lotes Pendentes de Parecer", pendentes_count)
    with col_k2:
        st.metric("Lotes Homologados", aprovados_count)
    with col_k3:
        st.metric("Retificações Solicitadas", retif_count)
    with col_k4:
        st.metric(
            "Valor Total em Análise",
            f"R$ {valor_pendente:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        )

    st.divider()

    # --- Filtros de Seleção de Lotes ---
    with st.expander("Filtros de Pesquisa de Lotes", expanded=True):
        col_fl1, col_fl2, col_fl3, col_fl4 = st.columns([1.3, 1, 1, 1])

        # Filtro de Clínicas nos Lotes
        clinicas_lotes = sorted([
            c for c in df_lotes["nome_clinica"].dropna().unique().tolist() if str(c).strip()
        ])
        with col_fl1:
            filtro_clinica_lote = st.multiselect(
                "Filtrar por Clínica:",
                options=clinicas_lotes,
                placeholder="Todas as clínicas",
                key="filtro_lote_clinica"
            )

        # Filtro de Competências / Meses
        meses_lotes = sorted([
            m for m in df_lotes["mes_referencia"].dropna().unique().tolist() if str(m).strip()
        ])
        with col_fl2:
            filtro_mes_lote = st.multiselect(
                "Filtrar por Competência:",
                options=meses_lotes,
                placeholder="Todos os meses",
                key="filtro_lote_mes"
            )

        # Filtro de Status
        status_lotes_disp = sorted([
            s for s in df_lotes["status"].dropna().unique().tolist() if str(s).strip()
        ])
        with col_fl3:
            filtro_status_lote = st.multiselect(
                "Filtrar por Status:",
                options=status_lotes_disp,
                placeholder="Todos os status",
                key="filtro_lote_status"
            )

        # Busca Textual no Lote
        with col_fl4:
            busca_lote_txt = st.text_input(
                "Busca (CNPJ ou ID):",
                placeholder="Digite CNPJ ou ID...",
                key="filtro_lote_busca_txt"
            )

    df_lotes_filtrados = df_lotes.copy()
    if filtro_clinica_lote:
        df_lotes_filtrados = df_lotes_filtrados[df_lotes_filtrados["nome_clinica"].isin(filtro_clinica_lote)]
    if filtro_mes_lote:
        df_lotes_filtrados = df_lotes_filtrados[df_lotes_filtrados["mes_referencia"].isin(filtro_mes_lote)]
    if filtro_status_lote:
        df_lotes_filtrados = df_lotes_filtrados[df_lotes_filtrados["status"].isin(filtro_status_lote)]
    if busca_lote_txt and busca_lote_txt.strip():
        termo_lote = busca_lote_txt.strip().lower()
        termo_limpo = re.sub(r"[^\w\d]", "", termo_lote)

        def match_lote(row):
            id_str = str(row.get("id", "")).lower()
            cnpj_str = re.sub(r"[^\w\d]", "", str(row.get("cnpj_clinica", "")).lower())
            nome_str = str(row.get("nome_clinica", "")).lower()
            return termo_lote in id_str or (termo_limpo and termo_limpo in cnpj_str) or termo_lote in nome_str

        df_lotes_filtrados = df_lotes_filtrados[df_lotes_filtrados.apply(match_lote, axis=1)]

    if df_lotes_filtrados.empty:
        st.warning("Nenhum lote de prestação de contas encontrado com os filtros selecionados.")
        return

    lotes_dict = {}
    lote_options = []

    for _, row in df_lotes_filtrados.iterrows():
        lote_id = row["id"]
        status = row.get("status", "Enviado para Análise")
        nome_c = row.get("nome_clinica") or row.get("cnpj_clinica")
        mes = row.get("mes_referencia", "")
        valor = float(row.get("valor_total", 0.0))
        label = f"[{status}] {nome_c} | Competência: {mes} | R$ {valor:,.2f} (ID: {str(lote_id)[:8]})"

        lotes_dict[label] = row
        lote_options.append(label)

    col_sel, _ = st.columns([2.5, 1])
    with col_sel:
        escolha_lote = st.selectbox(
            f"Selecione o Lote para Fiscalização ({len(lote_options)} localizados):",
            options=lote_options,
            index=None,
            placeholder="Selecione um lote no menu para abrir a análise técnica...",
            key="comissao_escolha_lote_sel"
        )

    if not escolha_lote:
        st.markdown(
            """
            <div class="sepan-empty-banner">
                <div class="empty-title">Nenhum Lote Selecionado</div>
                <div class="empty-desc">
                    Selecione um lote de prestação de contas no menu acima para auditar os procedimentos cirúrgicos, emitir o parecer técnico da comissão e gerar os documentos oficiais para o SEI.
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        return

    selected_row = lotes_dict[escolha_lote]
    lote_id = selected_row["id"]
    status_atual = selected_row.get("status", "Enviado para Análise")
    nome_clinica = selected_row.get("nome_clinica") or selected_row.get("cnpj_clinica")
    cnpj_clinica = selected_row.get("cnpj_clinica", "")
    mes_ref = selected_row.get("mes_referencia", "")
    valor_total = float(selected_row.get("valor_total", 0.0))
    total_proc = int(selected_row.get("total_procedimentos", 0))
    obitos = selected_row.get("obitos_relato") or "Sem relato informado."
    reclamacoes = selected_row.get("reclamacoes_relato") or "Sem relato informado."

    # Mapeamento do status para badge visual
    if status_atual in ["Aprovada", "Homologado"]:
        badge_status_class = "badge-green"
    elif status_atual in ["Aprovada com Ressalvas", "Apta com Necessidade de Saneamento", "Retificação Aprovada pela SEPAN"]:
        badge_status_class = "badge-amber"
    elif status_atual in ["Solicitação de Retificação Pendente", "Enviado para Análise"]:
        badge_status_class = "badge-blue"
    elif status_atual in ["Não Aprovada", "Retificação Recusada pela SEPAN"]:
        badge_status_class = "badge-red"
    else:
        badge_status_class = "badge-slate"

    with st.container(border=True):
        col_hdr1, col_hdr2 = st.columns([3, 1])
        with col_hdr1:
            st.markdown(f"### {nome_clinica} &bull; Competência {mes_ref}")
            st.caption(f"CNPJ: `{cnpj_clinica}` &bull; ID do Lote: `{str(lote_id)[:8]}`")
        with col_hdr2:
            st.markdown(f"<div style='text-align: right; margin-top: 8px;'><span class='sepan-badge {badge_status_class}'>{status_atual}</span></div>", unsafe_allow_html=True)

        col_d1, col_d2, col_d3 = st.columns(3)
        with col_d1:
            st.metric("Procedimentos no Lote", total_proc)
        with col_d2:
            st.metric("Valor Faturado (R$)", f"R$ {valor_total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        with col_d3:
            st.metric("Status do Processo", status_atual)

        st.divider()

        col_rel1, col_rel2 = st.columns(2)
        with col_rel1:
            with st.container(border=True):
                st.markdown("**Relato de Óbitos e Intercorrências Cirúrgicas:**")
                st.write(obitos)

        with col_rel2:
            with st.container(border=True):
                st.markdown("**Relato de Reclamações de Beneficiários:**")
                st.write(reclamacoes)

        st.markdown("#### Atendimentos Vinculados ao Lote")
        try:
            res_transacoes = (
                supabase.table("relacao_transacoes")
                .select("*")
                .eq("lote_id", lote_id)
                .order("data_atendimento", desc=False)
                .execute()
            )
            transacoes_lote = res_transacoes.data or []
        except Exception as ex:
            st.error(f"Erro ao carregar atendimentos do lote: {str(ex)}")
            transacoes_lote = []

        if transacoes_lote:
            df_itens = pd.DataFrame(transacoes_lote)

            # Filtros rápidos dentro do lote selecionado
            col_search_lote1, col_search_lote2 = st.columns([2, 1])
            with col_search_lote1:
                busca_item_lote = st.text_input(
                    "Pesquisar neste lote (Tutor, CPF, Microchip, NF-e):",
                    placeholder="Digite para buscar...",
                    key=f"busca_item_{lote_id}"
                )
            with col_search_lote2:
                filtro_esp_lote = st.multiselect(
                    "Espécie:",
                    options=["Canina", "Felina"],
                    placeholder="Todas as espécies",
                    key=f"filtro_esp_{lote_id}"
                )

            df_itens_filtrados = df_itens.copy()
            if filtro_esp_lote:
                df_itens_filtrados = df_itens_filtrados[df_itens_filtrados["especie"].isin(filtro_esp_lote)]
            if busca_item_lote and busca_item_lote.strip():
                t_item = busca_item_lote.strip().lower()
                t_limpo = re.sub(r"[^\w\d]", "", t_item)

                def match_item(row):
                    tutor = str(row.get("nome_beneficiario", "")).lower()
                    cpf = re.sub(r"[^\w\d]", "", str(row.get("cpf_beneficiario", "")).lower())
                    chip = str(row.get("numero_microchip", "")).lower()
                    nfe = str(row.get("nfe_referencia", "")).lower()
                    return t_item in tutor or (t_limpo and t_limpo in cpf) or t_item in chip or t_item in nfe

                df_itens_filtrados = df_itens_filtrados[df_itens_filtrados.apply(match_item, axis=1)]

            if "obito" in df_itens_filtrados.columns:
                df_itens_filtrados["obito_view"] = df_itens_filtrados["obito"].apply(
                    lambda o: "Sim" if o is True or str(o).lower() in ["true", "sim", "1"] else "Não"
                )
                cols_map = {
                    "data_atendimento": "Data",
                    "nome_beneficiario": "Beneficiário",
                    "cpf_beneficiario": "CPF",
                    "especie": "Espécie",
                    "sexo": "Sexo",
                    "porte": "Porte",
                    "numero_microchip": "Microchip",
                    "obito_view": "Óbito",
                    "valor_transacao": "Valor (R$)",
                    "nfe_referencia": "NF-e"
                }
            else:
                cols_map = {
                    "data_atendimento": "Data",
                    "nome_beneficiario": "Beneficiário",
                    "cpf_beneficiario": "CPF",
                    "especie": "Espécie",
                    "sexo": "Sexo",
                    "porte": "Porte",
                    "numero_microchip": "Microchip",
                    "valor_transacao": "Valor (R$)",
                    "nfe_referencia": "NF-e"
                }
            cols_exibir = [c for c in cols_map.keys() if c in df_itens_filtrados.columns]
            df_itens_view = df_itens_filtrados[cols_exibir].copy()
            df_itens_view["valor_transacao"] = df_itens_view["valor_transacao"].apply(
                lambda v: f"R$ {float(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            )
            df_itens_view = df_itens_view.rename(columns=cols_map)
            st.dataframe(df_itens_view, width="stretch", hide_index=True)
            st.caption(f"Exibindo {len(df_itens_filtrados)} de {len(transacoes_lote)} atendimentos deste lote.")

            # Botão de Download do PDF Anexo V para os Fiscais
            try:
                pdf_bytes_comissao = gerar_pdf_anexo_v(selected_row.to_dict(), transacoes_lote)
                mes_arq = mes_ref.replace("/", "_")
                st.download_button(
                    label="Baixar Relatório Oficial (PDF - Anexo V / SEI)",
                    data=pdf_bytes_comissao,
                    file_name=f"Relatorio_{nome_clinica.replace(' ', '_')}_{mes_arq}.pdf",
                    mime="application/pdf",
                    key=f"pdf_comissao_{lote_id}",
                    width="stretch",
                    type="secondary"
                )
            except Exception as err_pdf:
                st.caption(f"Erro ao gerar PDF: {str(err_pdf)}")
        else:
            st.warning("Não há atendimentos vinculados a este identificador de lote.")

    # -------------------------------------------------------------------------
    # Solicitação e Deliberação de Retificação de Lote
    # -------------------------------------------------------------------------
    status_retificacao = selected_row.get("status_retificacao")
    motivo_retificacao = selected_row.get("motivo_retificacao")
    data_solicitacao_retificacao = selected_row.get("data_solicitacao_retificacao")
    motivo_recusa_retificacao = selected_row.get("motivo_recusa_retificacao")
    analisado_retificacao_por = selected_row.get("analisado_retificacao_por")

    if status_atual == "Solicitação de Retificação Pendente" or status_retificacao == "pendente":
        st.markdown("#### Pedido de Retificação Solicitado pela Clínica")
        with st.container(border=True):
            st.warning(
                f"**A clínica credenciada formalizou um pedido de retificação para este lote.**\n\n"
                f"**Justificativa apresentada:** {motivo_retificacao or 'Não informada.'}"
            )
            if data_solicitacao_retificacao:
                st.caption(f"Data do pedido: {str(data_solicitacao_retificacao)[:19].replace('T', ' ')}")

            col_dec_ret1, col_dec_ret2 = st.columns(2)
            with col_dec_ret1:
                st.markdown("**1. Autorizar Retificação:**")
                st.caption("Libera o lote para estorno dos atendimentos, correções e reenvio pela clínica.")
                if st.button("Aceitar Retificação do Lote", key=f"btn_aceitar_retif_{lote_id}", type="primary", width="stretch"):
                    with st.spinner("Registrando aceite da retificação..."):
                        try:
                            user_email = (
                                st.session_state.get("user").email
                                if "user" in st.session_state and st.session_state.user
                                else "Comissão SEPAN"
                            )
                            update_retif = {
                                "status": "Retificação Aprovada pela SEPAN",
                                "solicitacao_retificacao": True,
                                "status_retificacao": "aprovada",
                                "parecer_bloqueado": False,
                                "analisado_retificacao_por": user_email,
                                "data_resposta_retificacao": datetime.now().isoformat()
                            }
                            try:
                                supabase.table("lotes_prestacao").update(update_retif).eq("id", lote_id).execute()
                            except Exception:
                                supabase.table("lotes_prestacao").update({
                                    "status": "Retificação Aprovada pela SEPAN",
                                    "parecer_bloqueado": False
                                }).eq("id", lote_id).execute()

                            st.session_state[f"parecer_bloqueado_{lote_id}"] = False
                            registrar_log_auditoria(
                                supabase, cnpj_clinica, nome_clinica,
                                tipo_entidade="retificacao",
                                acao="aceite_retificacao",
                                descricao=f"Pedido de retificação do lote {mes_ref} da clínica {nome_clinica} APROVADO pela comissão SEPAN",
                                referencia_id=lote_id
                            )
                            st.success("Retificação autorizada. Lote liberado para correções pela clínica.")
                            st.cache_data.clear()
                            st.rerun()
                        except Exception as ex_aceite:
                            st.error(f"Erro ao aceitar retificação: {str(ex_aceite)}")

            with col_dec_ret2:
                st.markdown("**2. Recusar Retificação:**")
                st.caption("Indefere o pedido e registra a fundamentação da recusa no painel da clínica.")
                with st.popover("Recusar Retificação", use_container_width=True):
                    motivo_recusa_input = st.text_area(
                        "Motivo da Recusa *",
                        placeholder="Informe a fundamentação da recusa da retificação...",
                        key=f"motivo_recusa_input_{lote_id}"
                    )
                    if st.button("Confirmar Recusa da Retificação", key=f"btn_conf_recusa_{lote_id}", type="secondary", width="stretch"):
                        if not motivo_recusa_input.strip():
                            st.error("Informe a fundamentação da recusa.")
                        else:
                            with st.spinner("Registrando recusa..."):
                                try:
                                    user_email = (
                                        st.session_state.get("user").email
                                        if "user" in st.session_state and st.session_state.user
                                        else "Comissão SEPAN"
                                    )
                                    update_recusa = {
                                        "status": "Retificação Recusada pela SEPAN",
                                        "solicitacao_retificacao": False,
                                        "status_retificacao": "recusada",
                                        "motivo_recusa_retificacao": motivo_recusa_input.strip(),
                                        "analisado_retificacao_por": user_email,
                                        "data_resposta_retificacao": datetime.now().isoformat()
                                    }
                                    try:
                                        supabase.table("lotes_prestacao").update(update_recusa).eq("id", lote_id).execute()
                                    except Exception:
                                        supabase.table("lotes_prestacao").update({
                                            "status": "Retificação Recusada pela SEPAN"
                                        }).eq("id", lote_id).execute()

                                    registrar_log_auditoria(
                                        supabase, cnpj_clinica, nome_clinica,
                                        tipo_entidade="retificacao",
                                        acao="recusa_retificacao",
                                        descricao=f"Pedido de retificação do lote {mes_ref} da clínica {nome_clinica} RECUSADO pela comissão SEPAN. Motivo: {motivo_recusa_input.strip()}",
                                        referencia_id=lote_id
                                    )
                                    st.info("Solicitação de retificação indeferida.")
                                    st.cache_data.clear()
                                    st.rerun()
                                except Exception as ex_recusa:
                                    st.error(f"Erro ao registrar recusa: {str(ex_recusa)}")

    elif status_atual == "Retificação Aprovada pela SEPAN" or status_retificacao == "aprovada":
        st.success(
            f"**Retificação Aprovada pela SEPAN**\n\n"
            f"A comissão autorizou a retificação deste lote (Analisado por: `{analisado_retificacao_por or 'Comissão'}`). "
            f"O lote aguarda estorno e saneamento pela clínica credenciada."
        )

    elif status_atual == "Retificação Recusada pela SEPAN" or status_retificacao == "recusada":
        st.error(
            f"**Retificação Recusada pela SEPAN**\n\n"
            f"O pedido de retificação deste lote foi recusado por `{analisado_retificacao_por or 'Comissão'}`.\n\n"
            f"**Motivo registrado:** {motivo_recusa_retificacao or 'Não informado.'}"
        )

    st.markdown("#### Parecer da Comissão de Gestão")

    is_parecer_bloqueado = (
        bool(selected_row.get("parecer_bloqueado", False))
        or bool(st.session_state.get(f"parecer_bloqueado_{lote_id}", False))
    )

    if is_parecer_bloqueado:
        st.info(
            "Este parecer técnico foi finalizado e homologado com emissão do documento oficial (PDF). "
            "Para garantir a integridade do processo de prestação de contas, novas alterações neste parecer não são permitidas."
        )

    PARECERES_OPCOES = [
        "Aprovada",
        "Aprovada com Ressalvas",
        "Apta com Necessidade de Saneamento",
        "Não Aprovada"
    ]

    parecer_salvo = selected_row.get("parecer_comissao") or status_atual
    default_parecer_idx = (
        PARECERES_OPCOES.index(parecer_salvo)
        if parecer_salvo in PARECERES_OPCOES
        else 0
    )

    with st.form(key=f"form_decisao_{lote_id}"):
        st.markdown("##### 5. Monitoramento dos Cadastros no CRIA")
        col_cria1, col_cria2 = st.columns([1, 2])
        with col_cria1:
            val_cria_init = int(selected_row.get("qtd_cria") if pd.notna(selected_row.get("qtd_cria")) else total_proc)
            val_cria_init = min(max(0, val_cria_init), max(0, total_proc))
            qtd_cria = st.number_input(
                "Quantidade de animais cadastrados no CRIA:",
                min_value=0,
                max_value=max(0, total_proc),
                step=1,
                value=val_cria_init,
                disabled=is_parecer_bloqueado,
                help=f"A quantidade não pode exceder o total de procedimentos do lote ({total_proc})."
            )
        with col_cria2:
            inconsistencias_cria = st.text_area(
                "Inconsistências ou Divergências Cadastrais:",
                value=str(selected_row.get("inconsistencias_cria") or "") if pd.notna(selected_row.get("inconsistencias_cria")) else "",
                placeholder="Descreva divergências encontradas ou deixe em branco se regular...",
                disabled=is_parecer_bloqueado
            )

        st.markdown("##### 6 e 7. Pontos de Atenção e Notas Pendentes")
        notas_pendentes = st.text_area(
            "Notas Pendentes de Envio / Pontos de Atenção:",
            value=str(selected_row.get("notas_pendentes") or "") if pd.notna(selected_row.get("notas_pendentes")) else "",
            placeholder="Descreva notas pendentes ou pontos de atenção observados...",
            disabled=is_parecer_bloqueado
        )

        st.markdown("##### 8. Análise de Conformidade")
        apontamentos = st.text_area(
            "Apontamentos da Fiscalização / Análise de Conformidade:",
            value=str(selected_row.get("apontamentos_comissao") or "") if pd.notna(selected_row.get("apontamentos_comissao")) else "",
            placeholder="Descreva a análise de conformidade dos serviços executados e preços praticados...",
            disabled=is_parecer_bloqueado
        )

        st.markdown("##### 9. Determinações e Providências")
        providencias = st.text_area(
            "Determinações e Providências:",
            value=str(selected_row.get("providencias") or "") if pd.notna(selected_row.get("providencias")) else "",
            placeholder="Informe as determinações ou providências a serem adotadas pela clínica...",
            disabled=is_parecer_bloqueado
        )

        st.markdown("##### 10. Parecer Final")
        col_p1, _ = st.columns([1.5, 1])
        with col_p1:
            novo_parecer = st.selectbox(
                "Parecer Final:",
                options=PARECERES_OPCOES,
                index=default_parecer_idx,
                disabled=is_parecer_bloqueado
            )

        submit_decisao = st.form_submit_button(
            "Salvar Parecer e Fiscalização",
            width="stretch",
            type="primary",
            disabled=is_parecer_bloqueado
        )

        if submit_decisao:
            if is_parecer_bloqueado:
                st.error("Este parecer está bloqueado para alterações.")
                st.stop()

            if int(qtd_cria) > total_proc:
                st.error(f"A quantidade de animais cadastrados no CRIA ({qtd_cria}) não pode ser superior ao total de procedimentos do lote ({total_proc}).")
                st.stop()

            with st.spinner("Salvando parecer técnico..."):
                try:
                    user_email = (
                        st.session_state.get("user").email
                        if "user" in st.session_state and st.session_state.user
                        else "Comissão SEPAN"
                    )

                    update_payload = {
                        "status": novo_parecer,
                        "parecer_comissao": novo_parecer,
                        "qtd_cria": int(qtd_cria),
                        "inconsistencias_cria": inconsistencias_cria.strip(),
                        "notas_pendentes": notas_pendentes.strip(),
                        "apontamentos_comissao": apontamentos.strip(),
                        "providencias": providencias.strip(),
                        "data_parecer": datetime.now().isoformat(),
                        "analisado_por": user_email
                    }

                    try:
                        supabase.table("lotes_prestacao").update(update_payload).eq("id", lote_id).execute()
                    except Exception as ex_up:
                        err_up = str(ex_up)
                        if "PGRST204" in err_up or "Could not find" in err_up:
                            colunas_novas = ["qtd_cria", "inconsistencias_cria", "notas_pendentes", "providencias"]
                            payload_seguro = {k: v for k, v in update_payload.items() if k not in colunas_novas}
                            supabase.table("lotes_prestacao").update(payload_seguro).eq("id", lote_id).execute()
                        else:
                            raise ex_up

                    status_transacoes = "aprovado" if novo_parecer in ["Aprovada", "Aprovada com Ressalvas"] else (
                        "rejeitado" if novo_parecer == "Não Aprovada" else "pendente"
                    )
                    supabase.table("relacao_transacoes").update({"status_validacao": status_transacoes}).eq("lote_id", lote_id).execute()

                    registrar_log_auditoria(
                        supabase, cnpj_clinica, nome_clinica,
                        tipo_entidade="parecer",
                        acao="emissao_parecer",
                        descricao=f"Parecer técnico '{novo_parecer}' emitido para o lote {mes_ref} da clínica {nome_clinica} (CRIA: {int(qtd_cria)}/{total_proc})",
                        referencia_id=lote_id,
                        detalhes=update_payload
                    )

                    st.success(f"Parecer '{novo_parecer}' registrado para a clínica {nome_clinica} ({mes_ref}).")
                    st.cache_data.clear()
                    st.rerun()

                except Exception as ex:
                    st.error(f"Erro ao registrar parecer: {str(ex)}")

    # -------------------------------------------------------------------------
    # 5. Emissão do Relatório Técnico Oficial de Fiscalização (SEPAN / SEI)
    # -------------------------------------------------------------------------
    if status_atual in ["Aprovada", "Aprovada com Ressalvas", "Apta com Necessidade de Saneamento", "Não Aprovada"] or selected_row.get("parecer_comissao"):
        st.divider()
        st.markdown("#### Documento Oficial de Fiscalização (SEI)")
        st.success(f"Este lote possui parecer técnico registrado: **{status_atual}**.")

        val_sei_salvo = str(selected_row.get("processo_sei") or "") if pd.notna(selected_row.get("processo_sei")) else ""
        val_membro_salvo = str(selected_row.get("membro_analise") or "") if pd.notna(selected_row.get("membro_analise")) else ""

        col_sei, col_mem = st.columns([1.2, 1.2])
        with col_sei:
            processo_sei = st.text_input(
                "Número do Processo SEI:",
                value=val_sei_salvo,
                placeholder="00000-00000000/0000-00",
                key=f"sei_{lote_id}",
                disabled=is_parecer_bloqueado,
                help="Informe o número do processo SEI correspondente para constar no cabeçalho do documento."
            )

        user_meta = getattr(st.session_state.get("user"), "user_metadata", {}) or {} if "user" in st.session_state and st.session_state.user else {}
        membro_padrao = (
            val_membro_salvo
            or user_meta.get("nome")
            or user_meta.get("name")
            or getattr(st.session_state.get("user"), "email", "Membro da Comissão de Gestão")
        )

        with col_mem:
            membro_comissao = st.text_input(
                "Membro Responsável pela Análise:",
                value=membro_padrao,
                key=f"mem_{lote_id}",
                disabled=is_parecer_bloqueado,
                help="Nome do fiscal ou membro da comissão que assinará o parecer."
            )

        try:
            cnpj_limpo = str(cnpj_clinica).replace(".", "").replace("/", "").replace("-", "").strip()
            pdf_parecer_bytes = gerar_pdf_parecer_sepan(
                selected_row.to_dict(),
                processo_sei,
                membro_comissao,
                transacoes_lote
            )
            texto_sei_gerado = gerar_texto_parecer_sepan(
                selected_row.to_dict(),
                processo_sei,
                membro_comissao,
                transacoes_lote
            )

            tab_doc_pdf, tab_doc_sei = st.tabs([
                "Baixar Parecer Técnico (PDF)",
                "Texto para o SEI (Copiar e Colar)"
            ])

            with tab_doc_pdf:
                st.caption("Gera o arquivo PDF oficial formatado para juntada ou arquivo do processo de fiscalização.")
                st.download_button(
                    label="Baixar Parecer Técnico (PDF)",
                    data=pdf_parecer_bytes,
                    file_name=f"Parecer_SEPAN_{cnpj_limpo}.pdf",
                    mime="application/pdf",
                    key=f"pdf_parecer_{lote_id}",
                    width="stretch",
                    type="primary",
                    on_click=_bloquear_parecer_lote,
                    args=(supabase, lote_id, processo_sei, membro_comissao),
                    help="Gera e baixa o Relatório de Prestação de Contas e Fiscalização da SEPAN formatado para o SEI, bloqueando alterações deste parecer."
                )

            with tab_doc_sei:
                st.caption("Texto formatado para criação de **Documento Nato-Digital** no SEI-GDF, possibilitando a assinatura eletrônica da comissão diretamente no processo.")
                
                col_info_sei, col_lock_sei = st.columns([2.2, 1.2])
                with col_info_sei:
                    st.info("Copie o texto estruturado abaixo e cole diretamente no editor de documentos do SEI.")
                with col_lock_sei:
                    if st.button("Homologar e Bloquear Parecer", key=f"btn_lock_sei_{lote_id}", width="stretch", type="secondary", disabled=is_parecer_bloqueado):
                        _bloquear_parecer_lote(supabase, lote_id, processo_sei, membro_comissao)
                        st.success("Parecer homologado e bloqueado com sucesso.")
                        st.rerun()

                st.code(texto_sei_gerado, language="text")

                with st.expander("Pré-visualização do Parecer em Campo de Texto"):
                    st.text_area(
                        "Texto Completo do Parecer para o SEI:",
                        value=texto_sei_gerado,
                        height=350,
                        key=f"txt_area_sei_{lote_id}"
                    )

        except Exception as err_parecer:
            st.error(f"Erro ao gerar documento do parecer: {str(err_parecer)}")


# -----------------------------------------------------------------------------
# ABA 2: Auditoria Geral de Atendimentos
# -----------------------------------------------------------------------------
def _render_tab_auditoria(supabase: Client):
    """Busca e filtros avançados em toda a base de atendimentos."""
    with st.spinner("Carregando atendimentos..."):
        df_raw = fetch_transacoes(supabase)

    if df_raw.empty:
        st.info("Não foram encontrados registros de atendimentos.")
        return

    if "nome_clinica" not in df_raw.columns:
        df_raw["nome_clinica"] = df_raw["cnpj_clinica"]
    else:
        df_raw["nome_clinica"] = df_raw["nome_clinica"].fillna(df_raw["cnpj_clinica"])

    # --- Container de Filtros Estruturado ---
    with st.expander("Filtros de Pesquisa", expanded=True):
        # 1. Estabelecimento e Período
        st.markdown("##### Estabelecimento, Período e Status")
        col_f1, col_f2, col_f3, col_f4 = st.columns([1.4, 1.2, 1, 1])

        with col_f1:
            clinicas_disponiveis = sorted(
                [c for c in df_raw["nome_clinica"].dropna().unique().tolist() if str(c).strip()]
            )
            filtro_clinica = st.multiselect(
                "Clínica Credenciada:",
                options=clinicas_disponiveis,
                placeholder="Todas as clínicas",
                key="auditoria_filtro_clinica"
            )

        with col_f2:
            min_date = df_raw["data_atendimento"].min().date() if not df_raw.empty and pd.notna(df_raw["data_atendimento"].min()) else date.today()
            max_date = df_raw["data_atendimento"].max().date() if not df_raw.empty and pd.notna(df_raw["data_atendimento"].max()) else date.today()
            periodo_selecionado = st.date_input(
                "Período de Atendimento:",
                value=(min_date, max_date),
                format="DD/MM/YYYY",
                key="auditoria_filtro_periodo"
            )

        with col_f3:
            status_disp = ["pendente", "aprovado", "rejeitado"]
            if "status_validacao" in df_raw.columns:
                vals_status = [str(s).lower() for s in df_raw["status_validacao"].dropna().unique().tolist() if str(s).strip()]
                status_disp = sorted(list(set(status_disp + vals_status)))

            filtro_status = st.multiselect(
                "Status de Validação:",
                options=status_disp,
                format_func=lambda s: str(s).capitalize(),
                placeholder="Todos os status",
                key="auditoria_filtro_status"
            )

        with col_f4:
            filtro_vinculo_lote = st.selectbox(
                "Vínculo com Lote:",
                options=["Todos", "Vinculados a Lote", "Avulsos (Sem Lote)"],
                index=0,
                key="auditoria_filtro_vinculo"
            )

        st.divider()

        # 2. Dados do Tutor / Beneficiário
        st.markdown("##### Beneficiário")
        col_t1, col_t2 = st.columns([1.5, 1])

        with col_t1:
            filtro_tutor_nome = st.text_input(
                "Nome do Beneficiário:",
                placeholder="Digite o nome completo ou parte...",
                key="auditoria_filtro_tutor_nome"
            )

        with col_t2:
            filtro_tutor_cpf = st.text_input(
                "CPF do Beneficiário:",
                placeholder="Digite o CPF com ou sem pontuação...",
                key="auditoria_filtro_tutor_cpf"
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
                key="auditoria_filtro_especie"
            )

        with col_a2:
            filtro_sexo = st.multiselect(
                "Sexo:",
                options=["Macho", "Fêmea"],
                placeholder="Todos os sexos",
                key="auditoria_filtro_sexo"
            )

        with col_a3:
            filtro_porte = st.multiselect(
                "Porte:",
                options=["Pequeno", "Médio", "Grande"],
                placeholder="Todos os portes",
                key="auditoria_filtro_porte"
            )

        with col_a4:
            filtro_microchip = st.text_input(
                "Nº do Microchip:",
                placeholder="Digite o número do microchip...",
                key="auditoria_filtro_microchip"
            )

        st.divider()

        # 4. Documentos & Busca Livre
        st.markdown("##### Documentação Fiscal e Busca Geral")
        col_d1, col_d2, col_d3 = st.columns([1.2, 1.8, 1])

        with col_d1:
            filtro_nfe = st.text_input(
                "NF-e / Nota Fiscal:",
                placeholder="Digite o número da NF-e...",
                key="auditoria_filtro_nfe"
            )

        with col_d2:
            filtro_geral = st.text_input(
                "Busca Geral:",
                placeholder="Digite qualquer termo para buscar...",
                key="auditoria_filtro_geral"
            )

        with col_d3:
            st.write("")
            st.write("")
            if st.button("Limpar Filtros", width="stretch", type="secondary"):
                for k in [
                    "auditoria_filtro_clinica", "auditoria_filtro_status",
                    "auditoria_filtro_tutor_nome", "auditoria_filtro_tutor_cpf",
                    "auditoria_filtro_especie", "auditoria_filtro_sexo",
                    "auditoria_filtro_porte", "auditoria_filtro_microchip",
                    "auditoria_filtro_nfe", "auditoria_filtro_geral"
                ]:
                    if k in st.session_state:
                        del st.session_state[k]
                st.rerun()

    # --- Aplicação dos Filtros ---
    df_filtered = df_raw.copy()

    # 1. Filtro Clínica
    if filtro_clinica:
        df_filtered = df_filtered[df_filtered["nome_clinica"].isin(filtro_clinica)]

    # 2. Filtro Período
    if isinstance(periodo_selecionado, (tuple, list)) and len(periodo_selecionado) == 2:
        dt_inicio, dt_fim = periodo_selecionado
        df_filtered = df_filtered[
            (df_filtered["data_atendimento"].dt.date >= dt_inicio) &
            (df_filtered["data_atendimento"].dt.date <= dt_fim)
        ]

    # 3. Filtro Status de Validação
    if filtro_status:
        df_filtered = df_filtered[df_filtered["status_validacao"].astype(str).str.lower().isin(filtro_status)]

    # 4. Filtro Vínculo Lote
    if filtro_vinculo_lote == "Vinculados a Lote":
        df_filtered = df_filtered[df_filtered["lote_id"].notna() & (df_filtered["lote_id"].astype(str) != "")]
    elif filtro_vinculo_lote == "Avulsos (Sem Lote)":
        df_filtered = df_filtered[df_filtered["lote_id"].isna() | (df_filtered["lote_id"].astype(str) == "")]

    # 5. Filtro Tutor - Nome
    if filtro_tutor_nome and filtro_tutor_nome.strip():
        termo_nome = filtro_tutor_nome.strip().lower()
        df_filtered = df_filtered[
            df_filtered["nome_beneficiario"].astype(str).str.lower().str.contains(termo_nome, na=False)
        ]

    # 6. Filtro Tutor - CPF
    if filtro_tutor_cpf and filtro_tutor_cpf.strip():
        cpf_buscado_limpo = re.sub(r"[^\w\d]", "", filtro_tutor_cpf.strip())
        if cpf_buscado_limpo:
            df_filtered = df_filtered[
                df_filtered["cpf_beneficiario"].astype(str).apply(
                    lambda x: cpf_buscado_limpo in re.sub(r"[^\w\d]", "", str(x))
                )
            ]

    # 7. Filtro Animal - Espécie
    if filtro_especie:
        especies_lower = [e.lower() for e in filtro_especie]
        df_filtered = df_filtered[
            df_filtered["especie"].astype(str).str.lower().isin(especies_lower)
        ]

    # 8. Filtro Animal - Sexo
    if filtro_sexo:
        sexos_lower = [s.lower() for s in filtro_sexo]
        df_filtered = df_filtered[
            df_filtered["sexo"].astype(str).str.lower().isin(sexos_lower)
        ]

    # 9. Filtro Animal - Porte
    if filtro_porte:
        portes_lower = [p.lower() for p in filtro_porte]
        df_filtered = df_filtered[
            df_filtered["porte"].astype(str).str.lower().isin(portes_lower)
        ]

    # 10. Filtro Animal - Microchip
    if filtro_microchip and filtro_microchip.strip():
        chip_termo = filtro_microchip.strip().lower()
        df_filtered = df_filtered[
            df_filtered["numero_microchip"].astype(str).str.lower().str.contains(chip_termo, na=False)
        ]

    # 11. Filtro NF-e
    if filtro_nfe and filtro_nfe.strip():
        nfe_termo = filtro_nfe.strip().lower()
        df_filtered = df_filtered[
            df_filtered["nfe_referencia"].astype(str).str.lower().str.contains(nfe_termo, na=False)
        ]

    # 12. Filtro Busca Geral
    if filtro_geral and filtro_geral.strip():
        termo_geral = filtro_geral.strip().lower()
        termo_geral_limpo = re.sub(r"[^\w\d]", "", termo_geral)

        def match_geral(row):
            for col in ["nome_clinica", "cnpj_clinica", "cpf_beneficiario", "nome_beneficiario", "nfe_referencia", "numero_microchip", "especie", "porte", "sexo"]:
                if col in row and pd.notna(row[col]):
                    val_s = str(row[col]).lower()
                    if termo_geral in val_s:
                        return True
                    if termo_geral_limpo and termo_geral_limpo in re.sub(r"[^\w\d]", "", val_s):
                        return True
            return False

        df_filtered = df_filtered[df_filtered.apply(match_geral, axis=1)]

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
        st.markdown(f"#### Registros Localizados ({total_proc})")

    with col_exp:
        if not df_filtered.empty:
            csv_export = df_filtered.to_csv(index=False, sep=";", encoding="utf-8-sig")
            st.download_button(
                label="Exportar Relatório (CSV)",
                data=csv_export,
                file_name=f"relatorio_fiscalizacao_sepan_{date.today().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                width="stretch",
                type="primary"
            )

    if df_filtered.empty:
        st.warning("Nenhum registro atende aos critérios selecionados.")
    else:
        df_display = df_filtered.copy()
        if "obito" in df_display.columns:
            df_display["obito_view"] = df_display["obito"].apply(
                lambda o: "Sim" if o is True or str(o).lower() in ["true", "sim", "1"] else "Não"
            )
            colunas_map = {
                "data_atendimento": "Data",
                "nome_clinica": "Clínica",
                "cnpj_clinica": "CNPJ Clínica",
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
                "nome_clinica": "Clínica",
                "cnpj_clinica": "CNPJ Clínica",
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


# -----------------------------------------------------------------------------
# ABA 3: Histórico de Auditoria e Logs do Sistema
# -----------------------------------------------------------------------------
def _render_tab_historico_auditoria(supabase: Client):
    """Exibe o histórico completo de auditoria e alterações do sistema com filtros avançados."""
    st.markdown("#### Histórico de Auditoria e Rastreabilidade")
    st.caption("Registro cronológico de todas as ações, cadastros, alterações, exclusões, pareceres e retificações.")

    with st.spinner("Carregando histórico de auditoria..."):
        df_logs = fetch_logs_auditoria(supabase)

    if df_logs.empty:
        st.info("Nenhum evento registrado no histórico de auditoria até o momento.")
        return

    # --- Container de Filtros Estruturado ---
    with st.expander("Filtros do Histórico de Auditoria", expanded=True):
        col_f1, col_f2, col_f3 = st.columns([1.4, 1.2, 1])

        # 1. Filtro por Clínica
        with col_f1:
            clinicas_disp = sorted([c for c in df_logs["nome_clinica"].dropna().unique().tolist() if str(c).strip()])
            filtro_clinica_log = st.multiselect(
                "Filtrar por Clínica:",
                options=clinicas_disp,
                placeholder="Todas as clínicas",
                key="filtro_log_clinica"
            )

        # 2. Filtro por Período
        with col_f2:
            min_date = df_logs["created_at"].min().date() if not df_logs.empty and pd.notna(df_logs["created_at"].min()) else date.today()
            max_date = df_logs["created_at"].max().date() if not df_logs.empty and pd.notna(df_logs["created_at"].max()) else date.today()
            periodo_log = st.date_input(
                "Período do Registro:",
                value=(min_date, max_date),
                format="DD/MM/YYYY",
                key="filtro_log_periodo"
            )

        # 3. Filtro por Tipo de Entidade
        with col_f3:
            entidades_disp = sorted([str(e).capitalize() for e in df_logs["tipo_entidade"].dropna().unique().tolist() if str(e).strip()])
            filtro_entidade_log = st.multiselect(
                "Tipo de Registro:",
                options=entidades_disp,
                placeholder="Todos os tipos",
                key="filtro_log_entidade"
            )

        st.divider()

        col_f4, col_f5, col_f6 = st.columns([1.2, 1.4, 1])
        # 4. Filtro por Ação
        with col_f4:
            acoes_disp = sorted([str(a).replace("_", " ").title() for a in df_logs["acao"].dropna().unique().tolist() if str(a).strip()])
            filtro_acao_log = st.multiselect(
                "Ação Realizada:",
                options=acoes_disp,
                placeholder="Todas as ações",
                key="filtro_log_acao"
            )

        # 5. Busca Textual
        with col_f5:
            busca_log_txt = st.text_input(
                "Busca Textual (Descrição, Tutor, Microchip ou ID):",
                placeholder="Digite para buscar nos logs...",
                key="filtro_log_busca_txt"
            )

        # 6. Botão Limpar
        with col_f6:
            st.write("")
            st.write("")
            if st.button("Limpar Filtros", key="btn_limpar_log_filtros", width="stretch", type="secondary"):
                for k in ["filtro_log_clinica", "filtro_log_periodo", "filtro_log_entidade", "filtro_log_acao", "filtro_log_busca_txt"]:
                    if k in st.session_state:
                        del st.session_state[k]
                st.rerun()

    # --- Aplicação dos Filtros ---
    df_f = df_logs.copy()

    if filtro_clinica_log:
        df_f = df_f[df_f["nome_clinica"].isin(filtro_clinica_log)]

    if isinstance(periodo_log, (tuple, list)) and len(periodo_log) == 2:
        dt_ini, dt_fim = periodo_log
        df_f = df_f[(df_f["created_at"].dt.date >= dt_ini) & (df_f["created_at"].dt.date <= dt_fim)]

    if filtro_entidade_log:
        ent_lower = [e.lower() for e in filtro_entidade_log]
        df_f = df_f[df_f["tipo_entidade"].astype(str).str.lower().isin(ent_lower)]

    if filtro_acao_log:
        acoes_normalizadas = [a.lower().replace(" ", "_") for a in filtro_acao_log]
        df_f = df_f[df_f["acao"].astype(str).str.lower().isin(acoes_normalizadas)]

    if busca_log_txt and busca_log_txt.strip():
        t = busca_log_txt.strip().lower()
        t_limpo = re.sub(r"[^\w\d]", "", t)

        def match_log(row):
            for col in ["descricao", "nome_clinica", "cnpj_clinica", "usuario_email", "referencia_id", "tipo_entidade", "acao"]:
                if col in row and pd.notna(row[col]):
                    val = str(row[col]).lower()
                    if t in val or (t_limpo and t_limpo in re.sub(r"[^\w\d]", "", val)):
                        return True
            return False

        df_f = df_f[df_f.apply(match_log, axis=1)]

    # --- KPIs de Auditoria ---
    total_logs = len(df_f)
    total_alteracoes = len(df_f[df_f["acao"].isin(["alteracao", "exclusao", "estorno"])])
    total_lotes_acoes = len(df_f[df_f["tipo_entidade"].isin(["lote", "parecer"])])
    total_retif = len(df_f[df_f["tipo_entidade"] == "retificacao"])

    col_k1, col_k2, col_k3, col_k4 = st.columns(4)
    with col_k1:
        st.metric("Total de Eventos", total_logs)
    with col_k2:
        st.metric("Alterações / Exclusões", total_alteracoes)
    with col_k3:
        st.metric("Lotes e Pareceres", total_lotes_acoes)
    with col_k4:
        st.metric("Retificações", total_retif)

    st.divider()

    col_sub, col_exp = st.columns([2.5, 1])
    with col_sub:
        st.markdown(f"#### Eventos Registrados ({total_logs})")

    with col_exp:
        if not df_f.empty:
            csv_logs = df_f.to_csv(index=False, sep=";", encoding="utf-8-sig")
            st.download_button(
                label="Exportar Auditoria (CSV)",
                data=csv_logs,
                file_name=f"historico_auditoria_sepan_{date.today().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                width="stretch",
                type="primary",
                key="btn_export_csv_logs"
            )

    if df_f.empty:
        st.warning("Nenhum registro de auditoria encontrado com os filtros selecionados.")
    else:
        df_show = df_f.copy()
        if "created_at" in df_show.columns:
            df_show["data_hora"] = df_show["created_at"].dt.strftime("%d/%m/%Y %H:%M:%S")
        if "acao" in df_show.columns:
            df_show["acao_view"] = df_show["acao"].apply(lambda a: str(a).replace("_", " ").title())
        if "tipo_entidade" in df_show.columns:
            df_show["tipo_entidade"] = df_show["tipo_entidade"].apply(lambda e: str(e).capitalize())
        if "referencia_id" in df_show.columns:
            df_show["referencia_id"] = df_show["referencia_id"].apply(lambda r: str(r)[:8] if pd.notna(r) and str(r).strip() else "-")

        cols_map = {
            "data_hora": "Data e Hora",
            "nome_clinica": "Clínica",
            "cnpj_clinica": "CNPJ",
            "tipo_entidade": "Entidade",
            "acao_view": "Ação",
            "usuario_email": "Usuário / Responsável",
            "descricao": "Descrição do Evento",
            "referencia_id": "ID Ref."
        }
        cols_disp = [c for c in cols_map.keys() if c in df_show.columns]
        df_show = df_show[cols_disp].rename(columns=cols_map)

        st.dataframe(df_show, width="stretch", hide_index=True)
