"""
Gestão de Recursos Humanos – GMC Simulator
"""
from __future__ import annotations
from tabelas import (
    OPERARIOS_NAO_ESP_POR_MAQUINA, HORAS_MIN_NAO_ESP_TRIMESTRE,
    HORAS_ESP_TOTAL, SUBSIDIO_TURNO, PCT_SALARIO_NAO_ESP,
    CUSTO_RECRUTAMENTO_ESP, CUSTO_RESCISAO_ESP, CUSTO_TREINO_ESP,
    CUSTO_RECRUTAMENTO_NAO_ESP, CUSTO_RESCISAO_NAO_ESP,
    CUSTO_CONSULTOR_DIA, SALARIO_HORA_MIN_ESP,
)


def operarios_nao_esp_necessarios(num_maquinas: int, turnos: int) -> int:
    """Número mínimo de operários não-esp para operar as máquinas."""
    return num_maquinas * OPERARIOS_NAO_ESP_POR_MAQUINA[turnos]


def ajustar_operarios_nao_esp(atual: int, necessarios: int) -> dict:
    """
    Calcula recrutas/despedidos automáticos para operários não-esp.
    Só pode despedir metade dos excedentes por trimestre.
    """
    if necessarios > atual:
        return {"recrutar": necessarios - atual, "despedir": 0}
    elif necessarios < atual:
        excedentes = atual - necessarios
        despedir = excedentes // 2  # só metade
        return {"recrutar": 0, "despedir": despedir}
    return {"recrutar": 0, "despedir": 0}


def calcular_operarios_proximo_trim(atual_esp: int, recrutar: int,
                                    treinar: int, despedir: int,
                                    abandono: int) -> int:
    """Operários especializados disponíveis no próximo trimestre."""
    return max(0, atual_esp + recrutar + treinar - despedir - abandono)


def estimar_abandono_esp(num_esp: int, salario_hora: float,
                          salario_mercado: float,
                          motivacao_score: float = 1.0) -> int:
    """
    Estima abandonos de operários esp. por trimestre.
    Simplificado – depende da competitividade salarial e motivação.
    """
    if num_esp == 0:
        return 0
    ratio_salario = salario_hora / max(salario_mercado, SALARIO_HORA_MIN_ESP)
    taxa_base = 0.05  # 5% abandona por trimestre em condições normais
    if ratio_salario < 1.0:
        taxa_base *= 1.5  # mais saídas se pagar abaixo do mercado
    elif ratio_salario > 1.15:
        taxa_base *= 0.7  # menos saídas se pagar acima
    taxa_base /= motivacao_score
    return max(0, int(num_esp * taxa_base))


def estimar_abandono_nao_esp(num_nao_esp: int,
                              motivacao_score: float = 1.0) -> int:
    """Estima abandonos de operários não-esp por trimestre."""
    if num_nao_esp == 0:
        return 0
    taxa_base = 0.03
    return max(0, int(num_nao_esp * taxa_base / motivacao_score))


def score_motivacao(salario_hora: float, salario_mercado: float,
                     orcamento_gestao: float, dias_formacao: int,
                     aviso_greve: int) -> float:
    """
    Score de motivação (0.5 – 1.5).
    Afecta rejeição, absentismo, probabilidade de greve.
    """
    score = 1.0
    # Salário comparativo
    if salario_hora >= salario_mercado * 1.10:
        score += 0.15
    elif salario_hora < salario_mercado:
        score -= 0.20
    # Orçamento de gestão (€40k = neutro)
    if orcamento_gestao >= 60_000:
        score += 0.10
    elif orcamento_gestao < 30_000:
        score -= 0.15
    # Formação
    if dias_formacao >= 10:
        score += 0.10
    # Greve prevista
    if aviso_greve > 0:
        score -= 0.20
    return max(0.5, min(1.5, score))


def risco_greve(score_motivacao: float,
                 semanas_greve_anteriores: int = 0) -> str:
    """Nível de risco de greve: 'baixo' | 'médio' | 'alto'."""
    if score_motivacao >= 1.1 and semanas_greve_anteriores == 0:
        return "baixo"
    elif score_motivacao >= 0.9:
        return "médio"
    return "alto"


def custo_total_rh(recrutar_esp: int, despedir_esp: int,
                   treinar_nao_esp: int,
                   recrutar_nao_esp: int, despedir_nao_esp: int,
                   dias_formacao: int) -> float:
    return (
        max(0, recrutar_esp) * CUSTO_RECRUTAMENTO_ESP
        + max(0, despedir_esp) * CUSTO_RESCISAO_ESP
        + treinar_nao_esp * CUSTO_TREINO_ESP
        + max(0, recrutar_nao_esp) * CUSTO_RECRUTAMENTO_NAO_ESP
        + max(0, despedir_nao_esp) * CUSTO_RESCISAO_NAO_ESP
        + dias_formacao * CUSTO_CONSULTOR_DIA
    )
