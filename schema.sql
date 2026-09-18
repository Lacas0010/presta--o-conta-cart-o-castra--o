-- =============================================================================
-- SISTEMA DE FISCALIZAÇÃO E PRESTAÇÃO DE CONTAS - CARTÃO CASTRAÇÃO (SEPAN)
-- Estrutura Completa do Banco de Dados: Transações, Lotes e Configurações
-- =============================================================================
-- Execute este script no SQL Editor do Supabase (Dashboard > SQL Editor > New query)
-- =============================================================================

-- 1. Criação da Tabela configuracoes_sistema
CREATE TABLE IF NOT EXISTS public.configuracoes_sistema (
    chave VARCHAR(100) PRIMARY KEY,
    valor_booleano BOOLEAN DEFAULT false NOT NULL,
    descricao TEXT,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

INSERT INTO public.configuracoes_sistema (chave, valor_booleano, descricao)
VALUES ('validar_documentos', false, 'Habilita ou desabilita a validação matemática rigorosa de CPF e CNPJ')
ON CONFLICT (chave) DO NOTHING;

-- 2. Criação da Tabela lotes_prestacao (Prestação de Contas Mensal)
CREATE TABLE IF NOT EXISTS public.lotes_prestacao (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    cnpj_clinica VARCHAR(20) NOT NULL,
    nome_clinica VARCHAR(255),
    nome_empresarial VARCHAR(255),
    nome_fantasia VARCHAR(255),
    endereco_clinica TEXT,
    telefone_clinica VARCHAR(50),
    email_clinica VARCHAR(255),
    nome_representante VARCHAR(255),
    cpf_representante VARCHAR(20),
    mes_referencia VARCHAR(20) NOT NULL,
    total_procedimentos INTEGER DEFAULT 0 NOT NULL,
    valor_total NUMERIC(10, 2) DEFAULT 0.00 NOT NULL,
    obitos_relato TEXT,
    reclamacoes_relato TEXT,
    declaracao_responsabilidade BOOLEAN DEFAULT true NOT NULL,
    status VARCHAR(100) DEFAULT 'Enviado para Análise' NOT NULL, 
    -- Status: 'Enviado para Análise', 'Aprovada', 'Aprovada com Ressalvas', 'Apta com Necessidade de Saneamento', 'Não Aprovada', 'Retificado pela Clínica'
    qtd_cria INTEGER DEFAULT 0,
    inconsistencias_cria TEXT,
    notas_pendentes TEXT,
    apontamentos_comissao TEXT,
    providencias TEXT,
    parecer_comissao VARCHAR(100),
    data_parecer TIMESTAMP WITH TIME ZONE,
    analisado_por VARCHAR(255)
);

-- Atualizações de Colunas em lotes_prestacao (Retrocompatibilidade)
ALTER TABLE public.lotes_prestacao ADD COLUMN IF NOT EXISTS nome_empresarial VARCHAR(255);
ALTER TABLE public.lotes_prestacao ADD COLUMN IF NOT EXISTS nome_fantasia VARCHAR(255);
ALTER TABLE public.lotes_prestacao ADD COLUMN IF NOT EXISTS endereco_clinica TEXT;
ALTER TABLE public.lotes_prestacao ADD COLUMN IF NOT EXISTS telefone_clinica VARCHAR(50);
ALTER TABLE public.lotes_prestacao ADD COLUMN IF NOT EXISTS email_clinica VARCHAR(255);
ALTER TABLE public.lotes_prestacao ADD COLUMN IF NOT EXISTS nome_representante VARCHAR(255);
ALTER TABLE public.lotes_prestacao ADD COLUMN IF NOT EXISTS cpf_representante VARCHAR(20);
ALTER TABLE public.lotes_prestacao ADD COLUMN IF NOT EXISTS qtd_cria INTEGER DEFAULT 0;
ALTER TABLE public.lotes_prestacao ADD COLUMN IF NOT EXISTS inconsistencias_cria TEXT;
ALTER TABLE public.lotes_prestacao ADD COLUMN IF NOT EXISTS notas_pendentes TEXT;
ALTER TABLE public.lotes_prestacao ADD COLUMN IF NOT EXISTS providencias TEXT;
ALTER TABLE public.lotes_prestacao ADD COLUMN IF NOT EXISTS parecer_bloqueado BOOLEAN DEFAULT false;
ALTER TABLE public.lotes_prestacao ADD COLUMN IF NOT EXISTS processo_sei VARCHAR(100);
ALTER TABLE public.lotes_prestacao ADD COLUMN IF NOT EXISTS membro_analise VARCHAR(255);
ALTER TABLE public.lotes_prestacao ADD COLUMN IF NOT EXISTS data_bloqueio_parecer TIMESTAMP WITH TIME ZONE;
ALTER TABLE public.lotes_prestacao ADD COLUMN IF NOT EXISTS solicitacao_retificacao BOOLEAN DEFAULT false;
ALTER TABLE public.lotes_prestacao ADD COLUMN IF NOT EXISTS status_retificacao VARCHAR(50);
ALTER TABLE public.lotes_prestacao ADD COLUMN IF NOT EXISTS motivo_retificacao TEXT;
ALTER TABLE public.lotes_prestacao ADD COLUMN IF NOT EXISTS motivo_recusa_retificacao TEXT;
ALTER TABLE public.lotes_prestacao ADD COLUMN IF NOT EXISTS data_solicitacao_retificacao TIMESTAMP WITH TIME ZONE;
ALTER TABLE public.lotes_prestacao ADD COLUMN IF NOT EXISTS analisado_retificacao_por VARCHAR(255);
ALTER TABLE public.lotes_prestacao ADD COLUMN IF NOT EXISTS data_resposta_retificacao TIMESTAMP WITH TIME ZONE;

-- 3. Criação da Tabela relacao_transacoes (Atendimentos Individuais)
CREATE TABLE IF NOT EXISTS public.relacao_transacoes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    data_atendimento DATE NOT NULL,
    cnpj_clinica VARCHAR(20) NOT NULL,
    nome_clinica VARCHAR(255),
    cpf_beneficiario VARCHAR(20) NOT NULL,
    nome_beneficiario VARCHAR(255) NOT NULL,
    especie VARCHAR(50) NOT NULL,
    sexo VARCHAR(20) NOT NULL,
    porte VARCHAR(50) NOT NULL,
    numero_microchip VARCHAR(100) NOT NULL,
    valor_transacao NUMERIC(10, 2) NOT NULL,
    nfe_referencia VARCHAR(100) NOT NULL,
    status_validacao VARCHAR(50) DEFAULT 'pendente' NOT NULL,
    observacoes_comissao TEXT,
    obito BOOLEAN DEFAULT false,
    lote_id UUID REFERENCES public.lotes_prestacao(id) ON DELETE SET NULL
);

-- Atualizações de Colunas em relacao_transacoes (Retrocompatibilidade)
ALTER TABLE public.relacao_transacoes ADD COLUMN IF NOT EXISTS nome_clinica VARCHAR(255);
ALTER TABLE public.relacao_transacoes ADD COLUMN IF NOT EXISTS lote_id UUID REFERENCES public.lotes_prestacao(id) ON DELETE SET NULL;
ALTER TABLE public.relacao_transacoes ADD COLUMN IF NOT EXISTS obito BOOLEAN DEFAULT false;

-- 4. Índices para Otimização de Consultas
CREATE INDEX IF NOT EXISTS idx_transacoes_cnpj ON public.relacao_transacoes(cnpj_clinica);
CREATE INDEX IF NOT EXISTS idx_transacoes_lote_id ON public.relacao_transacoes(lote_id);
CREATE INDEX IF NOT EXISTS idx_transacoes_data ON public.relacao_transacoes(data_atendimento);
CREATE INDEX IF NOT EXISTS idx_transacoes_cpf ON public.relacao_transacoes(cpf_beneficiario);
CREATE INDEX IF NOT EXISTS idx_lotes_cnpj ON public.lotes_prestacao(cnpj_clinica);
CREATE INDEX IF NOT EXISTS idx_lotes_status ON public.lotes_prestacao(status);
CREATE INDEX IF NOT EXISTS idx_lotes_mes ON public.lotes_prestacao(mes_referencia);

-- 5. Habilitação de Segurança em Nível de Linha (RLS)
ALTER TABLE public.configuracoes_sistema ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.relacao_transacoes ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.lotes_prestacao ENABLE ROW LEVEL SECURITY;

-- 6. Políticas de Acesso
DROP POLICY IF EXISTS "Permitir leitura de configuracoes para autenticados" ON public.configuracoes_sistema;
DROP POLICY IF EXISTS "Permitir atualizacao de configuracoes para autenticados" ON public.configuracoes_sistema;
DROP POLICY IF EXISTS "Permitir insercao de configuracoes para autenticados" ON public.configuracoes_sistema;

CREATE POLICY "Permitir leitura de configuracoes para autenticados" 
ON public.configuracoes_sistema FOR SELECT TO authenticated USING (true);

CREATE POLICY "Permitir atualizacao de configuracoes para autenticados" 
ON public.configuracoes_sistema FOR UPDATE TO authenticated USING (true) WITH CHECK (true);

CREATE POLICY "Permitir insercao de configuracoes para autenticados" 
ON public.configuracoes_sistema FOR INSERT TO authenticated WITH CHECK (true);

DROP POLICY IF EXISTS "Permitir insercao para usuarios autenticados" ON public.relacao_transacoes;
DROP POLICY IF EXISTS "Permitir leitura para usuarios autenticados" ON public.relacao_transacoes;
DROP POLICY IF EXISTS "Permitir atualizacao para usuarios autenticados" ON public.relacao_transacoes;
DROP POLICY IF EXISTS "Permitir exclusao para usuarios autenticados" ON public.relacao_transacoes;

CREATE POLICY "Permitir insercao para usuarios autenticados"
ON public.relacao_transacoes FOR INSERT TO authenticated WITH CHECK (true);

CREATE POLICY "Permitir leitura para usuarios autenticados"
ON public.relacao_transacoes FOR SELECT TO authenticated USING (true);

CREATE POLICY "Permitir atualizacao para usuarios autenticados"
ON public.relacao_transacoes FOR UPDATE TO authenticated USING (true) WITH CHECK (true);

CREATE POLICY "Permitir exclusao para usuarios autenticados"
ON public.relacao_transacoes FOR DELETE TO authenticated USING (true);

DROP POLICY IF EXISTS "Permitir leitura de lotes para autenticados" ON public.lotes_prestacao;
DROP POLICY IF EXISTS "Permitir criacao de lotes para autenticados" ON public.lotes_prestacao;
DROP POLICY IF EXISTS "Permitir atualizacao de lotes para autenticados" ON public.lotes_prestacao;

CREATE POLICY "Permitir leitura de lotes para autenticados" 
ON public.lotes_prestacao FOR SELECT TO authenticated USING (true);

CREATE POLICY "Permitir criacao de lotes para autenticados" 
ON public.lotes_prestacao FOR INSERT TO authenticated WITH CHECK (true);

CREATE POLICY "Permitir atualizacao de lotes para autenticados" 
ON public.lotes_prestacao FOR UPDATE TO authenticated USING (true) WITH CHECK (true);

-- 7. Criação da Tabela logs_auditoria (Histórico de Alterações e Rastreabilidade)
CREATE TABLE IF NOT EXISTS public.logs_auditoria (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    cnpj_clinica VARCHAR(20),
    nome_clinica VARCHAR(255),
    usuario_email VARCHAR(255),
    usuario_tipo VARCHAR(50), -- 'clinica' ou 'comissao'
    tipo_entidade VARCHAR(50) NOT NULL, -- 'atendimento', 'lote', 'parecer', 'retificacao', 'configuracao'
    acao VARCHAR(100) NOT NULL, -- 'criacao', 'alteracao', 'exclusao', 'estorno', 'emissao_parecer', 'bloqueio_parecer', 'solicitacao_retificacao', 'aceite_retificacao', 'recusa_retificacao'
    referencia_id VARCHAR(100), -- ID do lote ou ID do atendimento
    descricao TEXT NOT NULL,
    detalhes_json JSONB
);

CREATE INDEX IF NOT EXISTS idx_logs_cnpj ON public.logs_auditoria(cnpj_clinica);
CREATE INDEX IF NOT EXISTS idx_logs_created_at ON public.logs_auditoria(created_at);
CREATE INDEX IF NOT EXISTS idx_logs_tipo_entidade ON public.logs_auditoria(tipo_entidade);
CREATE INDEX IF NOT EXISTS idx_logs_acao ON public.logs_auditoria(acao);

ALTER TABLE public.logs_auditoria ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Permitir leitura de logs para autenticados" ON public.logs_auditoria;
DROP POLICY IF EXISTS "Permitir insercao de logs para autenticados" ON public.logs_auditoria;

CREATE POLICY "Permitir leitura de logs para autenticados" 
ON public.logs_auditoria FOR SELECT TO authenticated USING (true);

CREATE POLICY "Permitir insercao de logs para autenticados" 
ON public.logs_auditoria FOR INSERT TO authenticated WITH CHECK (true);
