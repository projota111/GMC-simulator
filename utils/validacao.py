"""
Validações críticas e alertas – GMC Simulator
"""
from __future__ import annotations
from dataclasses import dataclass, field
from tabelas import PRODUTOS, MERCADOS


@dataclass
class Alerta:
    tipo: str   # "erro" | "aviso" | "info"
    msg: str


def validar_decisoes(decisoes: dict, estado: dict) -> list[Alerta]:
    """
    Executa todas as validações antes de simular.
    Retorna lista de alertas (erros bloqueantes + avisos).
    """
    alertas: list[Alerta] = []

    # -----------------------------------------------------------------------
    # Preços
    # -----------------------------------------------------------------------
    for p in PRODUTOS:
        for m in MERCADOS:
            preco = decisoes.get("precos", {}).get(p, {}).get(m, 0)
            if preco < 0:
                alertas.append(Alerta("erro", f"Preço negativo: {p} {m}"))

    # -----------------------------------------------------------------------
    # Tempo de montagem mínimo
    # -----------------------------------------------------------------------
    from tabelas import TEMPO_MONTAGEM_MIN
    for p in PRODUTOS:
        tm = decisoes.get("tempo_montagem", {}).get(p, 0)
        if tm < TEMPO_MONTAGEM_MIN[p]:
            alertas.append(Alerta(
                "erro",
                f"Tempo montagem {p} ({tm} min) abaixo do mínimo ({TEMPO_MONTAGEM_MIN[p]} min)"
            ))

    # -----------------------------------------------------------------------
    # Turnos
    # -----------------------------------------------------------------------
    turnos = decisoes.get("turnos", 1)
    if turnos not in (1, 2, 3):
        alertas.append(Alerta("erro", f"Número de turnos inválido: {turnos}"))
        turnos = 1  # usar valor seguro para continuar validações

    # -----------------------------------------------------------------------
    # Capacidade produtiva vs entregas planeadas
    # -----------------------------------------------------------------------
    from tabelas import (HORAS_MAQUINA_POR_TURNO, HORAS_ESP_TOTAL,
                         TEMPO_MAQUINACAO, TEMPO_MONTAGEM_MIN)
    num_maquinas   = estado.get("maquinas", 0)
    eficiencia     = estado.get("eficiencia_maquinas", 100.0)
    num_esp        = estado.get("operarios_esp", 0)

    horas_maq_disp = num_maquinas * HORAS_MAQUINA_POR_TURNO[turnos]
    horas_esp_disp = num_esp * HORAS_ESP_TOTAL

    entregas = decisoes.get("entregas", {})
    total_por_produto: dict[str, int] = {}
    for p in PRODUTOS:
        total = sum(entregas.get(p, {}).get(m, 0) for m in MERCADOS)
        total_por_produto[p] = total

    horas_maq_necessarias = sum(
        total_por_produto[p] * TEMPO_MAQUINACAO[p] / 60.0
        for p in PRODUTOS
    )
    tm_dec = decisoes.get("tempo_montagem", TEMPO_MONTAGEM_MIN)
    horas_esp_necessarias = sum(
        total_por_produto[p] * tm_dec.get(p, TEMPO_MONTAGEM_MIN[p]) / 60.0
        for p in PRODUTOS
    )

    if horas_maq_necessarias > horas_maq_disp * 1.05:
        alertas.append(Alerta(
            "aviso",
            f"Capacidade máquinas insuficiente: "
            f"necessário {horas_maq_necessarias:.0f}h, disponível {horas_maq_disp:.0f}h"
        ))
    if horas_esp_necessarias > horas_esp_disp * 1.05:
        alertas.append(Alerta(
            "erro",
            f"Mão-de-obra especializada insuficiente: "
            f"necessário {horas_esp_necessarias:.0f}h, disponível {horas_esp_disp:.0f}h"
        ))

    # -----------------------------------------------------------------------
    # Cash-flow estimado
    # -----------------------------------------------------------------------
    cash_atual = estado.get("cash", 0)
    limite_desc = estado.get("limite_financiamento", 0)
    if cash_atual < -limite_desc * 1.2:
        alertas.append(Alerta(
            "erro",
            f"Cash estimado ({cash_atual:,.0f}€) excede limite de descoberto autorizado ({limite_desc:,.0f}€)"
        ))
    elif cash_atual < -limite_desc * 0.8:
        alertas.append(Alerta(
            "aviso",
            f"Cash próximo do limite de descoberto ({cash_atual:,.0f}€ / limite {limite_desc:,.0f}€)"
        ))

    # -----------------------------------------------------------------------
    # Espaço na fábrica
    # -----------------------------------------------------------------------
    area_fabrica     = estado.get("area_fabrica", 500)
    from tabelas import (ESPACO_POR_MAQUINA, ESPACO_POR_ESP,
                         PCT_USO_FABRICA, ESPACO_WIP, ESPACO_MP_POR_1000U)
    maquinas_proximo = estado.get("maquinas", 0) + decisoes.get("maquinas", {}).get("comprar", 0)
    esp_proximo      = estado.get("operarios_esp", 0) + max(0, decisoes.get("operarios_esp", {}).get("recrutar", 0))
    espaco_usado     = maquinas_proximo * ESPACO_POR_MAQUINA + esp_proximo * ESPACO_POR_ESP
    espaco_max       = area_fabrica * PCT_USO_FABRICA

    if espaco_usado > espaco_max:
        alertas.append(Alerta(
            "aviso",
            f"Espaço insuficiente na fábrica: {espaco_usado:.0f}m² necessário, {espaco_max:.0f}m² disponível"
        ))

    # -----------------------------------------------------------------------
    # Agentes / distribuidores – entregas para mercados sem cobertura
    # -----------------------------------------------------------------------
    agentes_ue   = decisoes.get("agentes_ue", {}).get("total", estado.get("agentes_ue", 0))
    dist_nafta   = decisoes.get("dist_nafta", {}).get("total", estado.get("dist_nafta", 0))
    dist_internet = estado.get("dist_internet", 0)

    for p in PRODUTOS:
        if entregas.get(p, {}).get("UE", 0) > 0 and agentes_ue == 0:
            alertas.append(Alerta("erro", f"Entrega {p} UE planeada mas sem agentes UE"))
        if entregas.get(p, {}).get("NAFTA", 0) > 0 and dist_nafta == 0:
            alertas.append(Alerta("erro", f"Entrega {p} NAFTA planeada mas sem distribuidores NAFTA"))
        if entregas.get(p, {}).get("Internet", 0) > 0 and dist_internet == 0:
            alertas.append(Alerta("aviso", f"Entrega {p} Internet planeada mas sem distribuidor Internet"))

    # -----------------------------------------------------------------------
    # Eficiência máquinas
    # -----------------------------------------------------------------------
    if eficiencia < 75:
        alertas.append(Alerta(
            "aviso",
            f"Eficiência das máquinas baixa ({eficiencia:.1f}%) – considerar substituição"
        ))

    # -----------------------------------------------------------------------
    # Encomendas em atraso existentes
    # -----------------------------------------------------------------------
    atraso = estado.get("encomendas_atraso", {})
    for key, val in atraso.items():
        if val > 0:
            alertas.append(Alerta(
                "aviso",
                f"Encomendas em atraso: {key} = {val} unidades"
            ))

    # -----------------------------------------------------------------------
    # Dividendos vs resultados transitados
    # -----------------------------------------------------------------------
    dividendo_pct = decisoes.get("dividendo_pct", 0)
    capital_social = estado.get("capital_social", 0)
    resultados_transitados = estado.get("resultados_transitados", 0)
    if dividendo_pct > 0:
        dividendos = capital_social * dividendo_pct / 100.0
        if dividendos > resultados_transitados:
            alertas.append(Alerta(
                "erro",
                f"Dividendos ({dividendos:,.0f}€) excedem resultados transitados ({resultados_transitados:,.0f}€)"
            ))

    return alertas
