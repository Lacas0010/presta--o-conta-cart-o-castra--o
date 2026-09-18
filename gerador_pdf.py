"""
=============================================================================
SISTEMA DE FISCALIZAÇÃO E PRESTAÇÃO DE CONTAS - CARTÃO CASTRAÇÃO (SEPAN)
Módulo Gerador de PDFs Oficiais: gerador_pdf.py
=============================================================================
Responsável por gerar:
1. "ANEXO V - MODELO DE RELATÓRIO MENSAL DE PRESTAÇÃO DE CONTAS" (Clínica)
2. "RELATÓRIO DE PRESTAÇÃO DE CONTAS E FISCALIZAÇÃO" (Comissão SEPAN)
utilizando a biblioteca fpdf2.
=============================================================================
"""

import re
from fpdf import FPDF
from datetime import date


class PDFBaseSEPAN(FPDF):
    """Classe base para documentos institucionais da SEPAN."""

    def __init__(self, doc_tipo="Anexo V - Modelo de Relatório Mensal de Prestação de Contas"):
        super().__init__(orientation="P", unit="mm", format="A4")
        self.doc_tipo = doc_tipo

    def header(self):
        self.set_font("Helvetica", "B", 8.5)
        self.set_text_color(50, 50, 50)
        self.cell(0, 4, "GOVERNO DO DISTRITO FEDERAL - SECRETARIA EXTRAORDINÁRIA DE PROTEÇÃO ANIMAL - SEPAN", ln=True, align="C")
        self.set_font("Helvetica", "", 8)
        self.cell(0, 4, "PROGRAMA CARTÃO CASTRAÇÃO - FISCALIZAÇÃO E PRESTAÇÃO DE CONTAS", ln=True, align="C")
        self.set_draw_color(180, 180, 180)
        self.line(10, 19, 200, 19)
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_draw_color(200, 200, 200)
        self.line(10, self.get_y(), 200, self.get_y())
        self.set_font("Helvetica", "", 8)
        self.set_text_color(120, 120, 120)
        self.cell(120, 8, self.doc_tipo, align="L")
        self.cell(70, 8, f"Página {self.page_no()}/{{nb}}", align="R")


def _obter_campo(dados: dict, *chaves, padrao: str = "Não informado") -> str:
    """Extrai com segurança o primeiro valor válido e não vazio, tratando None e NaN."""
    if not isinstance(dados, dict):
        return padrao
    for c in chaves:
        val = dados.get(c)
        if val is not None:
            if isinstance(val, float) and (val != val):
                continue
            val_str = str(val).strip()
            if val_str and val_str.lower() not in ["none", "nan", "null", "nat"]:
                return val_str
    return padrao


# =============================================================================
# 1. GERADOR DO ANEXO V (CLÍNICA CREDENCIADA)
# =============================================================================
def gerar_pdf_anexo_v(dados_lote: dict, lista_transacoes: list[dict]) -> bytes:
    """
    Gera o PDF oficial do Anexo V contendo identificação completa, resumo sintético,
    relação detalhada de transações (com porte), documentação e declaração do representante legal.
    """
    pdf = PDFBaseSEPAN(doc_tipo="Relatório Mensal de Prestação de Contas - Cartão Castração")
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.set_margins(10, 22, 10)
    pdf.add_page()

    # Título Principal do Documento
    pdf.set_font("Helvetica", "B", 10.5)
    pdf.set_text_color(20, 20, 20)
    pdf.cell(0, 6, "RELATÓRIO MENSAL DE PRESTAÇÃO DE CONTAS - CARTÃO CASTRAÇÃO", ln=True, align="C")
    pdf.ln(3)

    # 1. Identificação da Empresa Credenciada
    nome_empresarial = _obter_campo(dados_lote, "nome_empresarial", "razao_social", "nome_clinica", padrao="Clínica Credenciada")
    nome_fantasia = _obter_campo(dados_lote, "nome_fantasia", "nome_clinica", padrao=nome_empresarial)
    endereco_empresa = _obter_campo(dados_lote, "endereco_clinica", padrao="Não informado")
    cnpj_empresa = _obter_campo(dados_lote, "cnpj_clinica", padrao="Não informado")
    nome_responsavel = _obter_campo(dados_lote, "nome_representante", padrao="Não informado")
    telefone_empresa = _obter_campo(dados_lote, "telefone_clinica", padrao="Não informado")
    email_empresa = _obter_campo(dados_lote, "email_clinica", "email", "email_contato", padrao="Não informado")
    mes_referencia = _obter_campo(dados_lote, "mes_referencia", padrao="Não informado")

    pdf.set_fill_color(240, 240, 240)
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(0, 6, "1. IDENTIFICAÇÃO DA EMPRESA CREDENCIADA", ln=True, fill=True)
    pdf.ln(1)

    pdf.set_font("Helvetica", "", 8.5)
    col_label_w = 62
    col_val_w = 128

    dados_clinica_anexo = [
        ("Nome Empresarial:", nome_empresarial),
        ("Nome Fantasia:", nome_fantasia),
        ("Endereço Completo:", endereco_empresa),
        ("CNPJ:", cnpj_empresa),
        ("Nome do Responsável pela Empresa:", nome_responsavel),
        ("Telefones de Contato:", telefone_empresa),
        ("E-mail para Contato:", email_empresa),
    ]

    for label, val in dados_clinica_anexo:
        pdf.cell(col_label_w, 5, f" {label}", border=1)
        pdf.cell(col_val_w, 5, f" {val}", border=1, ln=True)

    pdf.ln(3)

    # 2. Período de Referência
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(0, 6, "2. PERÍODO DE REFERÊNCIA DA PRESTAÇÃO DE CONTAS", ln=True, fill=True)
    pdf.ln(1)

    pdf.set_font("Helvetica", "", 8.5)
    pdf.cell(45, 5, "Mês / Ano de Competência:", border=1)
    pdf.cell(145, 5, f" {mes_referencia}", border=1, ln=True)
    pdf.ln(3)

    # 3. Resumo Executivo
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(0, 6, "3. RESUMO EXECUTIVO - SERVIÇO DE CASTRAÇÃO (CARTÃO CASTRAÇÃO)", ln=True, fill=True)
    pdf.ln(1)

    total_proc = len(lista_transacoes)
    caes_machos = sum(1 for t in lista_transacoes if str(t.get("especie", "")).lower() == "canina" and str(t.get("sexo", "")).lower() == "macho")
    caes_femeas = sum(1 for t in lista_transacoes if str(t.get("especie", "")).lower() == "canina" and str(t.get("sexo", "")).lower() in ["fêmea", "femea"])
    gatos_machos = sum(1 for t in lista_transacoes if str(t.get("especie", "")).lower() == "felina" and str(t.get("sexo", "")).lower() == "macho")
    gatos_femeas = sum(1 for t in lista_transacoes if str(t.get("especie", "")).lower() == "felina" and str(t.get("sexo", "")).lower() in ["fêmea", "femea"])
    
    porte_pequeno = sum(1 for t in lista_transacoes if str(t.get("porte", "")).lower() == "pequeno")
    porte_medio = sum(1 for t in lista_transacoes if str(t.get("porte", "")).lower() in ["médio", "medio"])
    porte_grande = sum(1 for t in lista_transacoes if str(t.get("porte", "")).lower() == "grande")

    microchips_count = sum(1 for t in lista_transacoes if t.get("numero_microchip"))
    valor_total_soma = sum(float(t.get("valor_transacao", 0)) for t in lista_transacoes)

    pdf.set_font("Helvetica", "B", 8)
    pdf.cell(0, 5, "3.1. Serviços de Castração e Microchipagem Realizados no Período:", ln=True)

    pdf.set_font("Helvetica", "", 8)
    col_w1, col_w2 = 120, 70
    
    itens_sinteticos = [
        ("Total de Procedimentos Realizados", f"{total_proc}"),
        ("Cães - Machos", f"{caes_machos}"),
        ("Cães - Fêmeas", f"{caes_femeas}"),
        ("Gatos - Machos", f"{gatos_machos}"),
        ("Gatos - Fêmeas", f"{gatos_femeas}"),
        ("Animais de Porte Pequeno", f"{porte_pequeno}"),
        ("Animais de Porte Médio", f"{porte_medio}"),
        ("Animais de Porte Grande", f"{porte_grande}"),
        ("Microchips Implantados", f"{microchips_count}"),
        ("Valor Total Faturado (R$)", f"R$ {valor_total_soma:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")),
    ]

    for label, val in itens_sinteticos:
        pdf.cell(col_w1, 4.5, f"  {label}", border=1)
        pdf.cell(col_w2, 4.5, f"  {val}", border=1, ln=True, align="R")

    pdf.ln(2)

    obitos = dados_lote.get("obitos_relato") or "Sem intercorrências no período."
    reclamacoes = dados_lote.get("reclamacoes_relato") or "Nenhuma reclamação registrada no período."

    pdf.set_font("Helvetica", "B", 8)
    pdf.cell(0, 4.5, "3.2. Ocorrências e Relatos do Período:", ln=True)
    pdf.cell(0, 4, "- Óbitos e Intercorrências Cirúrgicas:", ln=True)
    pdf.set_font("Helvetica", "", 8)
    pdf.multi_cell(0, 4, f"  {obitos}")
    pdf.ln(1.5)

    pdf.set_font("Helvetica", "B", 8)
    pdf.cell(0, 4, "- Reclamações de Beneficiários:", ln=True)
    pdf.set_font("Helvetica", "", 8)
    pdf.multi_cell(0, 4, f"  {reclamacoes}")
    pdf.ln(3)

    # 4. Relação Detalhada de Transações (Com Coluna Porte)
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(0, 6, "4. RESUMO EXECUTIVO - RELAÇÃO DETALHADA DE TRANSAÇÕES", ln=True, fill=True)
    pdf.ln(1)

    # Larguras totais: 6+16+23+38+13+12+14+26+18+24 = 190 mm (A4 210mm - 2x10mm)
    col_widths = {
        "num": 6,
        "data": 16,
        "cpf": 23,
        "nome": 38,
        "esp": 13,
        "sexo": 12,
        "porte": 14,
        "micro": 26,
        "val": 18,
        "nfe": 24
    }

    pdf.set_font("Helvetica", "B", 7)
    pdf.set_fill_color(225, 235, 245)
    pdf.cell(col_widths["num"], 6, "Nº", border=1, align="C", fill=True)
    pdf.cell(col_widths["data"], 6, "Data", border=1, align="C", fill=True)
    pdf.cell(col_widths["cpf"], 6, "CPF", border=1, align="C", fill=True)
    pdf.cell(col_widths["nome"], 6, "Beneficiário", border=1, align="L", fill=True)
    pdf.cell(col_widths["esp"], 6, "Esp.", border=1, align="C", fill=True)
    pdf.cell(col_widths["sexo"], 6, "Sexo", border=1, align="C", fill=True)
    pdf.cell(col_widths["porte"], 6, "Porte", border=1, align="C", fill=True)
    pdf.cell(col_widths["micro"], 6, "Microchip", border=1, align="C", fill=True)
    pdf.cell(col_widths["val"], 6, "Valor (R$)", border=1, align="R", fill=True)
    pdf.cell(col_widths["nfe"], 6, "NF-e", border=1, align="C", fill=True, ln=True)

    pdf.set_font("Helvetica", "", 7)
    for idx, t in enumerate(lista_transacoes, 1):
        dt_str = str(t.get("data_atendimento", ""))[:10]
        if "-" in dt_str:
            p = dt_str.split("-")
            if len(p) == 3:
                dt_str = f"{p[2]}/{p[1]}/{p[0]}"

        cpf_val = str(t.get("cpf_beneficiario", ""))
        nome_val = str(t.get("nome_beneficiario", ""))[:22]
        esp_val = str(t.get("especie", ""))[:6]
        sexo_val = str(t.get("sexo", ""))[:5]
        porte_val = str(t.get("porte", ""))[:6]
        micro_val = str(t.get("numero_microchip", ""))[:15]
        val_num = float(t.get("valor_transacao", 0))
        val_str = f"{val_num:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        nfe_val = str(t.get("nfe_referencia", ""))[:14]

        pdf.cell(col_widths["num"], 5, str(idx), border=1, align="C")
        pdf.cell(col_widths["data"], 5, dt_str, border=1, align="C")
        pdf.cell(col_widths["cpf"], 5, cpf_val, border=1, align="C")
        pdf.cell(col_widths["nome"], 5, f" {nome_val}", border=1, align="L")
        pdf.cell(col_widths["esp"], 5, esp_val, border=1, align="C")
        pdf.cell(col_widths["sexo"], 5, sexo_val, border=1, align="C")
        pdf.cell(col_widths["porte"], 5, porte_val, border=1, align="C")
        pdf.cell(col_widths["micro"], 5, micro_val, border=1, align="C")
        pdf.cell(col_widths["val"], 5, val_str, border=1, align="R")
        pdf.cell(col_widths["nfe"], 5, nfe_val, border=1, align="C", ln=True)

    pdf.ln(3)

    # 5. Documentação Anexa
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(0, 6, "5. DOCUMENTAÇÃO ANEXA", ln=True, fill=True)
    pdf.ln(1)
    pdf.set_font("Helvetica", "", 8)
    checklist_docs = [
        "[ X ] Cópias digitalizadas de todas as Notas Fiscais de Serviço (NFS-e) emitidas no período.",
        "[ X ] Comprovantes de registro de todos os microchips implantados no sistema informatizado da SEPAN.",
        "[ X ] Comprovantes de cadastro no sistema fornecido pela SEPAN.",
        "[   ] Documentação complementar solicitada pela SEPAN.",
    ]
    for doc in checklist_docs:
        pdf.cell(0, 4.5, f"  {doc}", ln=True)
    pdf.ln(3)

    # 6. Declaração de Responsabilidade
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(0, 6, "6. DECLARAÇÃO DE RESPONSABILIDADE", ln=True, fill=True)
    pdf.ln(1)

    nome_representante = dados_lote.get("nome_representante") or "Representante Legal"
    cpf_representante = dados_lote.get("cpf_representante") or "Não informado"

    texto_declaracao = (
        f"Eu, {nome_representante}, CPF nº {cpf_representante}, na qualidade de representante legal da empresa {nome_empresarial}, CNPJ nº {cnpj_empresa}, "
        "DECLARO, sob as penas da lei, para os fins de prestação de contas junto à Secretaria Extraordinária de Proteção "
        "Animal (SEPAN) referente ao Programa Cartão Castração:\n\n"
        "- Que todas as informações e documentos (incluindo cópias das Notas Fiscais) apresentados neste Relatório de Prestação "
        "de Contas são verdadeiros, precisos e completos, refletindo fielmente as transações realizadas com o Cartão no período de referência.\n"
        "- Que a empresa cumpriu, em todas as transações listadas:\n"
        "  a) A obrigatoriedade de emissão de Nota Fiscal devidamente discriminada por itens, em nome e CPF do beneficiário titular do cartão;\n"
        "  b) A prática de preços compatíveis com os valores pactuados, não realizando cobrança de sobrepreço ou valores adicionais aos beneficiários;\n"
        "  c) Todas as demais obrigações e vedações impostas aos estabelecimentos credenciados.\n"
        "- Declaro, ainda, que toda a documentação comprobatória está disponível para verificação e auditoria a qualquer momento."
    )

    pdf.set_font("Helvetica", "", 8)
    pdf.multi_cell(0, 3.8, texto_declaracao)
    pdf.ln(6)

    hoje = date.today()
    meses_pt = ["", "janeiro", "fevereiro", "março", "abril", "maio", "junho",
                "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]
    data_extenso = f"Brasília/DF, {hoje.day:02d} de {meses_pt[hoje.month]} de {hoje.year}."

    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 5, data_extenso, ln=True, align="R")
    pdf.ln(10)

    pdf.cell(0, 4, "_" * 65, ln=True, align="C")
    pdf.set_font("Helvetica", "B", 8.5)
    pdf.cell(0, 4, f"{nome_representante}", ln=True, align="C")
    pdf.set_font("Helvetica", "", 8)
    pdf.cell(0, 4, f"CPF: {cpf_representante} - Representante Legal", ln=True, align="C")
    pdf.cell(0, 4, f"{nome_empresarial} (CNPJ: {cnpj_empresa})", ln=True, align="C")

    return bytes(pdf.output())


# =============================================================================
# 2. GERADOR DO RELATÓRIO TÉCNICO DE FISCALIZAÇÃO (COMISSÃO SEPAN)
# =============================================================================
def gerar_pdf_parecer_sepan(
    dados_lote: dict,
    processo_sei: str,
    membro_comissao: str,
    lista_transacoes: list[dict] = None
) -> bytes:
    """
    Gera o PDF oficial do "Relatório de Prestação de Contas e Fiscalização"
    emitido pela Comissão de Gestão de Contratos da SEPAN com seções 1 a 10 detalhadas.
    """
    pdf = PDFBaseSEPAN(doc_tipo="Relatório de Prestação de Contas e Fiscalização - SEPAN")
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.set_margins(10, 22, 10)
    pdf.add_page()

    # Título Principal do Parecer
    pdf.set_text_color(20, 20, 20)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 5, "RELATÓRIO DE PRESTAÇÃO DE CONTAS E FISCALIZAÇÃO - CARTÃO CASTRAÇÃO", ln=True, align="C")
    pdf.ln(4)

    # 1. IDENTIFICAÇÃO
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(0, 6, "1- IDENTIFICAÇÃO", ln=True, fill=True)
    pdf.ln(1)

    proc_sei_val = processo_sei.strip() if processo_sei and processo_sei.strip() else "Não informado"
    nome_clinica = _obter_campo(dados_lote, "nome_empresarial", "nome_clinica", padrao="Clínica Credenciada")
    cnpj_clinica = _obter_campo(dados_lote, "cnpj_clinica", padrao="Não informado")
    mes_ref = _obter_campo(dados_lote, "mes_referencia", padrao="Não informado")
    membro_val = membro_comissao.strip() if membro_comissao and membro_comissao.strip() else "Comissão de Gestão"
    hoje = date.today()
    data_emissao = hoje.strftime("%d/%m/%Y")

    pdf.set_font("Helvetica", "", 8.5)
    dados_identificacao = [
        ("Processo SEI:", proc_sei_val),
        ("Clínica credenciada (razão social):", nome_clinica),
        ("CNPJ:", cnpj_clinica),
        ("Período analisado:", mes_ref),
        ("Membro da comissão responsável:", membro_val),
        ("Data de emissão:", data_emissao),
    ]

    for label, val in dados_identificacao:
        pdf.cell(65, 5, f" {label}", border=1)
        pdf.cell(125, 5, f" {val}", border=1, ln=True)

    pdf.ln(3)

    # 2. INTRODUÇÃO
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(0, 6, "2- INTRODUÇÃO", ln=True, fill=True)
    pdf.ln(1)

    texto_intro = (
        f"O presente relatório analítico de prestação de contas tem por finalidade apresentar a análise da "
        f"execução operacional e financeira dos serviços prestados pela empresa credenciada no âmbito do Programa de "
        f"Apoio à Proteção Animal, na modalidade Cartão Castração, referente ao período de {mes_ref}.\n\n"
        "Considerando que o benefício financeiro é disponibilizado diretamente ao cidadão beneficiário do "
        "programa, a presente análise possui caráter não apenas contábil, mas também fiscalizatória e de controle da "
        "execução contratual, objetivando verificar a conformidade dos serviços executados com as condições "
        "estabelecidas no Termo de Referência, anexo ao Edital de Credenciamento, e demais normativos aplicáveis.\n\n"
        "A apuração realizada busca assegurar:\n"
        "- a correta utilização do benefício exclusivamente para o procedimento de castração;\n"
        "- a observância dos valores máximos pactuados;\n"
        "- a realização da microchipagem e cadastro dos animais no Cadastro de Identificação Animal (CRIA) sem cobrança adicional;\n"
        "- a compatibilidade entre documentação fiscal, registros administrativos e informações cadastradas no sistema."
    )

    pdf.set_font("Helvetica", "", 8)
    pdf.multi_cell(0, 3.8, texto_intro)
    pdf.ln(3)

    # 3. RESUMO EXECUTIVO
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(0, 6, "3- RESUMO EXECUTIVO", ln=True, fill=True)
    pdf.ln(1)

    total_proc = int(dados_lote.get("total_procedimentos", 0))
    val_tot = float(dados_lote.get("valor_total", 0.0))
    val_tot_str = f"R$ {val_tot:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    
    qtd_cria_val = dados_lote.get("qtd_cria")
    if qtd_cria_val is None or (isinstance(qtd_cria_val, str) and not str(qtd_cria_val).strip()):
        qtd_cria_val = total_proc
    else:
        try:
            qtd_cria_val = int(qtd_cria_val)
        except (ValueError, TypeError):
            qtd_cria_val = total_proc

    inconsistencias_texto = dados_lote.get("inconsistencias_cria")
    possui_inconsistencias = "Sim" if inconsistencias_texto and str(inconsistencias_texto).strip() else "Não"

    pdf.set_font("Helvetica", "B", 8)
    pdf.cell(115, 5, " Indicador", border=1, fill=True)
    pdf.cell(75, 5, " Quantidade / Valor", border=1, ln=True, fill=True, align="R")

    pdf.set_font("Helvetica", "", 8)
    pdf.cell(115, 5, " Castrações realizadas no período", border=1)
    pdf.cell(75, 5, f" {total_proc}", border=1, ln=True, align="R")

    pdf.cell(115, 5, " Valor total movimentado no período", border=1)
    pdf.cell(75, 5, f" {val_tot_str}", border=1, ln=True, align="R")

    pdf.cell(115, 5, " Animais cadastrados no CRIA", border=1)
    pdf.cell(75, 5, f" {qtd_cria_val}", border=1, ln=True, align="R")

    pdf.cell(115, 5, " Inconsistências Identificadas", border=1)
    pdf.cell(75, 5, f" {possui_inconsistencias}", border=1, ln=True, align="R")
    pdf.ln(3)

    # 4. MOVIMENTAÇÃO FINANCEIRA E TRANSAÇÕES
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(0, 6, "4- MOVIMENTAÇÃO FINANCEIRA E TRANSAÇÕES", ln=True, fill=True)
    pdf.ln(1)

    min_nfe, max_nfe = "Não informado", "Não informado"
    if lista_transacoes:
        nf_list = [str(t.get("nfe_referencia", "")).strip() for t in lista_transacoes if str(t.get("nfe_referencia", "")).strip()]
        if nf_list:
            def extrair_numero_nf(val):
                nums = re.findall(r"\d+", val)
                return int(nums[0]) if nums else 0

            try:
                nf_ordenadas = sorted(nf_list, key=extrair_numero_nf)
                min_nfe = nf_ordenadas[0]
                max_nfe = nf_ordenadas[-1]
            except Exception:
                min_nfe = min(nf_list)
                max_nfe = max(nf_list)

    texto_mov = (
        f"As transações realizadas no período totalizaram o montante de {val_tot_str}, conforme apuração efetuada "
        f"a partir dos documentos e relatórios apresentados pela clínica credenciada. "
        f"As notas fiscais emitidas no período compreendem a numeração de {min_nfe} a {max_nfe}. "
        "Os procedimentos realizados observaram os valores máximos estabelecidos no Termo de Referência "
        "e foram acobertados pela documentação fiscal correspondente emitida para cada beneficiário atendido."
    )
    pdf.set_font("Helvetica", "", 8)
    pdf.multi_cell(0, 3.8, texto_mov)
    pdf.ln(3)

    # 5. MONITORAMENTO DOS CADASTROS NO CRIA
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(0, 6, "5- MONITORAMENTO DOS CADASTROS NO CRIA", ln=True, fill=True)
    pdf.ln(1)

    if inconsistencias_texto and str(inconsistencias_texto).strip():
        texto_cria = f"Não conformidades ou divergências cadastrais apontadas:\n{str(inconsistencias_texto).strip()}"
    else:
        texto_cria = "Registros cadastrais no CRIA verificados pela fiscalização sem divergências ou inconsistências identificadas."

    pdf.set_font("Helvetica", "", 8)
    pdf.multi_cell(0, 3.8, texto_cria)
    pdf.ln(3)

    # 6. PONTOS DE ATENÇÃO
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(0, 6, "6- PONTOS DE ATENÇÃO", ln=True, fill=True)
    pdf.ln(1)

    notas_pendentes_val = dados_lote.get("notas_pendentes")
    if notas_pendentes_val and str(notas_pendentes_val).strip():
        texto_pontos = f"Apontamentos de atenção da fiscalização:\n{str(notas_pendentes_val).strip()}"
    else:
        texto_pontos = "Sem pontos críticos ou alertas operacionais destacados no período analisado."

    pdf.set_font("Helvetica", "", 8)
    pdf.multi_cell(0, 3.8, texto_pontos)
    pdf.ln(3)

    # 7. NOTAS PENDENTES
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(0, 6, "7- NOTAS PENDENTES", ln=True, fill=True)
    pdf.ln(1)

    if notas_pendentes_val and str(notas_pendentes_val).strip():
        texto_pendentes = f"Notas Fiscais ou pendências documentais a regularizar:\n{str(notas_pendentes_val).strip()}"
    else:
        texto_pendentes = "Nenhuma nota fiscal ou documento comprobatório pendente de apresentação para o período."

    pdf.set_font("Helvetica", "", 8)
    pdf.multi_cell(0, 3.8, texto_pendentes)
    pdf.ln(3)

    # 8. ANÁLISE DE CONFORMIDADE
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(0, 6, "8- ANÁLISE DE CONFORMIDADE", ln=True, fill=True)
    pdf.ln(1)

    apontamentos_val = dados_lote.get("apontamentos_comissao")
    if apontamentos_val and str(apontamentos_val).strip():
        texto_conformidade = str(apontamentos_val).strip()
    else:
        texto_conformidade = "Os procedimentos cirúrgicos, valores faturados e registros foram executados em estrita conformidade com o Termo de Referência."

    pdf.set_font("Helvetica", "", 8)
    pdf.multi_cell(0, 3.8, texto_conformidade)
    pdf.ln(3)

    # 9. DETERMINAÇÕES E PROVIDÊNCIAS
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(0, 6, "9- DETERMINAÇÕES E PROVIDÊNCIAS", ln=True, fill=True)
    pdf.ln(1)

    providencias_val = dados_lote.get("providencias")
    if providencias_val and str(providencias_val).strip():
        texto_providencias = str(providencias_val).strip()
    else:
        texto_providencias = "Sem determinações adicionais. Sugere-se o prosseguimento regular do fluxo administrativo de liquidação e pagamento."

    pdf.set_font("Helvetica", "", 8)
    pdf.multi_cell(0, 3.8, texto_providencias)
    pdf.ln(3)

    # 10. PARECER FINAL
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(0, 6, "10- PARECER FINAL", ln=True, fill=True)
    pdf.ln(1)

    pdf.set_font("Helvetica", "", 8.5)
    pdf.cell(0, 4.5, "Após análise da documentação apresentada, esta Comissão manifesta-se pela seguinte decisão:", ln=True)
    pdf.ln(1.5)

    parecer_atual = str(dados_lote.get("parecer_comissao") or dados_lote.get("status") or "").strip().upper()

    opcoes_parecer = [
        ("APROVADA", "APROVADA" in parecer_atual and "RESSALVAS" not in parecer_atual and "NÃO" not in parecer_atual),
        ("APROVADA COM RESSALVAS", "RESSALVAS" in parecer_atual),
        ("APTA COM NECESSIDADE DE SANEAMENTO", "SANEAMENTO" in parecer_atual or "APTA" in parecer_atual),
        ("NÃO APROVADA", "NÃO APROVADA" in parecer_atual or "REJEITADO" in parecer_atual),
    ]

    pdf.set_font("Helvetica", "B", 8)
    for label, is_checked in opcoes_parecer:
        box = "[ X ]" if is_checked else "[   ]"
        pdf.cell(0, 4.5, f"  {box}  {label}", ln=True)

    pdf.ln(3)

    # Subtópico Explícito: Fundamentação
    pdf.set_font("Helvetica", "B", 8.5)
    pdf.cell(0, 4.5, "Fundamentação:", ln=True)
    pdf.set_font("Helvetica", "", 8)

    fundamentacao_sintese = (
        apontamentos_val or
        providencias_val or
        "Prestação de contas regular. Os serviços executados foram devidamente comprovados por Notas Fiscais e registros de microchipagem no CRIA, atendendo às cláusulas do Edital de Credenciamento."
    )
    pdf.multi_cell(0, 3.8, f"  {str(fundamentacao_sintese).strip()}")
    pdf.ln(6)

    # Assinatura do Membro da Comissão
    meses_pt = ["", "janeiro", "fevereiro", "março", "abril", "maio", "junho",
                "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]
    data_extenso = f"Brasília/DF, {hoje.day:02d} de {meses_pt[hoje.month]} de {hoje.year}."

    pdf.set_font("Helvetica", "", 8.5)
    pdf.cell(0, 5, data_extenso, ln=True, align="R")
    pdf.ln(10)

    pdf.cell(0, 4, "_" * 65, ln=True, align="C")
    pdf.set_font("Helvetica", "B", 8.5)
    pdf.cell(0, 4, f"{membro_val}", ln=True, align="C")
    pdf.set_font("Helvetica", "", 8)
    pdf.cell(0, 4, "Comissão de Gestão e Fiscalização de Contratos - SEPAN", ln=True, align="C")

    return bytes(pdf.output())


def gerar_texto_parecer_sepan(
    dados_lote: dict,
    processo_sei: str,
    membro_comissao: str,
    lista_transacoes: list[dict] = None
) -> str:
    """
    Gera o texto completo e estruturado do Relatório de Prestação de Contas e Fiscalização
    formatado para cópia e colagem direta no editor de documentos do SEI-GDF.
    """
    proc_sei_val = processo_sei.strip() if processo_sei and processo_sei.strip() else "Não informado"
    nome_clinica = _obter_campo(dados_lote, "nome_empresarial", "nome_clinica", padrao="Clínica Credenciada")
    cnpj_clinica = _obter_campo(dados_lote, "cnpj_clinica", padrao="Não informado")
    mes_ref = _obter_campo(dados_lote, "mes_referencia", padrao="Não informado")
    membro_val = membro_comissao.strip() if membro_comissao and membro_comissao.strip() else "Comissão de Gestão"
    hoje = date.today()
    data_emissao = hoje.strftime("%d/%m/%Y")

    total_proc = int(dados_lote.get("total_procedimentos", 0))
    val_tot = float(dados_lote.get("valor_total", 0.0))
    val_tot_str = f"R$ {val_tot:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    qtd_cria_val = dados_lote.get("qtd_cria")
    if qtd_cria_val is None or (isinstance(qtd_cria_val, str) and not str(qtd_cria_val).strip()):
        qtd_cria_val = total_proc
    else:
        try:
            qtd_cria_val = int(qtd_cria_val)
        except (ValueError, TypeError):
            qtd_cria_val = total_proc

    inconsistencias_texto = dados_lote.get("inconsistencias_cria")
    possui_inconsistencias = "Sim" if inconsistencias_texto and str(inconsistencias_texto).strip() else "Não"

    min_nfe, max_nfe = "Não informado", "Não informado"
    if lista_transacoes:
        nf_list = [str(t.get("nfe_referencia", "")).strip() for t in lista_transacoes if str(t.get("nfe_referencia", "")).strip()]
        if nf_list:
            def extrair_numero_nf(val):
                nums = re.findall(r"\d+", val)
                return int(nums[0]) if nums else 0

            try:
                nf_ordenadas = sorted(nf_list, key=extrair_numero_nf)
                min_nfe = nf_ordenadas[0]
                max_nfe = nf_ordenadas[-1]
            except Exception:
                min_nfe = min(nf_list)
                max_nfe = max(nf_list)

    texto_mov = (
        f"As transações realizadas no período totalizaram o montante de {val_tot_str}, conforme apuração efetuada "
        f"a partir dos documentos e relatórios apresentados pela clínica credenciada. "
        f"As notas fiscais emitidas no período compreendem a numeração de {min_nfe} a {max_nfe}. "
        "Os procedimentos realizados observaram os valores máximos estabelecidos no Termo de Referência "
        "e foram acobertados pela documentação fiscal correspondente emitida para cada beneficiário atendido."
    )

    if inconsistencias_texto and str(inconsistencias_texto).strip():
        texto_cria = f"Não conformidades ou divergências cadastrais apontadas:\n{str(inconsistencias_texto).strip()}"
    else:
        texto_cria = "Registros cadastrais no CRIA verificados pela fiscalização sem divergências ou inconsistências identificadas."

    notas_pendentes_val = dados_lote.get("notas_pendentes")
    if notas_pendentes_val and str(notas_pendentes_val).strip():
        texto_pontos = f"Apontamentos de atenção da fiscalização:\n{str(notas_pendentes_val).strip()}"
        texto_pendentes = f"Notas Fiscais ou pendências documentais a regularizar:\n{str(notas_pendentes_val).strip()}"
    else:
        texto_pontos = "Sem pontos críticos ou alertas operacionais destacados no período analisado."
        texto_pendentes = "Nenhuma nota fiscal ou documento comprobatório pendente de apresentação para o período."

    apontamentos_val = dados_lote.get("apontamentos_comissao")
    if apontamentos_val and str(apontamentos_val).strip():
        texto_conformidade = str(apontamentos_val).strip()
    else:
        texto_conformidade = "Os procedimentos cirúrgicos, valores faturados e registros foram executados em estrita conformidade com o Termo de Referência."

    providencias_val = dados_lote.get("providencias")
    if providencias_val and str(providencias_val).strip():
        texto_providencias = str(providencias_val).strip()
    else:
        texto_providencias = "Sem determinações adicionais. Sugere-se o prosseguimento regular do fluxo administrativo de liquidação e pagamento."

    parecer_atual = str(dados_lote.get("parecer_comissao") or dados_lote.get("status") or "").strip().upper()

    opcoes_parecer = [
        ("APROVADA", "APROVADA" in parecer_atual and "RESSALVAS" not in parecer_atual and "NÃO" not in parecer_atual),
        ("APROVADA COM RESSALVAS", "RESSALVAS" in parecer_atual),
        ("APTA COM NECESSIDADE DE SANEAMENTO", "SANEAMENTO" in parecer_atual or "APTA" in parecer_atual),
        ("NÃO APROVADA", "NÃO APROVADA" in parecer_atual or "REJEITADO" in parecer_atual),
    ]

    linhas_parecer = []
    for label, is_checked in opcoes_parecer:
        box = "[ X ]" if is_checked else "[   ]"
        linhas_parecer.append(f"  {box}  {label}")
    parecer_box_str = "\n".join(linhas_parecer)

    fundamentacao_sintese = (
        apontamentos_val or
        providencias_val or
        "Prestação de contas regular. Os serviços executados foram devidamente comprovados por Notas Fiscais e registros de microchipagem no CRIA, atendendo às cláusulas do Edital de Credenciamento."
    )

    meses_pt = ["", "janeiro", "fevereiro", "março", "abril", "maio", "junho",
                "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]
    data_extenso = f"Brasília/DF, {hoje.day:02d} de {meses_pt[hoje.month]} de {hoje.year}."

    documento_sei = f"""GOVERNO DO DISTRITO FEDERAL
SECRETARIA EXTRAORDINÁRIA DE PROTEÇÃO ANIMAL - SEPAN
PROGRAMA CARTÃO CASTRAÇÃO - FISCALIZAÇÃO E PRESTAÇÃO DE CONTAS

RELATÓRIO DE PRESTAÇÃO DE CONTAS E FISCALIZAÇÃO - CARTÃO CASTRAÇÃO

1- IDENTIFICAÇÃO
Processo SEI: {proc_sei_val}
Clínica credenciada (razão social): {nome_clinica}
CNPJ: {cnpj_clinica}
Período analisado: {mes_ref}
Membro da comissão responsável: {membro_val}
Data de emissão: {data_emissao}

2- INTRODUÇÃO
O presente relatório analítico de prestação de contas tem por finalidade apresentar a análise da execução operacional e financeira dos serviços prestados pela empresa credenciada no âmbito do Programa de Apoio à Proteção Animal, na modalidade Cartão Castração, referente ao período de {mes_ref}.

Considerando que o benefício financeiro é disponibilizado diretamente ao cidadão beneficiário do programa, a presente análise possui caráter não apenas contábil, mas também fiscalizatória e de controle da execução contratual, objetivando verificar a conformidade dos serviços executados com as condições estabelecidas no Termo de Referência, anexo ao Edital de Credenciamento, e demais normativos aplicáveis.

A apuração realizada busca assegurar:
- a correta utilização do benefício exclusivamente para o procedimento de castração;
- a observância dos valores máximos pactuados;
- a realização da microchipagem e cadastro dos animais no Cadastro de Identificação Animal (CRIA) sem cobrança adicional;
- a compatibilidade entre documentação fiscal, registros administrativos e informações cadastradas no sistema.

3- RESUMO EXECUTIVO
- Castrações realizadas no período: {total_proc}
- Valor total movimentado no período: {val_tot_str}
- Animais cadastrados no CRIA: {qtd_cria_val}
- Inconsistências Identificadas: {possui_inconsistencias}

4- MOVIMENTAÇÃO FINANCEIRA E TRANSAÇÕES
{texto_mov}

5- MONITORAMENTO DOS CADASTROS NO CRIA
{texto_cria}

6- PONTOS DE ATENÇÃO
{texto_pontos}

7- NOTAS PENDENTES
{texto_pendentes}

8- ANÁLISE DE CONFORMIDADE
{texto_conformidade}

9- DETERMINAÇÕES E PROVIDÊNCIAS
{texto_providencias}

10- PARECER FINAL
Após análise da documentação apresentada, esta Comissão manifesta-se pela seguinte decisão:

{parecer_box_str}

Fundamentação:
  {fundamentacao_sintese.strip()}

{data_extenso}

___________________________________________________
{membro_val}
Comissão de Gestão e Fiscalização de Contratos - SEPAN
"""
    return documento_sei.strip()
