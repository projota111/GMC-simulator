"""
Cálculos de produção e distribuição – GMC Simulator
"""
from __future__ import annotations
import math
from tabelas import (
    TEMPO_MAQUINACAO, TEMPO_MONTAGEM_MIN, MP_POR_PRODUTO,
    HORAS_MAQUINA_POR_TURNO, OPERARIOS_NAO_ESP_POR_MAQUINA,
    HORAS_ESP_TOTAL, HORAS_GREVE_POR_SEMANA,
    CUSTO_SUPERVISAO_POR_TURNO, CUSTO_OVERHEAD_POR_MAQUINA,
    CUSTO_OPERACAO_POR_HORA, CUSTO_PLANEAMENTO_POR_UNIDADE,
    CUSTO_INSPECAO_POR_UNIDADE,
    CUSTO_DIARIO_CONTENTOR, DIST_PORTO_NAFTA_KM,
    CUSTO_TRAVESSIA_ATLANTICO, DIST_DISTRIBUIDOR_INTERNET_KM,
    KM_MAX_DIA, CAPACIDADE_CONTENTOR,
    GASTOS_GERAIS_COMPRAS_TRIMESTRE, PENALIZACAO_COMPRA_IMPREVISTA,
    CUSTO_MP_EXTRA_PCT,
    VALOR_SUCATA, CUSTO_INSPECAO_POR_UNIDADE,
    PRODUTOS, MERCADOS,
    HORAS_NAO_ESP_BASE, HORAS_NAO_ESP_SABADO, HORAS_NAO_ESP_DOMINGO,
    SUBSIDIO_TURNO, PCT_SALARIO_NAO_ESP, HORAS_MIN_NAO_ESP_TRIMESTRE,
    HORAS_ESP_BASE, HORAS_ESP_SABADO, HORAS_ESP_DOMINGO,
    CO2_AQUECIMENTO_KG_M2, CO2_MAQUINACAO_KG_HORA,
    CO2_MONTAGEM_KG_HORA, CUSTO_CO2_POR_TONELADA,
    ESPACO_POR_MAQUINA, ESPACO_POR_ESP, ESPACO_MP_POR_1000U, ESPACO_WIP,
    PCT_USO_FABRICA,
)


# ---------------------------------------------------------------------------
# Capacidade de máquinas
# ---------------------------------------------------------------------------

def horas_maquina_disponiveis(num_maquinas: int, turnos: int,
                               eficiencia_pct: float,
                               horas_avaria: float = 0.0) -> float:
    """Horas-máquina disponíveis no trimestre (após avarias)."""
    horas_brutas = num_maquinas * HORAS_MAQUINA_POR_TURNO[turnos]
    horas_uteis  = max(0.0, horas_brutas - horas_avaria)
    return horas_uteis  # eficiência afecta o tempo efectivo por unidade, não as horas disponíveis


def tempo_maquinacao_efectivo(produto: str, eficiencia_pct: float) -> float:
    """Tempo de maquinação ajustado pela eficiência (minutos/unidade)."""
    return TEMPO_MAQUINACAO[produto] * (100.0 / max(1.0, eficiencia_pct))


def unidades_maquinaveis(horas_disp: float, plano: dict[str, int],
                          eficiencia_pct: float) -> dict[str, int]:
    """
    Dada uma carteira de produção planeada, limita pelo tecto de maquinação.
    Distribui proporcionalmente ao plano se insuficiente.
    """
    horas_necessarias = sum(
        plano[p] * tempo_maquinacao_efectivo(p, eficiencia_pct) / 60.0
        for p in PRODUTOS
    )
    if horas_necessarias <= horas_disp or horas_necessarias == 0:
        return dict(plano)
    ratio = horas_disp / horas_necessarias
    return {p: int(plano[p] * ratio) for p in PRODUTOS}


# ---------------------------------------------------------------------------
# Capacidade de montagem (operários especializados)
# ---------------------------------------------------------------------------

def horas_esp_disponiveis(num_esp: int, semanas_greve: int = 0,
                           absentismo_horas: float = 0.0) -> float:
    """Horas-homem especializado disponíveis no trimestre."""
    horas_greve = semanas_greve * HORAS_GREVE_POR_SEMANA * num_esp
    return max(0.0, num_esp * HORAS_ESP_TOTAL - horas_greve - absentismo_horas)


def unidades_montaveis(horas_disp: float, plano: dict[str, int],
                        tempos_montagem: dict[str, int]) -> dict[str, int]:
    """Limita o plano pela capacidade de montagem; distribui proporcionalmente."""
    horas_necessarias = sum(
        plano[p] * tempos_montagem[p] / 60.0 for p in PRODUTOS
    )
    if horas_necessarias <= horas_disp or horas_necessarias == 0:
        return dict(plano)
    ratio = horas_disp / horas_necessarias
    return {p: int(plano[p] * ratio) for p in PRODUTOS}


# ---------------------------------------------------------------------------
# Matéria-prima
# ---------------------------------------------------------------------------

def mp_necessaria(plano_producao: dict[str, int],
                  rejeitados: dict[str, int] | None = None) -> int:
    """Unidades de MP consumidas pelo plano (incluindo rejeitados)."""
    rej = rejeitados or {p: 0 for p in PRODUTOS}
    return sum(
        (plano_producao[p] + rej[p]) * MP_POR_PRODUTO[p]
        for p in PRODUTOS
    )


def calcular_rejeitados(plano_producao: dict[str, int],
                         taxa_rejeicao_pct: float) -> dict[str, int]:
    """Estimativa de unidades rejeitadas pelo controlo de qualidade."""
    return {p: int(plano_producao[p] * taxa_rejeicao_pct / 100.0)
            for p in PRODUTOS}


def taxa_rejeicao_estimada(tempo_montagem: dict[str, int],
                            qualidade_mp_extra_pct: dict[str, float],
                            motivacao_score: float = 1.0) -> dict[str, float]:
    """
    Estima taxa de rejeição (%) por produto.
    Quanto maior o tempo de montagem e a qualidade MP, menor a rejeição.
    Modelo simplificado – calibrar com histórico.
    """
    taxas = {}
    for p in PRODUTOS:
        t_min = TEMPO_MONTAGEM_MIN[p]
        t_dec = max(t_min, tempo_montagem[p])
        # Redução de 0.5% base, melhorada pelo tempo extra de montagem
        factor_tempo = t_min / t_dec          # 1.0 quando no mínimo → pior
        factor_mp    = 1.0 - qualidade_mp_extra_pct[p] / 200.0
        taxa_base    = 3.0 * factor_tempo * factor_mp / motivacao_score
        taxas[p] = max(0.1, min(10.0, taxa_base))
    return taxas


# ---------------------------------------------------------------------------
# Custos de produção
# ---------------------------------------------------------------------------

def custo_maquinacao(num_maquinas: int, turnos: int,
                      horas_utilizadas: float,
                      unidades_planeadas: int) -> float:
    """Custo de operação das máquinas no trimestre."""
    return (
        num_maquinas * CUSTO_OVERHEAD_POR_MAQUINA
        + turnos * CUSTO_SUPERVISAO_POR_TURNO
        + horas_utilizadas * CUSTO_OPERACAO_POR_HORA
        + unidades_planeadas * CUSTO_PLANEAMENTO_POR_UNIDADE
    )


def custo_controlo_qualidade(unidades_montadas: int) -> float:
    return unidades_montadas * CUSTO_INSPECAO_POR_UNIDADE


def custo_salarios_nao_esp(num_nao_esp: int, horas_utilizadas: float,
                            turnos: int, salario_hora_esp: float,
                            num_nao_esp_necessarios: int) -> float:
    """
    Salários dos operários não especializados.
    salario_hora_nao_esp = 65% do salário base dos especializados.
    Trabalhadores em excesso (acima dos necessários) pagos ao mesmo valor médio.
    Garante mínimo de HORAS_MIN_NAO_ESP_TRIMESTRE horas pagas.
    """
    sal_nao_esp = salario_hora_esp * PCT_SALARIO_NAO_ESP
    subsidio = SUBSIDIO_TURNO[turnos]

    # Horas por trabalhador (iguais às da tabela 16 mas com estrutura de 1 turno base)
    if turnos == 1:
        horas_por_hom = HORAS_NAO_ESP_BASE + HORAS_NAO_ESP_SABADO + HORAS_NAO_ESP_DOMINGO
        # sáb +50%, dom +100%
        horas_base_eq = (HORAS_NAO_ESP_BASE
                         + HORAS_NAO_ESP_SABADO * 1.5
                         + HORAS_NAO_ESP_DOMINGO * 2.0)
    else:  # 2 ou 3 turnos
        horas_por_hom = HORAS_NAO_ESP_BASE + HORAS_NAO_ESP_SABADO + HORAS_NAO_ESP_DOMINGO
        horas_base_eq = (HORAS_NAO_ESP_BASE
                         + HORAS_NAO_ESP_SABADO * 1.5
                         + HORAS_NAO_ESP_DOMINGO * 2.0)

    horas_por_hom = max(HORAS_MIN_NAO_ESP_TRIMESTRE, horas_por_hom)
    custo_por_hom = horas_por_hom * sal_nao_esp * (1 + subsidio)
    return num_nao_esp * custo_por_hom


def custo_salarios_esp(num_esp: int, horas_utilizadas: float,
                        salario_hora_esp: float,
                        salario_hora_nao_esp_medio: float) -> float:
    """
    Salários dos operários especializados.
    Inclui horas ao salário base + sáb (+50%) + dom (+100%).
    Se remuneração média semanal for inferior à dos não-esp, são pagos por essa base.
    """
    if num_esp == 0 or horas_utilizadas == 0:
        return 0.0
    horas_base = HORAS_ESP_BASE
    horas_sab  = HORAS_ESP_SABADO
    horas_dom  = HORAS_ESP_DOMINGO
    custo_por_hom = (
        horas_base * salario_hora_esp
        + horas_sab * salario_hora_esp * 1.5
        + horas_dom * salario_hora_esp * 2.0
    )
    # Mínimo: remuneração dos não-esp × semanas trabalhadas
    semanas = HORAS_ESP_TOTAL / 48.0  # ~12 semanas / trimestre
    minimo_por_hom = salario_hora_nao_esp_medio * semanas * 48
    custo_por_hom = max(custo_por_hom, minimo_por_hom)
    return num_esp * custo_por_hom


# ---------------------------------------------------------------------------
# Transportes
# ---------------------------------------------------------------------------

def num_contentores(entregas: dict[str, int]) -> dict[str, int]:
    """Número de contentores necessários por mercado (cargas parciais = inteiro)."""
    result = {}
    for mercado in MERCADOS:
        total_unidades = sum(
            math.ceil(entregas.get(f"{p}_{mercado}", 0) / CAPACIDADE_CONTENTOR[p])
            for p in PRODUTOS
            if entregas.get(f"{p}_{mercado}", 0) > 0
        )
        result[mercado] = total_unidades
    return result


def dias_viagem(mercado: str, num_agentes_ue: int = 1) -> float:
    """Dias médios por viagem para cada mercado."""
    if mercado == "NAFTA":
        dist = DIST_PORTO_NAFTA_KM
    elif mercado == "Internet":
        dist = DIST_DISTRIBUIDOR_INTERNET_KM
    else:  # UE – depende do número de agentes
        # Distância média proporcional ao raio de cobertura por agente
        dist = max(50, 2_000 / max(1, num_agentes_ue))
    return math.ceil(dist / KM_MAX_DIA)


def custo_transportes(entregas_un: dict[str, dict[str, int]],
                       num_agentes_ue: int,
                       taxa_cambio_eur_usd: float = 0.73) -> float:
    """Custo total de transporte para todos os mercados."""
    custo = 0.0
    for mercado in MERCADOS:
        total_contentores = 0
        for p in PRODUTOS:
            qtd = entregas_un.get(p, {}).get(mercado, 0)
            if qtd > 0:
                total_contentores += math.ceil(qtd / CAPACIDADE_CONTENTOR[p])

        if total_contentores == 0:
            continue

        dias = dias_viagem(mercado, num_agentes_ue)
        custo_terrestre = total_contentores * dias * CUSTO_DIARIO_CONTENTOR

        if mercado == "NAFTA":
            custo_maritimo = total_contentores * CUSTO_TRAVESSIA_ATLANTICO
            custo += custo_terrestre + custo_maritimo
        else:
            custo += custo_terrestre

    return custo


# ---------------------------------------------------------------------------
# Espaço na fábrica
# ---------------------------------------------------------------------------

def calcular_espaco_utilizado(num_maquinas: int, num_esp: int,
                               mp_unidades: int,
                               componentes: dict[str, int]) -> float:
    """Espaço utilizado na fábrica no início do próximo trimestre (m²)."""
    esp_maquinas   = num_maquinas * ESPACO_POR_MAQUINA
    esp_esp        = num_esp * ESPACO_POR_ESP
    esp_mp         = (mp_unidades / 1_000) * ESPACO_MP_POR_1000U
    esp_componentes = sum(componentes.get(p, 0) * ESPACO_WIP[p]
                          for p in PRODUTOS)
    return esp_maquinas + esp_esp + esp_mp + esp_componentes


def espaco_disponivel(area_fabrica: float,
                       espaco_utilizado: float) -> float:
    """Espaço disponível (negativo = insuficiente → armazenagem externa)."""
    return area_fabrica * PCT_USO_FABRICA - espaco_utilizado


# ---------------------------------------------------------------------------
# Pegada de carbono
# ---------------------------------------------------------------------------

def pegada_carbono(area_fabrica: float, horas_maquina: float,
                   horas_montagem: float) -> float:
    """CO2e total (kg) no trimestre."""
    co2_aquecimento = area_fabrica * CO2_AQUECIMENTO_KG_M2
    co2_maquinacao  = horas_maquina * CO2_MAQUINACAO_KG_HORA
    co2_montagem    = horas_montagem * CO2_MONTAGEM_KG_HORA
    return co2_aquecimento + co2_maquinacao + co2_montagem


def custo_compensacao_carbono(co2_kg: float) -> float:
    return (co2_kg / 1_000) * CUSTO_CO2_POR_TONELADA
