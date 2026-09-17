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
from datetime import datetime, date
from supabase import Client
from gerador_pdf import gerar_pdf_anexo_v, gerar_pdf_parecer_sepan


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

    tab_lotes, tab_auditoria = st.tabs([
        "Prestações de Contas (Lotes)",
        "Auditoria de Atendimentos"
    ])

    with tab_lotes:
        _render_tab_lotes(supabase)

    with tab_auditoria:
        _render_tab_auditoria(supabase)


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
    valor_pendente = df_lotes[df_lotes["status"].isin(["Enviado para Análise", "Apta com Necessidade de Saneamento"])]["valor_total"].sum()

    col_k1, col_k2, col_k3 = st.columns(3)
    with col_k1:
        st.metric("Lotes Pendentes de Análise", pendentes_count)
    with col_k2:
        st.metric("Lotes Homologados", aprovados_count)
    with col_k3:
        st.metric(
            "Valor em Análise",
            f"R$ {valor_pendente:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        )

    st.divider()

    lotes_dict = {}
    lote_options = []

    for _, row in df_lotes.iterrows():
        lote_id = row["id"]
        status = row.get("status", "Enviado para Análise")
        nome_c = row.get("nome_clinica") or row.get("cnpj_clinica")
        mes = row.get("mes_referencia", "")
        valor = float(row.get("valor_total", 0.0))
        label = f"[{status}] {nome_c} | Competência: {mes} | R$ {valor:,.2f} (Lote: {str(lote_id)[:8]})"
        
        lotes_dict[label] = row
        lote_options.append(label)

    col_sel, _ = st.columns([2, 1])
    with col_sel:
        escolha_lote = st.selectbox(
            "Selecione o Lote para Análise:",
            options=lote_options,
            index=0
        )

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

    with st.container(border=True):
        st.markdown(f"**Lote: {nome_clinica} ({mes_ref})**")
        
        col_d1, col_d2, col_d3, col_d4 = st.columns(4)
        with col_d1:
            st.write(f"**CNPJ:** `{cnpj_clinica}`")
        with col_d2:
            st.write(f"**Procedimentos:** `{total_proc}`")
        with col_d3:
            st.write(f"**Valor Faturado:** `R$ {valor_total:,.2f}`")
        with col_d4:
            st.write(f"**Status Atual:** `{status_atual}`")

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
            cols_exibir = [c for c in cols_map.keys() if c in df_itens.columns]
            df_itens_view = df_itens[cols_exibir].copy()
            df_itens_view["valor_transacao"] = df_itens_view["valor_transacao"].apply(
                lambda v: f"R$ {float(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            )
            df_itens_view = df_itens_view.rename(columns=cols_map)
            st.dataframe(df_itens_view, width="stretch", hide_index=True)

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

    st.markdown("#### Parecer da Comissão de Gestão")

    PARECERES_OPCOES = [
        "Aprovada",
        "Aprovada com Ressalvas",
        "Apta com Necessidade de Saneamento",
        "Não Aprovada"
    ]

    default_parecer_idx = (
        PARECERES_OPCOES.index(status_atual)
        if status_atual in PARECERES_OPCOES
        else 0
    )

    with st.form(key=f"form_decisao_{lote_id}"):
        st.markdown("##### 5. Monitoramento dos Cadastros no CRIA")
        col_cria1, col_cria2 = st.columns([1, 2])
        with col_cria1:
            val_cria_init = int(selected_row.get("qtd_cria") if pd.notna(selected_row.get("qtd_cria")) else total_proc)
            qtd_cria = st.number_input(
                "Quantidade de animais cadastrados no CRIA:",
                min_value=0,
                step=1,
                value=val_cria_init
            )
        with col_cria2:
            inconsistencias_cria = st.text_area(
                "Inconsistências ou Divergências Cadastrais:",
                value=str(selected_row.get("inconsistencias_cria") or "") if pd.notna(selected_row.get("inconsistencias_cria")) else "",
                placeholder="Descreva divergências encontradas ou deixe em branco se regular..."
            )

        st.markdown("##### 6 e 7. Pontos de Atenção e Notas Pendentes")
        notas_pendentes = st.text_area(
            "Notas Pendentes de Envio / Pontos de Atenção:",
            value=str(selected_row.get("notas_pendentes") or "") if pd.notna(selected_row.get("notas_pendentes")) else "",
            placeholder="Descreva notas pendentes ou pontos de atenção observados..."
        )

        st.markdown("##### 8. Análise de Conformidade")
        apontamentos = st.text_area(
            "Apontamentos da Fiscalização / Análise de Conformidade:",
            value=str(selected_row.get("apontamentos_comissao") or "") if pd.notna(selected_row.get("apontamentos_comissao")) else "",
            placeholder="Descreva a análise de conformidade dos serviços executados e preços praticados..."
        )

        st.markdown("##### 9. Determinações e Providências")
        providencias = st.text_area(
            "Determinações e Providências:",
            value=str(selected_row.get("providencias") or "") if pd.notna(selected_row.get("providencias")) else "",
            placeholder="Informe as determinações ou providências a serem adotadas pela clínica..."
        )

        st.markdown("##### 10. Parecer Final")
        col_p1, _ = st.columns([1.5, 1])
        with col_p1:
            novo_parecer = st.selectbox(
                "Parecer Final:",
                options=PARECERES_OPCOES,
                index=default_parecer_idx
            )

        submit_decisao = st.form_submit_button("Salvar Parecer e Fiscalização", width="stretch", type="primary")

        if submit_decisao:
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

        col_sei, col_mem = st.columns([1.2, 1.2])
        with col_sei:
            processo_sei = st.text_input(
                "Número do Processo SEI:",
                placeholder="00000-00000000/0000-00",
                key=f"sei_{lote_id}",
                help="Informe o número do processo SEI correspondente para constar no cabeçalho do documento."
            )

        user_meta = getattr(st.session_state.get("user"), "user_metadata", {}) or {} if "user" in st.session_state and st.session_state.user else {}
        membro_padrao = (
            user_meta.get("nome")
            or user_meta.get("name")
            or getattr(st.session_state.get("user"), "email", "Membro da Comissão de Gestão")
        )

        with col_mem:
            membro_comissao = st.text_input(
                "Membro Responsável pela Análise:",
                value=membro_padrao,
                key=f"mem_{lote_id}",
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
            
            st.download_button(
                label="Baixar Parecer Técnico (PDF)",
                data=pdf_parecer_bytes,
                file_name=f"Parecer_SEPAN_{cnpj_limpo}.pdf",
                mime="application/pdf",
                key=f"pdf_parecer_{lote_id}",
                width="stretch",
                type="primary",
                help="Gera o Relatório de Prestação de Contas e Fiscalização da SEPAN formatado para o SEI."
            )
        except Exception as err_parecer:
            st.error(f"Erro ao gerar relatório técnico do parecer: {str(err_parecer)}")


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

    with st.expander("Filtros de Pesquisa", expanded=True):
        col_f1, col_f2, col_f3 = st.columns([1.3, 1.3, 1])

        with col_f1:
            clinicas_disponiveis = sorted(
                [c for c in df_raw["nome_clinica"].dropna().unique().tolist() if str(c).strip()]
            )
            filtro_clinica = st.multiselect(
                "Clínica:",
                options=clinicas_disponiveis,
                placeholder="Todas as clínicas"
            )

        with col_f2:
            min_date = df_raw["data_atendimento"].min().date() if not df_raw.empty else date.today()
            max_date = df_raw["data_atendimento"].max().date() if not df_raw.empty else date.today()
            periodo_selecionado = st.date_input(
                "Período de Atendimento:",
                value=(min_date, max_date),
                format="DD/MM/YYYY"
            )

        with col_f3:
            filtro_especie = st.multiselect(
                "Espécie:",
                options=["Canina", "Felina"],
                placeholder="Todas as espécies"
            )

        filtro_texto = st.text_input(
            "Busca Textual (CPF, Beneficiário, NF-e, Microchip, CNPJ):",
            placeholder="Digite para pesquisar..."
        )

    df_filtered = df_raw.copy()

    if filtro_clinica:
        df_filtered = df_filtered[df_filtered["nome_clinica"].isin(filtro_clinica)]

    if isinstance(periodo_selecionado, (tuple, list)) and len(periodo_selecionado) == 2:
        dt_inicio, dt_fim = periodo_selecionado
        df_filtered = df_filtered[
            (df_filtered["data_atendimento"].dt.date >= dt_inicio) &
            (df_filtered["data_atendimento"].dt.date <= dt_fim)
        ]

    if filtro_especie:
        df_filtered = df_filtered[df_filtered["especie"].isin(filtro_especie)]

    if filtro_texto and filtro_texto.strip():
        termo = filtro_texto.strip()
        colunas_busca = ["nome_clinica", "cnpj_clinica", "cpf_beneficiario", "nome_beneficiario", "nfe_referencia", "numero_microchip"]
        colunas_validas = [col for col in colunas_busca if col in df_filtered.columns]
        if colunas_validas:
            mascara = df_filtered[colunas_validas].astype(str).apply(
                lambda x: x.str.contains(termo, case=False, na=False)
            ).any(axis=1)
            df_filtered = df_filtered[mascara]

    total_proc = len(df_filtered)
    valor_tot = df_filtered["valor_transacao"].sum() if not df_filtered.empty else 0.0
    total_caes = (df_filtered["especie"].str.strip().str.capitalize() == "Canina").sum() if not df_filtered.empty else 0
    total_gatos = (df_filtered["especie"].str.strip().str.capitalize() == "Felina").sum() if not df_filtered.empty else 0

    col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)
    with col_kpi1:
        st.metric("Total de Procedimentos", f"{total_proc:,}".replace(",", "."))
    with col_kpi2:
        st.metric("Valor Total (R$)", f"R$ {valor_tot:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    with col_kpi3:
        st.metric("Cães Castrados", f"{total_caes:,}".replace(",", "."))
    with col_kpi4:
        st.metric("Gatos Castrados", f"{total_gatos:,}".replace(",", "."))

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
        colunas_map = {
            "data_atendimento": "Data",
            "nome_clinica": "Clínica",
            "cnpj_clinica": "CNPJ Clínica",
            "nome_beneficiario": "Beneficiário",
            "cpf_beneficiario": "CPF",
            "especie": "Espécie",
            "sexo": "Sexo",
            "porte": "Porte",
            "numero_microchip": "Microchip",
            "valor_transacao": "Valor (R$)",
            "nfe_referencia": "NF-e",
            "status_validacao": "Status",
        }
        cols_to_show = [col for col in colunas_map.keys() if col in df_display.columns]
        df_display = df_display[cols_to_show].copy()

        if "data_atendimento" in df_display.columns:
            df_display["data_atendimento"] = df_display["data_atendimento"].dt.strftime("%d/%m/%Y")
        if "valor_transacao" in df_display.columns:
            df_display["valor_transacao"] = df_display["valor_transacao"].apply(
                lambda v: f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            )
        df_display = df_display.rename(columns=colunas_map)

        st.dataframe(df_display, width="stretch", hide_index=True)
