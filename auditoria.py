"""
=============================================================================
SISTEMA DE FISCALIZAÇÃO E PRESTAÇÃO DE CONTAS - CARTÃO CASTRAÇÃO (SEPAN)
Módulo de Histórico de Auditoria e Rastreabilidade: auditoria.py
=============================================================================
Responsável por:
1. Gravação padronizada de eventos e alterações (atendimentos, lotes, pareceres).
2. Consulta de logs de auditoria com tipagem segura e tratamento de erros.
=============================================================================
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from supabase import Client


def registrar_log_auditoria(
    supabase: Client,
    cnpj_clinica: str,
    nome_clinica: str,
    tipo_entidade: str,
    acao: str,
    descricao: str,
    referencia_id: str = None,
    detalhes: dict = None
):
    """
    Registra um evento de auditoria no banco de dados.
    Falhas na gravação do log não interrompem a operação principal do usuário.
    """
    try:
        user = st.session_state.get("user")
        user_email = user.email if user and hasattr(user, "email") else getattr(user, "email", "Sistema")
        user_tipo = "clinica" if st.session_state.get("user_role") == "clinica" else "comissao"

        payload = {
            "cnpj_clinica": str(cnpj_clinica or "").strip(),
            "nome_clinica": str(nome_clinica or "").strip(),
            "usuario_email": str(user_email or "").strip(),
            "usuario_tipo": user_tipo,
            "tipo_entidade": str(tipo_entidade or "").strip(),
            "acao": str(acao or "").strip(),
            "descricao": str(descricao or "").strip(),
            "referencia_id": str(referencia_id or "").strip() if referencia_id else None,
            "detalhes_json": detalhes if isinstance(detalhes, dict) else None,
            "created_at": datetime.now().isoformat()
        }

        try:
            supabase.table("logs_auditoria").insert(payload).execute()
        except Exception:
            # Fallback silencioso se tabela não existir ainda no Supabase
            pass
    except Exception:
        pass


def fetch_logs_auditoria(_supabase: Client) -> pd.DataFrame:
    """Busca os registros de log de auditoria no Supabase."""
    try:
        response = (
            _supabase.table("logs_auditoria")
            .select("*")
            .order("created_at", desc=True)
            .limit(1000)
            .execute()
        )
        data = response.data or []
        if not data:
            return pd.DataFrame()

        df = pd.DataFrame(data)
        if "created_at" in df.columns:
            df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")
        return df
    except Exception:
        return pd.DataFrame()
