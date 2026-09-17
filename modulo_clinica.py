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
from datetime import date
import calendar
from supabase import Client
from validate_docbr import CPF
from auth import is_validacao_ativa
from gerador_pdf import gerar_pdf_anexo_v


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

    st.markdown(f"### Portal da Clínica: {nome_clinica}")
    st.caption(f"Razão Social: {nome_empresarial} | CNPJ: {cnpj} | Programa Cartão Castração - SEPAN")

    tab_insercao, tab_fechamento, tab_historico = st.tabs([
        "Lançamento de Atendimentos",
        "Fechamento de Lote Mensal",
        "Histórico de Lotes"
    ])

    with tab_insercao:
        _render_tab_insercao(supabase, cnpj, nome_clinica)

    with tab_fechamento:
        _render_tab_fechamento(supabase, cnpj, nome_clinica, nome_empresarial)

    with tab_historico:
        _render_tab_historico(supabase, cnpj)


# -----------------------------------------------------------------------------
# ABA 1: Inserção Individual de Atendimentos
# -----------------------------------------------------------------------------
def _render_tab_insercao(supabase: Client, cnpj: str, nome_clinica: str):
    """Lançamento unitário de procedimentos cirúrgicos executados."""
    with st.container(border=True):
        st.markdown("#### Registro de Atendimento")

        with st.form(key="form_cadastro_atendimento", clear_on_submit=True):
            col1, col2, col3 = st.columns([1, 1.2, 1.8])
            with col1:
                data_atendimento = st.date_input(
                    "Data do Atendimento *",
                    value=date.today(),
                    format="DD/MM/YYYY"
                )
            with col2:
                cpf_beneficiario = st.text_input("CPF do Beneficiário *", placeholder="000.000.000-00")
            with col3:
                nome_beneficiario = st.text_input("Nome do Beneficiário *", placeholder="Nome completo do tutor")

            col4, col5, col6, col7 = st.columns([1, 1, 1, 1.2])
            with col4:
                especie = st.selectbox("Espécie *", options=["Canina", "Felina"])
            with col5:
                sexo = st.radio("Sexo *", options=["Macho", "Fêmea"], horizontal=True)
            with col6:
                porte = st.selectbox("Porte *", options=["Pequeno", "Médio", "Grande"])
            with col7:
                numero_microchip = st.text_input("Nº do Microchip *", placeholder="Número do microchip")

            col8, col9 = st.columns([1, 1])
            with col8:
                valor_transacao = st.number_input(
                    "Valor do Procedimento (R$) *",
                    min_value=0.0,
                    value=0.0,
                    step=10.0,
                    format="%.2f"
                )
            with col9:
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
                    st.error(f"Campos obrigatórios não preenchidos: {', '.join(erros)}.")
                else:
                    # Validação matemática de CPF se configurada no sistema
                    if is_validacao_ativa(supabase):
                        if not CPF().validate(cpf_beneficiario.strip()):
                            st.error("CPF do Beneficiário inválido. Verifique os dígitos informados.")
                            return

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
                        "valor_transacao": float(valor_transacao),
                        "nfe_referencia": nfe_referencia.strip(),
                    }

                    with st.spinner("Gravando atendimento..."):
                        try:
                            supabase.table("relacao_transacoes").insert(dados_transacao).execute()
                            st.session_state.lista_conferencia.insert(0, dados_transacao)
                            st.success(f"Atendimento de {nome_beneficiario.strip()} gravado com sucesso.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Falha ao registrar atendimento: {str(e)}")

    st.divider()

    st.markdown("#### Atendimentos Registrados na Sessão")
    if st.session_state.lista_conferencia:
        df_conferencia = pd.DataFrame(st.session_state.lista_conferencia)
        colunas_exibicao = {
            "data_atendimento": "Data",
            "nome_beneficiario": "Beneficiário",
            "especie": "Espécie",
            "valor_transacao": "Valor (R$)",
            "nfe_referencia": "NF-e",
        }
        df_view = df_conferencia[list(colunas_exibicao.keys())].copy()
        df_view["valor_transacao"] = df_view["valor_transacao"].apply(
            lambda v: f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        )
        df_view["data_atendimento"] = pd.to_datetime(df_view["data_atendimento"]).dt.strftime("%d/%m/%Y")
        df_view = df_view.rename(columns=colunas_exibicao)

        st.dataframe(df_view, width="stretch", hide_index=True)
    else:
        st.info("Nenhum atendimento registrado nesta sessão.")


# -----------------------------------------------------------------------------
# ABA 2: Fechamento Mensal de Lote e Exclusão de Itens
# -----------------------------------------------------------------------------
def _render_tab_fechamento(supabase: Client, cnpj: str, nome_clinica: str, nome_empresarial: str = ""):
    """Consolidação mensal, visualização e exclusão de transações abertas."""
    st.markdown("#### Fechamento de Prestação de Contas")
    st.caption("Consolidação dos procedimentos executados para envio formal à SEPAN.")

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

    col_r1, col_r2 = st.columns(2)
    with col_r1:
        st.metric("Procedimentos Pendentes de Envio", total_abertas)
    with col_r2:
        st.metric(
            "Valor Total do Período",
            f"R$ {valor_total_aberto:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        )

    if total_abertas == 0:
        st.info(f"Não há atendimentos avulsos pendentes de fechamento para {mes_rotulo}.")
        return

    # Visualização prévia dos atendimentos abertos
    with st.expander(f"Visualizar os {total_abertas} atendimentos deste período", expanded=True):
        df_preview = pd.DataFrame(transacoes_abertas)
        cols_preview = ["data_atendimento", "nome_beneficiario", "cpf_beneficiario", "especie", "numero_microchip", "valor_transacao", "nfe_referencia"]
        cols_presentes = [c for c in cols_preview if c in df_preview.columns]
        st.dataframe(df_preview[cols_presentes], width="stretch", hide_index=True)

        # ---------------------------------------------------------------------
        # Funcionalidade de Exclusão de Registro Aberto
        # ---------------------------------------------------------------------
        st.markdown("##### Excluir Atendimento Incorreto")
        st.caption("Caso algum atendimento deste período tenha sido lançado com erro, selecione-o para exclusão:")

        opcoes_exclusao = {
            f"{t.get('data_atendimento', '')} | {t.get('nome_beneficiario', '')} (Microchip: {t.get('numero_microchip', '-')}) - ID: {str(t.get('id', ''))[:8]}": t.get("id")
            for t in transacoes_abertas
        }

        col_exc1, col_exc2 = st.columns([3, 1])
        with col_exc1:
            item_excluir_label = st.selectbox(
                "Selecione o registro para exclusão:",
                options=list(opcoes_exclusao.keys()),
                key=f"sel_exc_{mes_codigo}",
                label_visibility="collapsed"
            )
        with col_exc2:
            if st.button("Excluir Registro", key=f"btn_exc_{mes_codigo}", width="stretch", type="secondary"):
                id_para_excluir = opcoes_exclusao[item_excluir_label]
                try:
                    supabase.table("relacao_transacoes").delete().eq("id", id_para_excluir).execute()
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
            placeholder="Descreva eventuais intercorrências ou informe 'Sem intercorrências no período'."
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
                        st.error("CPF do Representante Legal inválido. Verifique os dígitos informados.")
                        st.stop()

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

                        st.success(f"Prestação de contas ({mes_codigo}) enviada com sucesso para a SEPAN (Lote ID: {lote_id[:8]}).")
                        st.rerun()

                    except Exception as ex:
                        st.error(f"Falha ao enviar lote: {str(ex)}")


# -----------------------------------------------------------------------------
# ABA 3: Histórico de Lotes e Estorno para Saneamento
# -----------------------------------------------------------------------------
def _render_tab_historico(supabase: Client, cnpj: str):
    """Consulta de lotes e estorno de lotes devolvidos para saneamento."""
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

        with st.container(border=True):
            col_h1, col_h2, col_h3, col_h4 = st.columns([1.5, 1.2, 1, 1.3])
            with col_h1:
                st.markdown(f"**Referência:** {mes_ref}")
                st.caption(f"ID: {lote_id[:8]} | Envio: {data_envio}")
            with col_h2:
                st.write(f"Procedimentos: {total_proc}")
                st.write(f"Valor: R$ {valor_tot:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
            with col_h3:
                st.markdown(f"**Status:** `{status}`")
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

            parecer = lote.get("parecer_comissao")
            apontamentos = lote.get("apontamentos_comissao")
            if parecer or apontamentos:
                st.divider()
                if status == "Apta com Necessidade de Saneamento":
                    st.warning(f"**Parecer:** {parecer or status}\n\n**Apontamentos:** {apontamentos}")

                    # Botão de Estorno para permitir correção e novo fechamento
                    if st.button("Estornar Lote para Correção", key=f"estorno_{lote_id}", width="stretch", type="primary"):
                        with st.spinner("Estornando lote..."):
                            try:
                                # 1. Desvincula os atendimentos para que fiquem abertos novamente (lote_id = null)
                                supabase.table("relacao_transacoes").update({"lote_id": None}).eq("lote_id", lote_id).execute()

                                # 2. Atualiza o status do lote
                                supabase.table("lotes_prestacao").update({"status": "Retificado pela Clínica"}).eq("id", lote_id).execute()

                                st.success("Lote estornado. Os atendimentos voltaram para a aba de Fechamento onde podem ser excluídos ou editados.")
                                st.rerun()
                            except Exception as ex:
                                st.error(f"Erro ao estornar lote: {str(ex)}")

                elif status == "Aprovada":
                    st.success(f"**Parecer:** {parecer or status}\n\n{apontamentos or 'Homologado sem ressalvas.'}")
                elif status == "Aprovada com Ressalvas":
                    st.info(f"**Parecer:** {parecer or status}\n\n**Observações:** {apontamentos}")
                else:
                    st.error(f"**Parecer:** {parecer or status}\n\n**Motivação:** {apontamentos}")
