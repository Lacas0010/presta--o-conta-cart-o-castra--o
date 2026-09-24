"""
=============================================================================
GERADOR DE MANUAL DO USUÁRIO EM PDF - PROGRAMA CARTÃO CASTRAÇÃO (SEPAN/GDF)
Arquivo: gerar_manual_pdf.py
=============================================================================
Compila o manual completo ilustrado com capturas de tela das interfaces
em formato PDF de alta qualidade utilizando fpdf2.
=============================================================================
"""

import os
from fpdf import FPDF


class ManualPDF(FPDF):
    """Classe personalizada para diagramação do Manual do Usuário da SEPAN."""

    def __init__(self):
        super().__init__(orientation="P", unit="mm", format="A4")
        self.set_auto_page_break(auto=True, margin=20)
        self.set_margins(12, 22, 12)
        self.is_cover = True

    def header(self):
        if self.is_cover:
            return
        self.set_font("Helvetica", "B", 7.5)
        self.set_text_color(70, 70, 70)
        self.cell(0, 4, "GOVERNO DO DISTRITO FEDERAL - SECRETARIA EXTRAORDINÁRIA DE PROTEÇÃO ANIMAL (SEPAN)", new_x="LMARGIN", new_y="NEXT", align="C")
        self.set_font("Helvetica", "", 7.5)
        self.cell(0, 4, "SISTEMA DE FISCALIZAÇÃO E PRESTAÇÃO DE CONTAS - PROGRAMA CARTÃO CASTRAÇÃO", new_x="LMARGIN", new_y="NEXT", align="C")
        self.set_draw_color(200, 200, 200)
        self.line(12, 19, 198, 19)
        self.ln(4)

    def footer(self):
        if self.is_cover:
            return
        self.set_y(-14)
        self.set_draw_color(210, 210, 210)
        self.line(12, self.get_y(), 198, self.get_y())
        self.set_font("Helvetica", "", 7.5)
        self.set_text_color(120, 120, 120)
        self.cell(110, 7, "Manual de Operação e Uso do Sistema - SEPAN/GDF &bull; Versão 1.0", align="L")
        self.cell(76, 7, f"Página {self.page_no()}/{{nb}}", align="R")

    def add_chapter_title(self, number, title):
        self.ln(4)
        self.set_fill_color(30, 58, 138)  # Azul Institucional Escuro #1e3a8a
        self.set_text_color(255, 255, 255)
        self.set_font("Helvetica", "B", 10.5)
        self.cell(0, 7.5, f" {number}. {title.upper()}", new_x="LMARGIN", new_y="NEXT", fill=True)
        self.set_text_color(30, 41, 59)
        self.ln(2.5)

    def add_section_title(self, title):
        self.ln(2)
        self.set_fill_color(238, 242, 255) # Indigo suave
        self.set_text_color(37, 99, 235)  # Azul vibrante
        self.set_font("Helvetica", "B", 9.5)
        self.cell(0, 6, f"  {title}", new_x="LMARGIN", new_y="NEXT", fill=True)
        self.set_text_color(30, 41, 59)
        self.ln(1.5)

    def add_subsection_title(self, title):
        self.set_font("Helvetica", "B", 8.5)
        self.set_text_color(30, 58, 138)
        self.cell(0, 5, f"&bull; {title}", new_x="LMARGIN", new_y="NEXT")
        self.set_text_color(30, 41, 59)
        self.ln(0.5)

    def add_paragraph(self, text):
        self.set_font("Helvetica", "", 8.5)
        self.set_text_color(40, 40, 40)
        self.multi_cell(0, 4.3, text)
        self.ln(1.5)

    def add_bullet(self, title, text):
        self.set_font("Helvetica", "B", 8.2)
        self.set_text_color(30, 41, 59)
        self.write(4.2, f"  - {title}: ")
        self.set_font("Helvetica", "", 8.2)
        self.set_text_color(50, 50, 50)
        self.write(4.2, f"{text}\n")

    def add_alert_box(self, title, text, tipo="info"):
        """Adiciona caixa de destaque institucional."""
        if tipo == "importante":
            bg_r, bg_g, bg_b = 254, 242, 242
            border_r, border_g, border_b = 239, 68, 68
            icon = "[ ATENÇÃO ]"
        elif tipo == "dica":
            bg_r, bg_g, bg_b = 240, 253, 244
            border_r, border_g, border_b = 34, 197, 94
            icon = "[ DICA PRÁTICA ]"
        else:
            bg_r, bg_g, bg_b = 239, 246, 255
            border_r, border_g, border_b = 59, 130, 246
            icon = "[ INFORMAÇÃO ]"

        self.ln(1)
        self.set_fill_color(bg_r, bg_g, bg_b)
        self.set_draw_color(border_r, border_g, border_b)
        self.set_line_width(0.4)
        
        # Guarda posição
        curr_x = self.get_x()
        curr_y = self.get_y()
        
        self.set_font("Helvetica", "B", 8)
        self.set_text_color(border_r, border_g, border_b)
        self.cell(0, 4.5, f"  {icon} {title}", new_x="LMARGIN", new_y="NEXT", fill=True, border="LTR")
        
        self.set_font("Helvetica", "", 8)
        self.set_text_color(50, 50, 50)
        self.multi_cell(0, 4, f"  {text}", fill=True, border="LBR")
        self.set_line_width(0.2)
        self.set_draw_color(200, 200, 200)
        self.ln(2)

    def add_screenshot(self, img_path, caption):
        """Adiciona captura de tela centralizada com borda e legenda."""
        if not os.path.exists(img_path):
            return

        # Verifica se cabe na página ou adiciona quebra
        if self.get_y() > 210:
            self.add_page()

        self.ln(1.5)
        # Largura máxima disponível: 186 mm
        img_w = 176
        img_x = (210 - img_w) / 2
        
        # Desenha moldura de fundo
        start_y = self.get_y()
        self.image(img_path, x=img_x, y=start_y, w=img_w)
        
        # Avança o cursor após a imagem (altura estimada ~105mm para aspect ratio 1440x900)
        img_h = (img_w / 1440) * 920
        self.set_y(start_y + img_h + 1.5)
        
        # Legenda
        self.set_font("Helvetica", "I", 7.5)
        self.set_text_color(100, 100, 100)
        self.cell(0, 4, f"Figura: {caption}", new_x="LMARGIN", new_y="NEXT", align="C")
        self.ln(2)


def gerar_manual_completo_pdf(output_path: str = "MANUAL_DO_USUARIO_SEPAN.pdf"):
    """Gera o arquivo PDF institucional diagramado do Manual do Usuário."""
    pdf = ManualPDF()
    screenshots_dir = "docs/screenshots"

    # =========================================================================
    # CAPA INSTITUCIONAL
    # =========================================================================
    pdf.is_cover = True
    pdf.add_page()

    # Faixa superior azul
    pdf.set_fill_color(30, 58, 138)
    pdf.rect(0, 0, 210, 80, style="F")

    pdf.set_y(22)
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 7, "GOVERNO DO DISTRITO FEDERAL", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.set_font("Helvetica", "", 10.5)
    pdf.cell(0, 6, "SECRETARIA EXTRAORDINÁRIA DE PROTEÇÃO ANIMAL - SEPAN", new_x="LMARGIN", new_y="NEXT", align="C")
    
    pdf.ln(4)
    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 9, "MANUAL DO USUÁRIO FINAL", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.set_font("Helvetica", "I", 11)
    pdf.set_text_color(224, 231, 255)
    pdf.cell(0, 6, "Sistema de Fiscalização e Prestação de Contas", new_x="LMARGIN", new_y="NEXT", align="C")

    pdf.set_y(90)
    pdf.set_text_color(30, 41, 59)

    # Imagem ou destaque da tela inicial na capa
    img_capa = os.path.join(screenshots_dir, "08_comissao_dashboard_fila.png")
    if os.path.exists(img_capa):
        pdf.image(img_capa, x=17, y=95, w=176)
        pdf.set_y(210)
    else:
        pdf.set_y(150)

    # Box de identificação técnica na capa
    pdf.set_fill_color(248, 250, 252)
    pdf.set_draw_color(203, 213, 225)
    pdf.rect(17, 220, 176, 50, style="DF")

    pdf.set_y(223)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(30, 58, 138)
    pdf.cell(0, 5, "   PROGRAMA CARTÃO CASTRAÇÃO - DISTRITO FEDERAL", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(1)
    
    pdf.set_font("Helvetica", "", 8.5)
    pdf.set_text_color(60, 60, 60)
    pdf.cell(0, 4.5, "Público-Alvo: Clínicas Veterinárias Credenciadas e Comissão de Fiscalização SEPAN", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.cell(0, 4.5, "Integrações Oficiais: Sistema CRIA (Identificação Animal) & SEI-GDF (Processos Eletrônicos)", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.cell(0, 4.5, "Versão do Documento: 1.0 &bull; Ano: 2026 &bull; Brasília/DF", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.cell(0, 4.5, "Ambiente: Plataforma Web Integrada (PostgreSQL / Supabase / Streamlit)", new_x="LMARGIN", new_y="NEXT", align="C")

    # =========================================================================
    # PÁGINA 2: SUMÁRIO & APRESENTAÇÃO
    # =========================================================================
    pdf.is_cover = False
    pdf.add_page()

    pdf.add_chapter_title("1", "Visão Geral e Apresentação Institucional")
    pdf.add_paragraph(
        "O Sistema de Fiscalização e Prestação de Contas do Programa Cartão Castração é a plataforma digital "
        "institucional desenvolvida para modernizar, garantir a transparência pública e estruturar todo o ciclo "
        "de prestação de contas dos serviços de esterilização cirúrgica e microchipagem de caninos e felinos no Distrito Federal."
    )
    pdf.add_paragraph(
        "A plataforma conecta em tempo real as Clínicas Veterinárias Credenciadas com a Comissão de Gestão e Fiscalização "
        "da Secretaria Extraordinária de Proteção Animal (SEPAN/GDF), assegurando integridade cadastral com o sistema "
        "CRIA (Cadastro Distrital de Identificação Animal), auditoria digital imutável e integração nativa com o SEI-GDF."
    )

    pdf.add_alert_box(
        "Objetivos Estratégicos do Sistema",
        "1. Eliminar processos físicos e planilhas paralelas através de prestação de contas 100% digital.\n"
        "2. Assegurar rastreabilidade cirúrgica rigorosa por animal, microchip implantado e nota fiscal emitida.\n"
        "3. Viabilizar a fiscalização técnica em 10 itens com geração automática de documentos nato-digitais para o SEI-GDF.",
        tipo="info"
    )

    pdf.add_section_title("Estrutura de Perfis de Acesso (Roles)")
    pdf.add_paragraph(
        "O sistema adota o modelo de controle de acesso baseado em funções (Role-Based Access Control - RBAC) "
        "com políticas de segurança a nível de linha de banco de dados (Row Level Security - RLS):"
    )

    perfis_info = [
        ("Clínica Credenciada ('clinica')", "Acesso exclusivo aos atendimentos do seu estabelecimento. Permite registro individual de procedimentos, alteração direta de lançamentos abertos, consolidação mensal de lotes, download do Anexo V em PDF, solicitação de retificação e auditoria interna."),
        ("Comissão de Gestão ('comissao')", "Acesso aos servidores da SEPAN para gestão da fila de lotes, deliberação de retificações (aceite/recusa fundamentada), emissão de pareceres técnicos em 10 itens com validação de CRIA, download do parecer oficial em PDF e texto nato-digital para o SEI."),
        ("Administrador Geral ('admin')", "Controle irrestrito a todas as visões, parametrização global da validação rígida de CPF/CNPJ e acesso ao backoffice de homologação de usuários."),
        ("Leitor / Pendente ('leitor')", "Perfil provisório atribuído aos novos servidores que realizam cadastro institucional de Pessoa Física, aguardando liberação formal de permissões.")
    ]

    for p_tit, p_desc in perfis_info:
        pdf.add_bullet(p_tit, p_desc)
        pdf.ln(0.5)

    # =========================================================================
    # CAPÍTULO 2: ACESSO, CADASTRO E LOGIN
    # =========================================================================
    pdf.add_page()
    pdf.add_chapter_title("2", "Primeiro Acesso, Cadastro e Autenticação")
    pdf.add_paragraph(
        "O sistema conta com tela unificada de autenticação com segregação clara entre Pessoa Jurídica (Clínicas) "
        "e Pessoa Física (Servidores da SEPAN), além de suporte integral aos modos Claro e Escuro."
    )

    pdf.add_screenshot(os.path.join(screenshots_dir, "01_login_pj.png"), "Tela de Login e Acesso Institucional ao Sistema")

    pdf.add_section_title("2.1. Cadastro de Clínica Credenciada (Pessoa Jurídica)")
    pdf.add_paragraph(
        "Para cadastrar um novo estabelecimento credenciado, selecione a aba 'Criar Conta' e marque a opção "
        "'Pessoa Jurídica (Clínica Credenciada)'. Os seguintes campos são obrigatórios para emissão dos relatórios oficiais:"
    )
    pdf.add_bullet("CNPJ da Empresa", "14 dígitos oficiais do estabelecimento credenciado.")
    pdf.add_bullet("Nome Empresarial / Razão Social", "Razão social completa conforme constar no Cartão CNPJ.")
    pdf.add_bullet("Nome Fantasia", "Nome público/comercial do hospital ou clínica veterinária.")
    pdf.add_bullet("Endereço Completo & Telefone", "Logradouro, número, bairro, cidade/UF e telefone de contato institucional.")
    pdf.add_bullet("Representante Legal", "Nome completo e CPF do responsável legal que assinará a prestação de contas.")

    pdf.add_screenshot(os.path.join(screenshots_dir, "02_cadastro_pj.png"), "Formulário de Cadastro de Clínica Credenciada (PJ)")

    pdf.add_section_title("2.2. Cadastro de Servidor da SEPAN (Pessoa Física)")
    pdf.add_paragraph(
        "Servidores municipais e fiscais devem selecionar 'Pessoa Física (Servidor SEPAN)' e preencher E-mail Institucional, "
        "Senha, CPF e Nome Completo. Ao concluir o cadastro, a conta é criada com perfil 'Leitor (Pendente)' até a homologação."
    )

    pdf.add_screenshot(os.path.join(screenshots_dir, "03_cadastro_pf.png"), "Formulário de Cadastro de Servidor SEPAN (PF)")

    # =========================================================================
    # CAPÍTULO 3: PORTAL DA CLÍNICA CREDENCIADA
    # =========================================================================
    pdf.add_page()
    pdf.add_chapter_title("3", "Portal da Clínica Credenciada")
    pdf.add_paragraph(
        "O portal da clínica é o ambiente operacional onde os procedimentos cirúrgicos são lançados, saneados, "
        "consolidados em lotes e auditados pelo próprio estabelecimento."
    )

    pdf.add_section_title("3.1. Lançamento Individual de Atendimentos")
    pdf.add_paragraph(
        "Cada cirurgia realizada pelo Programa Cartão Castração deve ser registrada individualmente na aba "
        "'Lançamento de Atendimentos'. O formulário está dividido em 3 blocos:"
    )
    pdf.add_bullet("1. Beneficiário / Tutor", "Data da Castração, CPF e Nome Completo do titular do benefício.")
    pdf.add_bullet("2. Identificação do Animal", "Espécie (Canina/Felina), Sexo (Macho/Fêmea), Porte (Pequeno/Médio/Grande), Nº do Microchip e indicação de Óbito (Não/Sim).")
    pdf.add_bullet("3. Faturamento & NF-e", "Valor contratual tabelado em R$ e número/série da Nota Fiscal comprobatória.")

    pdf.add_screenshot(os.path.join(screenshots_dir, "04_clinica_lancamento.png"), "Registro Individual de Atendimento e Relação da Sessão")

    pdf.add_section_title("3.2. Fechamento de Lote Mensal de Prestação de Contas")
    pdf.add_paragraph(
        "Ao final de cada mês, a clínica acessa a aba 'Fechamento de Lote Mensal' e seleciona a competência desejada. "
        "O sistema consolida automaticamente os procedimentos em aberto e exibe 5 métricas em tempo real:"
    )

    pdf.add_screenshot(os.path.join(screenshots_dir, "05_clinica_fechamento.png"), "Painel de Fechamento de Lote Mensal com KPIs e Relato de Óbitos")

    pdf.add_alert_box(
        "Edição Direta de Atendimentos Abertos",
        "Caso algum dado tenha sido digitado incorretamente, utilize o recurso 'Alterar Dados do Atendimento' dentro da própria tela de fechamento. O sistema carrega todos os campos para correção imediata sem necessidade de excluir o registro.",
        tipo="dica"
    )

    pdf.add_paragraph(
        "Destaques do Fechamento de Lote:\n"
        "&bull; Relato de Óbitos Automatizado: O sistema identifica automaticamente animais com óbito registrado e pré-preenche o relatório circunstanciado com espécie, microchip, tutor e data, mantendo o campo aberto para parecer do médico-veterinário.\n"
        "&bull; Declaração de Responsabilidade Legal: A clínica atesta formalmente a veracidade das informações, regular emissão das Notas Fiscais e gratuidade do serviço aos tutores."
    )

    # =========================================================================
    # HISTÓRICO, ANEXO V E RETIFICAÇÃO
    # =========================================================================
    pdf.add_page()
    pdf.add_section_title("3.3. Histórico de Lotes, Emissão do Anexo V e Retificação")
    pdf.add_paragraph(
        "Na aba 'Histórico de Lotes', o estabelecimento acompanha o status de cada prestação de contas enviada, "
        "baixa o Relatório Oficial Anexo V em PDF e formaliza pedidos de retificação quando necessário."
    )

    pdf.add_screenshot(os.path.join(screenshots_dir, "06_clinica_historico_retificacao.png"), "Histórico de Lotes, Download do Anexo V e Pedidos de Retificação")

    pdf.add_alert_box(
        "Fluxo Seguro de Retificação e Estorno",
        "1. Solicitação: A clínica clica em 'Solicitar Retificação do Lote', informa o motivo e envia à SEPAN.\n"
        "2. Análise SEPAN: Os fiscais avaliam e aprovam ou recusam com fundamentação.\n"
        "3. Estorno Seguro: Após aprovação da comissão, a clínica clica em 'Estornar Lote para Correção'. Os atendimentos retornam para a aba de fechamento para saneamento e reenvio.",
        tipo="importante"
    )

    pdf.add_section_title("3.4. Auditoria de Atendimentos da Clínica")
    pdf.add_paragraph(
        "A aba 'Auditoria de Atendimentos' permite pesquisar toda a base histórica do estabelecimento através de múltiplos filtros "
        "combinados (Período, Status, Tutor, CPF, Espécie, Sexo, Porte, Microchip, NF-e) e conta com botão para exportação em formato CSV."
    )

    pdf.add_screenshot(os.path.join(screenshots_dir, "07_clinica_auditoria.png"), "Auditoria e Pesquisa Avançada de Atendimentos da Clínica")

    # =========================================================================
    # CAPÍTULO 4: PAINEL DA COMISSÃO DE FISCALIZAÇÃO (SEPAN)
    # =========================================================================
    pdf.add_page()
    pdf.add_chapter_title("4", "Painel da Comissão de Gestão e Fiscalização")
    pdf.add_paragraph(
        "O módulo da Comissão é destinado aos servidores e fiscais da SEPAN responsáveis pela análise documental, "
        "conferência no sistema CRIA, deliberação de retificações e instrução processual eletrônica no SEI-GDF."
    )

    pdf.add_section_title("4.1. Dashboard Executivo e Fila de Lotes")
    pdf.add_paragraph(
        "O dashboard de topo apresenta o quantitativo de Lotes Pendentes de Parecer, Lotes Homologados, "
        "Retificações Solicitadas e Valor Total em Análise (R$). A fila permite filtrar prestações por clínica, "
        "competência e status de tramitação."
    )

    pdf.add_screenshot(os.path.join(screenshots_dir, "08_comissao_dashboard_fila.png"), "Painel Executivo e Fila de Fiscalização de Lotes da SEPAN")

    pdf.add_section_title("4.2. Deliberação de Retificações (Aceite / Recusa)")
    pdf.add_paragraph(
        "Quando um estabelecimento solicita retificação, os fiscais examinam a justificativa no painel e podem:\n"
        "&bull; Aceitar Retificação: Autoriza a clínica a realizar o estorno para correções.\n"
        "&bull; Recusar Retificação: Registra a fundamentação legal da recusa, exibida no painel da clínica."
    )

    pdf.add_screenshot(os.path.join(screenshots_dir, "09_comissao_deliberacao_retificacao.png"), "Painel de Deliberação de Retificação de Lote pela Comissão")

    # =========================================================================
    # PARECER EM 10 ITENS E INTEGRAÇÃO SEI
    # =========================================================================
    pdf.add_page()
    pdf.add_section_title("4.3. Parecer Técnico em 10 Itens e Fiscalização")
    pdf.add_paragraph(
        "A fiscalização técnica estruturada contempla a conferência rigorosa dos 10 itens padronizados pela SEPAN:"
    )
    pdf.add_bullet("Item 5. Monitoramento no CRIA", "Quantidade de animais cadastrados no sistema CRIA (com trava eletrônica contra quantidade excedente) e relatório de divergências cadastrais.")
    pdf.add_bullet("Itens 6 e 7. Pontos de Atenção", "Verificação de notas pendentes, séries fiscais ou pendências documentais.")
    pdf.add_bullet("Item 8. Análise de Conformidade", "Aferição da conformidade dos serviços executados e preços praticados.")
    pdf.add_bullet("Item 9. Determinações e Providências", "Instruções formais e recomendações emitidas ao estabelecimento.")
    pdf.add_bullet("Item 10. Parecer Final", "Decisão colegiada: 'Aprovada', 'Aprovada com Ressalvas', 'Apta com Necessidade de Saneamento' ou 'Não Aprovada'.")

    pdf.add_screenshot(os.path.join(screenshots_dir, "10_comissao_parecer_10itens.png"), "Formulário de Emissão do Parecer Técnico em 10 Itens")

    pdf.add_section_title("4.4. Documento Oficial e Texto Nato-Digital para o SEI-GDF")
    pdf.add_paragraph(
        "Após salvar o parecer, o sistema gera os documentos oficiais:\n"
        "&bull; Aba Baixar Parecer Técnico (PDF): Documento oficial diagramado para juntada ao processo.\n"
        "&bull; Aba Texto para o SEI (Copiar e Colar): Texto estruturado para colar diretamente no editor do SEI-GDF, viabilizando a assinatura eletrônica dos fiscais no processo, com botão de 'Homologar e Bloquear Parecer'."
    )

    pdf.add_screenshot(os.path.join(screenshots_dir, "11_comissao_documentos_sei.png"), "Geração de Documento Oficial em PDF e Texto Nato-Digital para o SEI-GDF")

    # =========================================================================
    # AUDITORIA GERAL E LOGS
    # =========================================================================
    pdf.add_page()
    pdf.add_section_title("4.5. Auditoria Geral de Atendimentos da Rede")
    pdf.add_paragraph(
        "A comissão pode consultar de forma unificada todos os procedimentos realizados por todas as clínicas "
        "credenciadas no Distrito Federal, com filtros avançados, KPIs consolidados e exportação em CSV."
    )

    pdf.add_screenshot(os.path.join(screenshots_dir, "12_comissao_auditoria_geral.png"), "Painel de Auditoria Geral da Rede Credenciada")

    pdf.add_section_title("4.6. Histórico de Auditoria e Rastreabilidade (Logs)")
    pdf.add_paragraph(
        "Trilha de auditoria imutável em conformidade com as diretrizes da CGDF e TCDF. Registra com carimbo de tempo, "
        "usuário e CNPJ cada criação, alteração, exclusão, envio de lote, deliberação e homologação de parecer."
    )

    pdf.add_screenshot(os.path.join(screenshots_dir, "13_comissao_logs_rastreabilidade.png"), "Histórico Cronológico de Auditoria e Trilha de Rastreabilidade")

    # =========================================================================
    # CAPÍTULO 5: ADMINISTRAÇÃO E BACKOFFICE
    # =========================================================================
    pdf.add_page()
    pdf.add_chapter_title("5", "Administração e Backoffice")
    
    pdf.add_section_title("5.1. Backoffice de Gestão de Usuários (gestao_usuarios.py)")
    pdf.add_paragraph(
        "Módulo independente para controle de segurança institucional. Permite homologar novos servidores cadastrados "
        "como 'Leitor' e atribuir permissões de 'Comissão', 'Clínica' ou 'Administrador'."
    )

    pdf.add_screenshot(os.path.join(screenshots_dir, "14_admin_gestao_usuarios.png"), "Painel de Gestão de Usuários e Homologação de Perfis")

    pdf.add_section_title("5.2. Parâmetros do Sistema e Validação Rígida")
    pdf.add_paragraph(
        "No menu administrativo do portal, o gestor de TI controla o interruptor (toggle) de 'Validação Rígida de CPF/CNPJ', "
        "permitindo alternar com segurança entre o Modo de Produção (validação matemática estrita) e o Modo de Teste."
    )

    pdf.add_screenshot(os.path.join(screenshots_dir, "15_admin_parametros.png"), "Configurações Gerais e Toggle de Validação de Documentos")

    # =========================================================================
    # CAPÍTULO 6: FAQ E BOAS PRÁTICAS
    # =========================================================================
    pdf.add_page()
    pdf.add_chapter_title("6", "Boas Práticas e Perguntas Frequentes (FAQ)")

    faq_items = [
        ("Como corrigir um atendimento digitado com erro antes de fechar o lote?",
         "Acesse a aba 'Fechamento de Lote Mensal', expanda 'Gerenciar e Ajustar Atendimentos do Período', selecione o atendimento em 'Alterar Dados do Atendimento', corrija os dados e salve."),
        ("O que fazer se esqueci de incluir um atendimento em um lote já enviado?",
         "Na aba 'Histórico de Lotes', clique em 'Solicitar Retificação do Lote', detalhe o motivo e aguarde autorização da SEPAN. Quando aprovado, clique em 'Estornar Lote para Correção', adicione o atendimento e feche o lote novamente."),
        ("Como a comissão bloqueia o parecer para garantir integridade no SEI?",
         "Ao clicar em 'Baixar Parecer Técnico (PDF)' ou no botão 'Homologar e Bloquear Parecer' na aba de Texto SEI, o sistema grava o bloqueio no banco de dados e impede novas edições no processo."),
        ("O que acontece com os atendimentos quando um lote é estornado?",
         "Eles são desvinculados do identificador do lote (lote_id = null) e retornam imediatamente para a tela de Fechamento de Lote Mensal, mantendo intactos todos os dados originais.")
    ]

    for p, r in faq_items:
        pdf.add_alert_box(f"P: {p}", f"R: {r}", tipo="dica")

    pdf.ln(4)
    pdf.set_fill_color(30, 58, 138)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(0, 7, "SECRETARIA EXTRAORDINÁRIA DE PROTEÇÃO ANIMAL - GOVERNO DO DISTRITO FEDERAL", new_x="LMARGIN", new_y="NEXT", align="C", fill=True)

    pdf.output(output_path)
    print(f"Manual PDF gerado com sucesso em: {output_path}")


if __name__ == "__main__":
    gerar_manual_completo_pdf("MANUAL_DO_USUARIO_SEPAN.pdf")
