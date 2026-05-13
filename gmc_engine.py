"""
GMC Engine – Motor de simulação do Global Management Challenge
Classe principal: Empresa
"""
from __future__ import annotations
import math
import copy
from dataclasses import dataclass, field
from typing import Any

from tabelas import (
    PRODUTOS, MERCADOS,
    HORAS_MAQUINA_POR_TURNO, OPERARIOS_NAO_ESP_POR_MAQUINA,
    HORAS_ESP_TOTAL, HORAS_GREVE_POR_SEMANA,
    CUSTO_MAQUINA, TAXA_AMORTIZACAO_TRIM, CUSTO_DESMONTAGEM,
    TEMPO_MAQUINACAO, TEMPO_MONTAGEM_MIN, MP_POR_PRODUTO,
    CUSTO_SUPERVISAO_POR_TURNO, CUSTO_OVERHEAD_POR_MAQUINA,
    CUSTO_OPERACAO_POR_HORA, CUSTO_PLANEAMENTO_POR_UNIDADE,
    CUSTO_INSPECAO_POR_UNIDADE,
    VALOR_SUCATA, CUSTO_GARANTIA,
    SUBSIDIO_TURNO, PCT_SALARIO_NAO_ESP,
    HORAS_ESP_BASE, HORAS_ESP_SABADO, HORAS_ESP_DOMINGO,
    HORAS_MIN_NAO_ESP_TRIMESTRE,
    TAXA_EMPRESTIMO_PRAZO_ANUAL, TAXA_IMPOSTO,
    FATOR_VALORIZACAO_MP, FATOR_VALORIZACAO_PRODUTOS,
    CUSTO_MP_EXTRA_PCT, PENALIZACAO_COMPRA_IMPREVISTA,
    GASTOS_GERAIS_COMPRAS_TRIMESTRE,
    ARMAZENAGEM_PRODUTO_UE_INTERNET, ARMAZENAGEM_PRODUTO_NAFTA_USD,
    CUSTOS_FIXOS_FABRICA_M2,
    AGENTE_APOIO_MINIMO, AGENTE_CUSTO_ANGARIACAO, AGENTE_CUSTO_RESCISAO,
    ISP_CUSTO_POR_PORTA, ISP_PCT_VENDAS, ISP_CUSTO_ADESAO, ISP_CUSTO_RESCISAO,
    SEGUROS,
    CUSTO_CONTROLO_CREDITO_UE_NAFTA, CUSTO_CARTAO_CREDITO_INTERNET,
    CO2_AQUECIMENTO_KG_M2, CO2_MAQUINACAO_KG_HORA, CO2_MONTAGEM_KG_HORA,
    CUSTO_CO2_POR_TONELADA,
    ESPACO_POR_MAQUINA, ESPACO_POR_ESP, ESPACO_MP_POR_1000U, ESPACO_WIP,
    PCT_USO_FABRICA, PRAZO_PAGAMENTO_CLIENTE,
    calcular_limite_financiamento, calcular_potencial_credito,
    calcular_capacidade_credito,
    taxa_deposito, taxa_financiamento_autorizado, taxa_financiamento_nao_autorizado,
    CUSTO_CONSERVACAO_HORA, CUSTO_CONSERVACAO_EMERGENCIA,
    CAPACIDADE_CONTENTOR, CUSTO_DIARIO_CONTENTOR,
    DIST_PORTO_NAFTA_KM, CUSTO_TRAVESSIA_ATLANTICO,
    DIST_DISTRIBUIDOR_INTERNET_KM, KM_MAX_DIA,
    CUSTO_RECRUTAMENTO_ESP, CUSTO_RESCISAO_ESP, CUSTO_TREINO_ESP,
    CUSTO_RECRUTAMENTO_NAO_ESP, CUSTO_RESCISAO_NAO_ESP, CUSTO_CONSULTOR_DIA,
    SALARIO_HORA_MIN_ESP,
)
from utils.validacao import validar_decisoes, Alerta


# ---------------------------------------------------------------------------
# Estado inicial de referência (Y15Q1 – histórico)
# ---------------------------------------------------------------------------
ESTADO_INICIAL_PADRAO = {
    # Fábrica e espaço
    "area_terreno_total": 1_000,   # m²
    "area_estacionamento": 200,    # m²
    "area_fabrica": 500,           # m² (construída)
    # Máquinas
    "maquinas": 2,
    "eficiencia_maquinas": 100.0,  # %
    "valor_maquinas": 585_000,     # € (2 máq × 300k − 2.5% deprec)
    # Trabalhadores
    "operarios_esp": 11,           # disponíveis para Q2
    "operarios_nao_esp": 0,        # calculado automaticamente
    # Agentes / distribuidores
    "agentes_ue": 2,
    "dist_nafta": 0,
    "dist_internet": 0,
    "portas_website": 0,
    # Inventários (unidades)
    "inventario_mp": 0,            # MP em stock
    "mp_proximo_trim": 3_000,      # MP encomendada para o próximo trim
    "mp_seguinte_trim": 0,         # MP encomendada para 2 trims à frente
    "componentes": {"P1": 0, "P2": 0, "P3": 0},
    "inventario_produtos": {
        "P1": {"UE": 0, "NAFTA": 0, "Internet": 0},
        "P2": {"UE": 0, "NAFTA": 0, "Internet": 0},
        "P3": {"UE": 0, "NAFTA": 0, "Internet": 0},
    },
    "encomendas_atraso": {
        "P1_UE": 0, "P1_NAFTA": 0,
        "P2_UE": 0, "P2_NAFTA": 0,
        "P3_UE": 0, "P3_NAFTA": 0,
    },
    # Financeiro
    "cash": 2_833_842,             # Caixa + equivalentes (inclui depósito)
    "deposito_prazo": 2_400_000,   # € em depósito a prazo
    "emprestimo_prazo": 0,
    "capital_social": 4_000_000,   # valor nominal × nº acções
    "num_acoes": 4_000_000,        # acções (€1 nominal cada)
    "premios_emissao": 0,
    "resultados_transitados": -239_763,
    "clientes": 0,
    "fornecedores": 100_968,
    "impostos_pagar": 0,
    "terreno": 50_000,
    "edificios": 250_000,
    "lucro_tributavel_acumulado": -239_763,
    # Parâmetros de mercado (actualizados a cada trimestre)
    "taxa_bce_ue": 0.015,          # 1.5% a.a.
    "taxa_cambio_eur_usd": 0.73,   # €/$
    "preco_mp_spot_usd": 74_574,   # $ / 1000 unidades
    "preco_mp_3m_usd": 73_402,
    "preco_mp_6m_usd": 72_229,
    "custo_construcao_m2": 500,
    # Imagem (simplificado)
    "imagem_produtos": {"P1": 2.0, "P2": 2.0, "P3": 2.0},  # estrelas (1-5)
    "imagem_empresa": 2.0,
    "imagem_website": 0.0,
    # Controlo
    "trimestre": 2,    # próximo trimestre a simular
    "ano": 2015,
    "aviso_greve": 0,  # semanas de greve anunciadas
    "plano_seguro": 0,
    "limite_financiamento": 120_000,
    "potencial_credito": 1_706_000,
}


# ---------------------------------------------------------------------------
# Classe principal
# ---------------------------------------------------------------------------

class Empresa:
    """Motor de simulação GMC – representa uma empresa ao longo dos trimestres."""

    def __init__(self, estado: dict | None = None):
        self.estado = copy.deepcopy(estado or ESTADO_INICIAL_PADRAO)

    # ------------------------------------------------------------------
    # Método principal
    # ------------------------------------------------------------------

    def simular_trimestre(self, decisoes: dict) -> dict:
        """
        Simula um trimestre completo dado um conjunto de decisões.
        Devolve o relatório de gestão calculado e actualiza o estado interno.
        """
        e = self.estado
        d = decisoes
        alertas: list[Alerta] = validar_decisoes(d, e)

        # =================================================================
        # 0. Parâmetros do trimestre (actualizados pelas decisões ou estado)
        # =================================================================
        trimestre        = e["trimestre"]
        ano              = e["ano"]
        taxa_bce         = e.get("taxa_bce_ue", 0.015)
        taxa_cambio      = e.get("taxa_cambio_eur_usd", 0.73)
        preco_mp_spot    = e.get("preco_mp_spot_usd", 74_574)
        preco_mp_3m      = e.get("preco_mp_3m_usd", 73_402)
        preco_mp_6m      = e.get("preco_mp_6m_usd", 72_229)
        custo_constr_m2  = e.get("custo_construcao_m2", 500)

        # =================================================================
        # 1. RECURSOS HUMANOS – operários especializados
        # =================================================================
        recrutar_esp  = max(0, d.get("operarios_esp", {}).get("recrutar", 0))
        treinar_n_esp = max(0, d.get("operarios_esp", {}).get("treinar", 0))
        despedir_esp  = max(0, d.get("operarios_esp", {}).get("despedir", 0))
        salario_hora  = max(SALARIO_HORA_MIN_ESP,
                            d.get("operarios_esp", {}).get("salario_hora", e.get("salario_hora", 9.0)) / 100.0)
        # salário em cêntimos na decisão → converter para €
        salario_hora_eur = salario_hora  # já em €

        aviso_greve      = e.get("aviso_greve", 0)
        semanas_greve    = aviso_greve
        absentismo_hrs   = e.get("absentismo_horas", 0.0)

        # Abandono estimado (simplificado)
        salario_mercado  = e.get("salario_mercado_esp", salario_hora_eur)
        abandono_esp     = int(e["operarios_esp"] * 0.05)  # 5% por trimestre
        # Novos esp só disponíveis no próximo trimestre (não afectam produção deste)
        esp_producao     = e["operarios_esp"] - despedir_esp  # já despedidos início trim
        esp_proximo_trim = max(0, esp_producao + recrutar_esp + treinar_n_esp - abandono_esp)

        # Operários não-esp (automático)
        turnos           = d.get("turnos", e.get("turnos", 1))
        num_maquinas_prod = e["maquinas"]  # máquinas disponíveis ESTE trimestre
        nao_esp_necessarios = num_maquinas_prod * OPERARIOS_NAO_ESP_POR_MAQUINA[turnos]
        nao_esp_atual    = e.get("operarios_nao_esp", nao_esp_necessarios)
        # Ajuste automático (recruta/despede até metade dos excedentes)
        if nao_esp_necessarios > nao_esp_atual:
            recrutar_nao_esp = nao_esp_necessarios - nao_esp_atual
            despedir_nao_esp = 0
        else:
            excedentes = nao_esp_atual - nao_esp_necessarios
            despedir_nao_esp = excedentes // 2
            recrutar_nao_esp = 0
        nao_esp_producao  = nao_esp_atual - despedir_nao_esp + recrutar_nao_esp

        # =================================================================
        # 2. MÁQUINAS – investimento e amortização
        # =================================================================
        maquinas_comprar  = d.get("maquinas", {}).get("comprar", 0)
        maquinas_vender   = min(d.get("maquinas", {}).get("vender", 0), num_maquinas_prod)
        # Máquinas disponíveis ESTE trimestre (antes de comprar novas)
        num_maquinas_prod = num_maquinas_prod - maquinas_vender
        # Máquinas novas instaladas no FIM deste trimestre → disponíveis no PRÓXIMO
        maquinas_proximo  = num_maquinas_prod + maquinas_comprar

        # Amortização
        valor_maq_vendidas = maquinas_vender * (e["valor_maquinas"] / max(1, e["maquinas"] + maquinas_vender))
        depreciacao        = (e["valor_maquinas"] - valor_maq_vendidas) * TAXA_AMORTIZACAO_TRIM
        valor_maq_fim      = (e["valor_maquinas"] - valor_maq_vendidas - depreciacao
                              + maquinas_comprar * CUSTO_MAQUINA)

        # Eficiência (simplificado: conservação retarda degradação)
        horas_conservacao   = d.get("horas_conservacao", d.get("conservacao_horas_maquina", 0))
        eficiencia_anterior = e.get("eficiencia_maquinas", 100.0)
        degradacao          = max(0, 2.0 - horas_conservacao * 0.05)
        eficiencia_nova     = max(50.0, eficiencia_anterior - degradacao)
        # Máquinas novas restauram eficiência ponderada
        if maquinas_proximo > 0:
            eficiencia_nova = (eficiencia_nova * num_maquinas_prod
                               + 100.0 * maquinas_comprar) / maquinas_proximo

        # Avarias (simplificado: probabilidade baixa)
        horas_avaria = 0.0  # determinístico (sem eventos aleatórios base)

        # =================================================================
        # 3. EXPANSÃO DA FÁBRICA
        # =================================================================
        expansao_m2     = d.get("expansao_fabrica", d.get("extensao_fabrica", 0))
        area_fabrica    = e["area_fabrica"]
        area_disponivel = e["area_terreno_total"] * 0.80 - area_fabrica - e.get("area_estacionamento", 200)
        expansao_real   = min(expansao_m2, max(0, area_disponivel))
        custo_expansao  = expansao_real * custo_constr_m2
        # Expansão fica disponível no próximo trimestre
        area_fabrica_proximo = area_fabrica + expansao_real

        # =================================================================
        # 4. MATÉRIA-PRIMA
        # =================================================================
        # Inventário inicial = stock anterior + encomendas que chegam agora
        mp_inicial = e["inventario_mp"] + e.get("mp_proximo_trim", 0)

        # Encomendas desta decisão
        _compra_mp  = d.get("compra_mp", d.get("materia_prima", {}))
        mp_enc_spot = _compra_mp.get("spot", _compra_mp.get("ocasiao", 0))
        mp_enc_3m   = _compra_mp.get("3m",   _compra_mp.get("3_meses", 0))
        mp_enc_6m   = _compra_mp.get("6m",   _compra_mp.get("6_meses", 0))

        # Custo da MP encomendada a spot (pago 50% agora)
        custo_mp_spot_usd  = mp_enc_spot * preco_mp_spot / 1_000
        custo_mp_3m_usd    = mp_enc_3m   * preco_mp_3m  / 1_000
        custo_mp_6m_usd    = mp_enc_6m   * preco_mp_6m  / 1_000
        custo_mp_total_eur = (custo_mp_spot_usd + custo_mp_3m_usd + custo_mp_6m_usd) * taxa_cambio

        # =================================================================
        # 5. SUBCONTRATAÇÃO (componentes chegam no próximo trim)
        # =================================================================
        subcontratacao = {p: d.get("subcontratacao", {}).get(p, 0) for p in PRODUTOS}
        # Componentes disponíveis ESTE trimestre = stock anterior
        componentes_disponiveis = {p: e["componentes"].get(p, 0) for p in PRODUTOS}
        # Componentes subcontratados agora chegam no PRÓXIMO trimestre
        componentes_proximo_trim = {p: subcontratacao[p] for p in PRODUTOS}

        # =================================================================
        # 6. PLANO DE ENTREGAS E PRODUÇÃO
        # =================================================================
        entregas_plan = d.get("entregas", {})
        plano_producao: dict[str, int] = {}
        for p in PRODUTOS:
            total_p = sum(max(0, entregas_plan.get(p, {}).get(m, 0)) for m in MERCADOS)
            plano_producao[p] = total_p

        # Tempo de montagem decidido
        tempo_montagem = {
            p: max(TEMPO_MONTAGEM_MIN[p], d.get("tempo_montagem", {}).get(p, TEMPO_MONTAGEM_MIN[p]))
            for p in PRODUTOS
        }

        # --- Limite 1: capacidade de montagem (operários especializados) ---
        horas_esp_disp = max(0.0,
            esp_producao * HORAS_ESP_TOTAL
            - semanas_greve * HORAS_GREVE_POR_SEMANA * esp_producao
            - absentismo_hrs
        )
        horas_esp_necessarias = sum(
            plano_producao[p] * tempo_montagem[p] / 60.0 for p in PRODUTOS
        )
        if horas_esp_necessarias > horas_esp_disp and horas_esp_necessarias > 0:
            ratio = horas_esp_disp / horas_esp_necessarias
            plano_producao = {p: int(plano_producao[p] * ratio) for p in PRODUTOS}
            alertas.append(Alerta("aviso",
                f"Produção limitada por montagem: rácio {ratio:.2%}"))

        # --- Limite 2: capacidade de máquinas ---
        horas_maq_disp = (num_maquinas_prod * HORAS_MAQUINA_POR_TURNO[turnos]
                           - horas_avaria)
        tempo_maq_eff = {p: TEMPO_MAQUINACAO[p] * 100.0 / max(1.0, eficiencia_anterior)
                         for p in PRODUTOS}
        horas_maq_necessarias = sum(
            plano_producao[p] * tempo_maq_eff[p] / 60.0 for p in PRODUTOS
        )
        if horas_maq_necessarias > horas_maq_disp and horas_maq_necessarias > 0:
            ratio = horas_maq_disp / horas_maq_necessarias
            plano_producao = {p: int(plano_producao[p] * ratio) for p in PRODUTOS}
            alertas.append(Alerta("aviso",
                f"Produção limitada por máquinas: rácio {ratio:.2%}"))

        # --- Limite 3: MP disponível (inclui spot, emergência automática) ---
        mp_necessaria_total = sum(
            plano_producao[p] * MP_POR_PRODUTO[p] for p in PRODUTOS
        )
        # MP disponível = inicial + spot encomendado agora (entrega imediata) + componentes
        mp_disponivel = mp_inicial + mp_enc_spot
        mp_emergencia = 0
        if mp_necessaria_total > mp_disponivel:
            mp_emergencia = mp_necessaria_total - mp_disponivel
            alertas.append(Alerta("aviso",
                f"Compra de emergência de MP: {mp_emergencia:,} unidades"))

        # MP extra (qualidade)
        pct_mp_extra = d.get("mp_extra_pct", d.get("materia_prima_extra_pct", {}))

        # --- Taxa de rejeição (simplificado) ---
        taxa_rej_pct = {}
        for p in PRODUTOS:
            t_min = TEMPO_MONTAGEM_MIN[p]
            t_dec = tempo_montagem[p]
            factor = t_min / t_dec
            mp_extra_p = pct_mp_extra.get(p, 0) / 100.0
            taxa_rej_pct[p] = max(0.1, 3.0 * factor * (1.0 - mp_extra_p * 0.5))

        rejeitados = {p: int(plano_producao[p] * taxa_rej_pct[p] / 100.0)
                      for p in PRODUTOS}
        produzidos = {p: plano_producao[p] for p in PRODUTOS}  # inclui rejeitados

        # Produzidos liquidos (para entrega)
        produzidos_liquidos = {p: produzidos[p] - rejeitados[p] for p in PRODUTOS}

        # =================================================================
        # 7. DISTRIBUIÇÃO E VENDAS
        # =================================================================
        agentes_ue_n      = d.get("agentes_ue", {}).get("total", e["agentes_ue"])
        dist_nafta_n      = d.get("dist_nafta", {}).get("total", e["dist_nafta"])
        dist_internet_n   = 1 if d.get("portas_website", e.get("portas_website", 0)) > 0 else e.get("dist_internet", 0)

        entregas_reais: dict[str, dict[str, int]] = {p: {} for p in PRODUTOS}
        inventario_produtos_fim: dict[str, dict[str, int]] = {p: {} for p in PRODUTOS}
        encomendas_atraso_fim: dict[str, int] = {}
        vendas_un: dict[str, dict[str, int]] = {p: {} for p in PRODUTOS}

        # Distribuir produção líquida proporcionalmente ao plano de entregas
        for p in PRODUTOS:
            total_planeado = sum(max(0, entregas_plan.get(p, {}).get(m, 0)) for m in MERCADOS)
            for m in MERCADOS:
                plan_m = max(0, entregas_plan.get(p, {}).get(m, 0))
                # Verificar cobertura de mercado
                if m == "UE" and agentes_ue_n == 0:
                    plan_m = 0
                if m == "NAFTA" and dist_nafta_n == 0:
                    plan_m = 0
                if m == "Internet" and dist_internet_n == 0:
                    plan_m = 0

                if total_planeado > 0 and plan_m > 0:
                    ratio_m = plan_m / total_planeado
                    entregues = int(produzidos_liquidos[p] * ratio_m)
                else:
                    entregues = 0
                entregas_reais[p][m] = entregues

        # Encomendas estimadas (modelo simplificado de procura)
        precos       = d.get("precos", {})
        publicidade  = d.get("publicidade", {})
        inovacao     = d.get("inovacao", {})
        encomendas_estimadas = self._estimar_encomendas(
            precos, publicidade, inovacao, agentes_ue_n, dist_nafta_n,
            dist_internet_n, e
        )

        for p in PRODUTOS:
            for m in MERCADOS:
                inv_anterior = e["inventario_produtos"].get(p, {}).get(m, 0)
                atraso_anterior = e["encomendas_atraso"].get(f"{p}_{m}", 0)
                entregues = entregas_reais[p][m]
                encomendas_m = encomendas_estimadas.get(p, {}).get(m, 0)

                # Vendas = min(encomendas + atraso, entregas + inv_anterior)
                oferta    = entregues + inv_anterior
                procura   = encomendas_m + atraso_anterior
                vendas_q  = min(oferta, procura)
                vendas_un[p][m] = vendas_q

                # Inventário final
                inv_fim = oferta - vendas_q
                inventario_produtos_fim[p][m] = max(0, inv_fim)

                # Encomendas em atraso (só UE e NAFTA; Internet sem atraso)
                if m in ("UE", "NAFTA"):
                    atraso_bruto = max(0, procura - oferta)
                    # Metade é cancelada
                    atraso_fim = atraso_bruto // 2
                    encomendas_atraso_fim[f"{p}_{m}"] = atraso_fim
                    if atraso_bruto > 0:
                        alertas.append(Alerta("aviso",
                            f"Encomendas em atraso {p} {m}: {atraso_fim} unidades"))
                else:
                    encomendas_atraso_fim[f"{p}_Internet"] = 0

        # =================================================================
        # 8. CUSTOS DE PRODUÇÃO
        # =================================================================
        horas_esp_usadas  = sum(produzidos[p] * tempo_montagem[p] / 60.0 for p in PRODUTOS)
        horas_maq_usadas  = sum(produzidos[p] * tempo_maq_eff[p] / 60.0 for p in PRODUTOS)
        unidades_planeadas = sum(plano_producao.values())

        custo_maquinacao = (
            num_maquinas_prod * CUSTO_OVERHEAD_POR_MAQUINA
            + turnos * CUSTO_SUPERVISAO_POR_TURNO
            + horas_maq_usadas * CUSTO_OPERACAO_POR_HORA
            + unidades_planeadas * CUSTO_PLANEAMENTO_POR_UNIDADE
        )

        # Salários não-especializados
        sal_nao_esp_hora = salario_hora_eur * PCT_SALARIO_NAO_ESP
        subsidio_t       = SUBSIDIO_TURNO[turnos]
        horas_base_nao   = HORAS_MIN_NAO_ESP_TRIMESTRE
        custo_sal_nao_esp = nao_esp_producao * horas_base_nao * sal_nao_esp_hora * (1 + subsidio_t)

        # Salários especializados
        custo_sal_esp = esp_producao * (
            HORAS_ESP_BASE * salario_hora_eur
            + HORAS_ESP_SABADO * salario_hora_eur * 1.5
            + HORAS_ESP_DOMINGO * salario_hora_eur * 2.0
        )

        # Controlo de qualidade
        unidades_montadas = sum(produzidos.values())
        custo_cq = unidades_montadas * CUSTO_INSPECAO_POR_UNIDADE

        # =================================================================
        # 9. TRANSPORTES
        # =================================================================
        custo_transp = self._calcular_transportes(entregas_reais, agentes_ue_n)

        # =================================================================
        # 10. VALORIZAÇÃO DO INVENTÁRIO FINAL
        # =================================================================
        preco_mp_min_usd = min(preco_mp_spot, preco_mp_3m, preco_mp_6m)
        preco_mp_eur_unid = FATOR_VALORIZACAO_MP * preco_mp_min_usd * taxa_cambio / 1_000

        mp_fim = max(0, (mp_inicial + mp_enc_spot + mp_emergencia
                         - mp_necessaria_total))
        # MP encomendada para futuros trimestres (já é activo)
        mp_total_activo = mp_fim + mp_enc_3m + mp_enc_6m

        val_mp_fim = preco_mp_eur_unid * mp_total_activo

        # Componentes
        componentes_fim = {p: componentes_disponiveis[p] for p in PRODUTOS}  # simplificado
        val_comp_fim    = sum(componentes_fim[p] * preco_mp_eur_unid * MP_POR_PRODUTO[p]
                              for p in PRODUTOS)

        # Produtos acabados
        val_prod_fim = 0.0
        for p in PRODUTOS:
            total_inv_p = sum(inventario_produtos_fim[p].get(m, 0) for m in MERCADOS)
            custo_unit_mp   = preco_mp_eur_unid * MP_POR_PRODUTO[p]
            fator_mp_extra  = 1.0 + pct_mp_extra.get(p, 0) / 100.0 * CUSTO_MP_EXTRA_PCT
            custo_unit_maq  = sal_nao_esp_hora * (1 + subsidio_t) * 4 * tempo_maq_eff[p] / 60.0
            custo_unit_mon  = salario_hora_eur * tempo_montagem[p] / 60.0
            custo_unit      = (custo_unit_mp * fator_mp_extra + custo_unit_maq + custo_unit_mon)
            val_prod_fim   += FATOR_VALORIZACAO_PRODUTOS * custo_unit * total_inv_p

        inventario_final_total = val_mp_fim + val_comp_fim + val_prod_fim

        # =================================================================
        # 11. DEMONSTRAÇÃO DE RESULTADOS
        # =================================================================
        # Vendas
        vendas_valor = 0.0
        val_encomendas_ue    = 0.0
        val_vendas_nafta     = 0.0
        val_vendas_internet  = 0.0
        for p in PRODUTOS:
            for m in MERCADOS:
                un   = vendas_un[p][m]
                preco = precos.get(p, {}).get(m, 0)
                v     = un * preco
                vendas_valor += v
                if m == "UE":
                    val_encomendas_ue += un * preco
                elif m == "NAFTA":
                    val_vendas_nafta += un * preco
                elif m == "Internet":
                    val_vendas_internet += un * preco

        # Sucata
        for p in PRODUTOS:
            vendas_valor += rejeitados[p] * VALOR_SUCATA[p]

        # Inventário inicial
        inv_inicial_total = e.get("_inventario_total_valor", 0.0)

        # Compra de componentes (subcontratação deste trim → activo)
        custo_componentes = sum(
            subcontratacao[p] * preco_mp_eur_unid * MP_POR_PRODUTO[p] * (
                1.0 + pct_mp_extra.get(p, 0) / 100.0 * CUSTO_MP_EXTRA_PCT
            ) for p in PRODUTOS
        )

        # Custo MP encomendada (incluindo emergência)
        custo_mp_total_eur += mp_emergencia * preco_mp_spot * taxa_cambio / 1_000 * (1 + PENALIZACAO_COMPRA_IMPREVISTA)

        custo_vendas = (
            inv_inicial_total + custo_componentes + custo_mp_total_eur
            + custo_maquinacao + custo_sal_nao_esp + custo_sal_esp
            + custo_cq + custo_transp
            - inventario_final_total
        )

        resultado_bruto = vendas_valor - custo_vendas

        # --- Despesas Administrativas ---
        # Publicidade (valores já em €)
        custo_pub = (publicidade.get("imagem_corporativa", 0)
                     + sum(publicidade.get(p, {}).get(m, 0)
                            for p in PRODUTOS for m in MERCADOS))

        # Agentes / distribuidores
        custo_agentes = self._custo_agentes(
            d, e, val_encomendas_ue, val_vendas_nafta,
            agentes_ue_n, dist_nafta_n
        )

        # Distribuidor Internet (comissão + apoio)
        apoio_int    = d.get("dist_internet", {}).get("apoio", 0)
        comissao_int = d.get("dist_internet", {}).get("comissao_pct", 0)
        custo_dist_int = val_vendas_internet * comissao_int / 100.0 + apoio_int

        # ISP
        portas_site = d.get("portas_website", e.get("portas_website", 0))
        tinha_site  = e.get("dist_internet", 0) > 0 or e.get("portas_website", 0) > 0
        tem_site    = portas_site > 0
        custo_isp   = (portas_site * ISP_CUSTO_POR_PORTA
                       + val_vendas_internet * ISP_PCT_VENDAS
                       + (ISP_CUSTO_ADESAO if tem_site and not tinha_site else 0)
                       + (ISP_CUSTO_RESCISAO if tinha_site and not tem_site else 0))

        # Departamento de vendas
        val_total_enc = val_encomendas_ue + val_vendas_nafta + val_vendas_internet
        custo_depto_vendas = val_total_enc * 0.01

        # Garantia
        unidades_reparadas = {p: int(sum(vendas_un[p].values()) * 0.02) for p in PRODUTOS}
        custo_gar = sum(unidades_reparadas[p] * CUSTO_GARANTIA[p] for p in PRODUTOS)

        # I&D (valor em €, ou por produto em inovacao dict)
        custo_id = d.get("investimento_id",
                         sum(inovacao.get(p, 0) for p in PRODUTOS))

        # Website
        custo_website = d.get("desenvolvimento_website", 0)

        # RH
        dias_form     = d.get("dias_formacao", d.get("formacao_dias", 0))
        custo_rh      = (
            recrutar_esp * CUSTO_RECRUTAMENTO_ESP
            + despedir_esp * CUSTO_RESCISAO_ESP
            + treinar_n_esp * CUSTO_TREINO_ESP
            + dias_form * CUSTO_CONSULTOR_DIA
            + max(0, recrutar_nao_esp) * CUSTO_RECRUTAMENTO_NAO_ESP
            + max(0, despedir_nao_esp) * CUSTO_RESCISAO_NAO_ESP
        )

        # Conservação máquinas
        horas_cons_total = horas_conservacao * num_maquinas_prod
        horas_emerg      = max(0.0, horas_avaria - horas_cons_total)
        custo_cons       = (horas_cons_total * CUSTO_CONSERVACAO_HORA
                            + horas_emerg * CUSTO_CONSERVACAO_EMERGENCIA)

        # Armazenagem
        inv_med_mp    = (e["inventario_mp"] + mp_fim) / 2.0
        inv_med_comp  = sum((e["componentes"].get(p, 0) + componentes_fim[p]) / 2.0
                            for p in PRODUTOS)
        inv_med_ue    = sum((e["inventario_produtos"].get(p, {}).get("UE", 0)
                             + inventario_produtos_fim[p].get("UE", 0)) / 2.0
                            for p in PRODUTOS)
        inv_med_nafta = sum((e["inventario_produtos"].get(p, {}).get("NAFTA", 0)
                             + inventario_produtos_fim[p].get("NAFTA", 0)) / 2.0
                            for p in PRODUTOS)
        inv_med_int   = sum((e["inventario_produtos"].get(p, {}).get("Internet", 0)
                             + inventario_produtos_fim[p].get("Internet", 0)) / 2.0
                            for p in PRODUTOS)
        espaco_fab    = area_fabrica * PCT_USO_FABRICA
        espaco_usado  = (num_maquinas_prod * ESPACO_POR_MAQUINA
                         + esp_producao * ESPACO_POR_ESP
                         + mp_necessaria_total / 1_000 * ESPACO_MP_POR_1000U)
        espaco_disp   = espaco_fab - espaco_usado

        custo_armaz  = (GASTOS_GERAIS_COMPRAS_TRIMESTRE
                        + (inv_med_ue + inv_med_int) * ARMAZENAGEM_PRODUTO_UE_INTERNET
                        + inv_med_nafta * ARMAZENAGEM_PRODUTO_NAFTA_USD * taxa_cambio
                        + (max(0, -espaco_disp / ESPACO_MP_POR_1000U * 1_000)
                           * 2.50 / 2.0))  # armazenagem externa estimada

        # Informações
        custo_info = (
            (CUSTO_INFO_QUOTAS    if d.get("comprar_quotas", False) else 0)
            + (CUSTO_INFO_ACTIVIDADES if d.get("comprar_atividades", False) else 0)
        ) if True else 0  # carregado de tabelas
        from tabelas import CUSTO_INFO_QUOTAS, CUSTO_INFO_ACTIVIDADES
        custo_info = (
            (CUSTO_INFO_QUOTAS    if d.get("comprar_quotas", False) else 0)
            + (CUSTO_INFO_ACTIVIDADES if d.get("comprar_atividades", False) else 0)
        )

        # Controlo de crédito
        custo_credito = (
            sum(vendas_un[p]["UE"] + vendas_un[p]["NAFTA"] for p in PRODUTOS) * CUSTO_CONTROLO_CREDITO_UE_NAFTA
            + sum(vendas_un[p]["Internet"] for p in PRODUTOS) * CUSTO_CARTAO_CREDITO_INTERNET
        )

        # Seguros
        plano_seg   = d.get("plano_seguro", e.get("plano_seguro", 0))
        anc_anterior = e["terreno"] + e["edificios"] + e["valor_maquinas"]
        inv_anterior  = e.get("_inventario_total_valor", 0.0)
        custo_seg    = (anc_anterior + inv_anterior) * SEGUROS[plano_seg]["premio_pct"]

        # Administração e gestão
        orcamento_gestao = d.get("orcamento_gestao", 40_000)

        # Outros custos (fábrica + desmontagem + carbono)
        co2_total = (area_fabrica * CO2_AQUECIMENTO_KG_M2
                     + horas_maq_usadas * CO2_MAQUINACAO_KG_HORA
                     + horas_esp_usadas * CO2_MONTAGEM_KG_HORA)
        custo_outros = (
            area_fabrica * CUSTOS_FIXOS_FABRICA_M2
            + maquinas_vender * CUSTO_DESMONTAGEM
            + (co2_total / 1_000) * CUSTO_CO2_POR_TONELADA
        )

        total_desp_adm = (custo_pub + custo_dist_int + custo_isp
                          + custo_agentes + custo_depto_vendas + custo_gar
                          + custo_id + custo_website + custo_rh + custo_cons
                          + custo_armaz + custo_info + custo_credito + custo_seg
                          + orcamento_gestao + custo_outros)

        # Amortizações
        dep_amort = depreciacao

        # Resultado operacional
        ind_seguros = 0.0  # simplificado (sem eventos aleatórios)
        resultado_op = resultado_bruto - total_desp_adm - dep_amort + ind_seguros

        # Financeiro
        juros_rec  = e.get("deposito_prazo", 0) * taxa_deposito(taxa_bce) / 4.0
        juros_pag  = (e.get("emprestimo_prazo", 0) * TAXA_EMPRESTIMO_PRAZO_ANUAL / 4.0)

        lucro_trib = resultado_op + juros_rec - juros_pag

        # Imposto (Q4 apenas)
        lucro_trib_acum_anterior = e.get("lucro_tributavel_acumulado", 0.0)
        lucro_trib_acum = lucro_trib_acum_anterior + lucro_trib
        imposto = 0.0
        if (trimestre % 4 == 0) and lucro_trib_acum > 0:
            imposto = lucro_trib_acum * TAXA_IMPOSTO
            lucro_trib_acum_depois = 0.0
        else:
            lucro_trib_acum_depois = lucro_trib_acum

        lucro_liquido = lucro_trib - imposto

        # Dividendos
        dividendo_pct = d.get("dividendo_pct", 0)
        dividendos    = e["capital_social"] * dividendo_pct / 100.0
        dividendos    = min(dividendos, max(0, e["resultados_transitados"]))

        eps = lucro_liquido / max(1, e["num_acoes"])

        # =================================================================
        # 12. BALANÇO
        # =================================================================
        # Activo não corrente
        edificios_fim = e["edificios"] + custo_expansao
        anc_fim       = e["terreno"] + edificios_fim + valor_maq_fim
        inv_tot_fim   = inventario_final_total

        # Clientes
        receb_int    = val_vendas_internet
        receb_ue     = val_encomendas_ue * (30 / 60.0)   # ~30 dias em 60 dias
        receb_nafta  = val_vendas_nafta   * (30 / 90.0)   # ~30 dias em 90 dias
        receb_ant    = e.get("clientes", 0) * 0.9
        recebimentos = receb_int + receb_ue + receb_nafta + receb_ant
        clientes_fim = max(0, e.get("clientes", 0) + vendas_valor - recebimentos
                           - val_vendas_internet)  # Internet pago imediato

        # Empréstimos a prazo
        emprestimo_novo       = d.get("emprestimo_prazo_novo", d.get("emprestimo_prazo", 0))
        emprestimo_reembolso  = d.get("emprestimo_prazo_reembolso", 0)
        emprestimo_adicional  = emprestimo_novo - emprestimo_reembolso
        emprestimo_prazo_fim  = max(0, e.get("emprestimo_prazo", 0) + emprestimo_adicional)

        # Depósito a prazo: a decisão indica o SALDO ALVO (não delta)
        deposito_alvo  = d.get("deposito_prazo", e.get("deposito_prazo", 0))
        deposito_delta = deposito_alvo - e.get("deposito_prazo", 0)
        deposito_fim   = max(0, deposito_alvo)

        # Emissão / recompra de acções
        acoes_delta   = d.get("acoes", {}).get("emitir", 0) * 1_000
        acoes_recomp  = abs(min(0, d.get("acoes", {}).get("emitir", 0))) * 1_000
        cotacao_atual = self._calcular_cotacao(
            anc_fim, inv_tot_fim, clientes_fim, 0, e
        )
        premios_em    = e.get("premios_emissao", 0) + acoes_delta * max(0, cotacao_atual - 1)
        capital_social_fim = e["capital_social"] + acoes_delta - acoes_recomp
        num_acoes_fim      = e["num_acoes"] + acoes_delta - acoes_recomp

        resultados_trans = (e["resultados_transitados"]
                            + lucro_liquido - dividendos)

        # Fornecedores (aprox. 50% da MP encomendada + outros pagamentos diferidos)
        fornecedores_fim = custo_mp_total_eur * 0.5  # segunda metade a pagar

        # Impostos a pagar (Q4 → pago no Q2 do ano seguinte)
        impostos_pagar_fim = imposto  # simplificado

        # Cash
        # Recebimentos - pagamentos
        pagamentos_fornec = (e.get("fornecedores", 0)
                             + custo_mp_total_eur * 0.5  # 50% da MP de agora
                             + custo_sal_nao_esp + custo_sal_esp
                             + custo_maquinacao + custo_cq + custo_transp
                             + custo_pub + custo_isp + custo_agentes + custo_dist_int
                             + custo_depto_vendas + custo_gar + custo_id + custo_website
                             + custo_rh + custo_cons + custo_info + custo_seg
                             + orcamento_gestao + custo_outros + custo_credito
                             + custo_armaz)
        imposto_pago = e.get("impostos_pagar", 0) if trimestre == 2 else 0

        fluxo_op  = recebimentos - pagamentos_fornec - imposto_pago
        fluxo_inv = (juros_rec
                     + maquinas_vender * (valor_maq_vendidas)
                     - maquinas_comprar * CUSTO_MAQUINA
                     - custo_expansao)
        fluxo_fin = (acoes_delta * cotacao_atual
                     - acoes_recomp * cotacao_atual
                     - dividendos
                     + emprestimo_adicional
                     - juros_pag
                     - deposito_delta)

        var_caixa = fluxo_op + fluxo_inv + fluxo_fin
        caixa_ant = e.get("cash", 0) - e.get("deposito_prazo", 0)  # caixa líquida
        caixa_fim_liq = caixa_ant + var_caixa
        cash_fim  = caixa_fim_liq + deposito_fim

        # Verificar descoberto
        limite_desc_prox = calcular_limite_financiamento(
            anc_fim, inv_tot_fim, clientes_fim, impostos_pagar_fim, fornecedores_fim
        )
        if cash_fim < 0:
            if abs(cash_fim) > limite_desc_prox:
                alertas.append(Alerta("erro",
                    f"Descoberto não autorizado: {cash_fim:,.0f}€ (limite: {-limite_desc_prox:,.0f}€)"))

        # Potencial de crédito
        cotacao_final = self._calcular_cotacao(anc_fim, inv_tot_fim, clientes_fim, cash_fim, e)
        pot_credito   = calcular_potencial_credito(
            cotacao_final, num_acoes_fim, emprestimo_prazo_fim, limite_desc_prox
        )

        # =================================================================
        # 13. INDICADORES FINAIS
        # =================================================================
        total_ativo = anc_fim + inv_tot_fim + clientes_fim + cash_fim
        total_passivo_cp = fornecedores_fim + impostos_pagar_fim + max(0, -cash_fim)
        total_cap_prop = capital_social_fim + premios_em + resultados_trans

        # =================================================================
        # 14. ACTUALIZAR ESTADO INTERNO
        # =================================================================
        e_novo = {
            **e,
            "trimestre": (trimestre % 4) + 1,
            "ano": ano + (1 if trimestre == 4 else 0),
            "maquinas": maquinas_proximo,
            "eficiencia_maquinas": eficiencia_nova,
            "valor_maquinas": valor_maq_fim,
            "operarios_esp": esp_proximo_trim,
            "operarios_nao_esp": nao_esp_producao,
            "agentes_ue": agentes_ue_n,
            "dist_nafta": dist_nafta_n,
            "dist_internet": 1 if tem_site else 0,
            "portas_website": d.get("portas_website", e.get("portas_website", 0)),
            "inventario_mp": mp_fim,
            "mp_proximo_trim": mp_enc_3m,
            "mp_seguinte_trim": mp_enc_6m,
            "componentes": {p: componentes_proximo_trim[p] for p in PRODUTOS},
            "inventario_produtos": inventario_produtos_fim,
            "encomendas_atraso": encomendas_atraso_fim,
            "cash": cash_fim,
            "deposito_prazo": deposito_fim,
            "emprestimo_prazo": emprestimo_prazo_fim,
            "capital_social": capital_social_fim,
            "num_acoes": num_acoes_fim,
            "premios_emissao": premios_em,
            "resultados_transitados": resultados_trans,
            "clientes": clientes_fim,
            "fornecedores": fornecedores_fim,
            "impostos_pagar": impostos_pagar_fim,
            "terreno": e["terreno"],
            "edificios": edificios_fim,
            "lucro_tributavel_acumulado": lucro_trib_acum_depois,
            "plano_seguro": plano_seg,
            "aviso_greve": 0,  # reset (novo aviso vem do relatório)
            "limite_financiamento": limite_desc_prox,
            "potencial_credito": pot_credito,
            "area_fabrica": area_fabrica_proximo,
            "salario_hora": salario_hora_eur * 100,  # guardar em cêntimos
            "_inventario_total_valor": inventario_final_total,
        }
        self.estado = e_novo

        # =================================================================
        # 15. RELATÓRIO
        # =================================================================
        return {
            "trimestre": trimestre,
            "ano": ano,
            "producao": {
                "plano": plano_producao,
                "produzidos": produzidos,
                "rejeitados": rejeitados,
                "produzidos_liquidos": produzidos_liquidos,
                "entregas_reais": entregas_reais,
                "encomendas_estimadas": encomendas_estimadas,
                "vendas": vendas_un,
                "encomendas_atraso": encomendas_atraso_fim,
                "inventario_fim": inventario_produtos_fim,
                "horas_maq_usadas": horas_maq_usadas,
                "horas_maq_disp": horas_maq_disp,
                "horas_esp_usadas": horas_esp_usadas,
                "horas_esp_disp": horas_esp_disp,
                "eficiencia_maquinas": eficiencia_anterior,
                "taxa_rejeicao_pct": taxa_rej_pct,
            },
            "rh": {
                "esp_inicio": e["operarios_esp"],
                "esp_despedidos": despedir_esp,
                "esp_recrutados": recrutar_esp,
                "esp_treinados": treinar_n_esp,
                "esp_abandono": abandono_esp,
                "esp_proximo_trim": esp_proximo_trim,
                "nao_esp_inicio": e.get("operarios_nao_esp", 0),
                "nao_esp_necessarios": nao_esp_necessarios,
                "nao_esp_producao": nao_esp_producao,
                "aviso_greve": semanas_greve,
            },
            "dr": {
                "vendas": vendas_valor,
                "inventario_inicial": inv_inicial_total,
                "compra_componentes": custo_componentes,
                "compra_mp": custo_mp_total_eur,
                "operacao_maquinas": custo_maquinacao,
                "salarios_nao_esp": custo_sal_nao_esp,
                "salarios_esp": custo_sal_esp,
                "controlo_qualidade": custo_cq,
                "transportes": custo_transp,
                "inventario_final": inventario_final_total,
                "custo_vendas": custo_vendas,
                "resultado_bruto": resultado_bruto,
                "despesas_adm": total_desp_adm,
                "indemnizacoes_seguros": ind_seguros,
                "depreciacao_amortizacao": dep_amort,
                "resultado_operacional": resultado_op,
                "rendimentos_financeiros": juros_rec,
                "gastos_financeiros": juros_pag,
                "lucro_tributavel": lucro_trib,
                "impostos": imposto,
                "lucro_liquido": lucro_liquido,
                "eps": eps,
                "dividendos_pagos": dividendos,
            },
            "despesas_adm_detalhe": {
                "publicidade": custo_pub,
                "distribuidor_internet": custo_dist_int,
                "isp": custo_isp,
                "agentes_distribuidores": custo_agentes,
                "depto_vendas": custo_depto_vendas,
                "garantia": custo_gar,
                "id": custo_id,
                "website": custo_website,
                "recrutamento_formacao": custo_rh,
                "conservacao_maquinas": custo_cons,
                "armazenagem_compras": custo_armaz,
                "informacoes": custo_info,
                "controlo_credito": custo_credito,
                "premios_seguros": custo_seg,
                "gestao": orcamento_gestao,
                "outros": custo_outros,
            },
            "balanco": {
                "terreno": e["terreno"],
                "edificios": edificios_fim,
                "maquinas": valor_maq_fim,
                "ativo_nao_corrente": anc_fim,
                "inventario_produtos": val_prod_fim,
                "inventario_componentes": val_comp_fim,
                "inventario_mp": val_mp_fim,
                "clientes": clientes_fim,
                "caixa": cash_fim,
                "ativo_corrente": inv_tot_fim + clientes_fim + cash_fim,
                "total_ativo": total_ativo,
                "impostos_pagar": impostos_pagar_fim,
                "fornecedores": fornecedores_fim,
                "financiamentos_obtidos": max(0, -cash_fim),
                "passivo_corrente": total_passivo_cp,
                "emprestimos_prazo": emprestimo_prazo_fim,
                "capital_social": capital_social_fim,
                "premios_emissao": premios_em,
                "resultados_transitados": resultados_trans,
                "total_cap_proprio": total_cap_prop,
            },
            "fluxos": {
                "recebimentos_clientes": recebimentos,
                "pagamentos_fornecedores": pagamentos_fornec,
                "imposto_pago": imposto_pago,
                "fluxo_operacional": fluxo_op,
                "juros_recebidos": juros_rec,
                "venda_ativo": maquinas_vender * valor_maq_vendidas,
                "compra_ativo": maquinas_comprar * CUSTO_MAQUINA + custo_expansao,
                "fluxo_investimento": fluxo_inv,
                "acoes_emitidas": acoes_delta * cotacao_atual,
                "recompra_acoes": acoes_recomp * cotacao_atual,
                "dividendos_pagos": dividendos,
                "emprestimos_obtidos": emprestimo_adicional,
                "juros_pagos": juros_pag,
                "fluxo_financiamento": fluxo_fin,
                "variacao_caixa": var_caixa,
                "caixa_anterior": caixa_ant + e.get("deposito_prazo", 0),
                "caixa_final": cash_fim,
                "limite_financiamento_prox": limite_desc_prox,
                "potencial_credito_prox": pot_credito,
            },
            "indicadores": {
                "cotacao_acoes": cotacao_final,
                "capitalizacao_bolsista": cotacao_final * num_acoes_fim,
                "cash": cash_fim,
                "limite_descob_autorizado": limite_desc_prox,
                "descoberto": max(0, -cash_fim),
                "roa": resultado_op / max(1, total_ativo),
                "roe": lucro_liquido / max(1, total_cap_prop),
            },
            "co2": {
                "aquecimento_kg": area_fabrica * CO2_AQUECIMENTO_KG_M2,
                "maquinacao_kg": horas_maq_usadas * CO2_MAQUINACAO_KG_HORA,
                "montagem_kg": horas_esp_usadas * CO2_MONTAGEM_KG_HORA,
                "total_kg": co2_total,
                "custo_compensacao": (co2_total / 1_000) * CUSTO_CO2_POR_TONELADA,
            },
            "alertas": [{"tipo": a.tipo, "msg": a.msg} for a in alertas],
        }

    # ------------------------------------------------------------------
    # Auxiliares privados
    # ------------------------------------------------------------------

    def _estimar_encomendas(self, precos, publicidade, inovacao,
                             agentes_ue, dist_nafta, dist_internet, estado):
        """
        Modelo simplificado de procura.
        O modelo real do GMC é proprietário; este é uma aproximação.
        Baseado em: preço, publicidade, agentes, imagem, sazonalidade.
        """
        encomendas = {}
        for p in PRODUTOS:
            encomendas[p] = {}
            imagem = estado.get("imagem_produtos", {}).get(p, 2.0)
            for m in MERCADOS:
                preco_m = precos.get(p, {}).get(m, 0)
                if preco_m <= 0:
                    encomendas[p][m] = 0
                    continue

                # Base de mercado
                base_ue    = {"P1": 8_000, "P2": 5_000, "P3": 2_000}
                base_nafta = {"P1": 4_000, "P2": 2_500, "P3": 1_000}
                base_int   = {"P1": 2_000, "P2": 1_200, "P3": 500}

                if m == "UE":
                    base  = base_ue[p] * (agentes_ue / 10.0) ** 0.5
                    ref_preco = {"P1": 200, "P2": 350, "P3": 600}[p]
                elif m == "NAFTA":
                    base  = base_nafta[p] * (dist_nafta / 5.0) ** 0.5 if dist_nafta > 0 else 0
                    ref_preco = {"P1": 210, "P2": 370, "P3": 630}[p]
                else:
                    base  = base_int[p] if dist_internet > 0 else 0
                    ref_preco = {"P1": 185, "P2": 330, "P3": 560}[p]

                # Elasticidade preço (≈ -2)
                factor_preco = (ref_preco / max(preco_m, 1)) ** 2.0
                # Publicidade
                pub_m  = publicidade.get(p, {}).get(m, 0)
                factor_pub = 1.0 + min(0.30, pub_m / 20_000)
                # Imagem
                factor_imagem = imagem / 3.0
                # I&D
                id_p = inovacao.get(p, 0)
                factor_id = 1.0 + min(0.10, id_p / 50_000)

                encomendas[p][m] = int(base * factor_preco * factor_pub
                                       * factor_imagem * factor_id)
        return encomendas

    def _calcular_cotacao(self, anc, inv, clientes, cash, estado):
        """
        Cotação das acções (simplificado – valor baseado em CP/acção).
        O simulador real usa uma fórmula proprietária.
        """
        num_acoes = estado.get("num_acoes", 4_000_000)
        resultados_trans = estado.get("resultados_transitados", 0)
        capital_social   = estado.get("capital_social", 4_000_000)
        premios_em       = estado.get("premios_emissao", 0)
        cp = capital_social + premios_em + resultados_trans
        cotacao_book = cp / max(1, num_acoes)
        # Múltiplo de mercado simplificado
        return max(0.01, cotacao_book)

    def _custo_agentes(self, d, e, val_enc_ue, val_vend_nafta,
                        agentes_ue_n, dist_nafta_n):
        """Custo total de agentes e distribuidores."""
        agentes_ue_ant = e.get("agentes_ue", 0)
        dist_nafta_ant = e.get("dist_nafta", 0)

        apoio_ue_unit   = max(AGENTE_APOIO_MINIMO, d.get("agentes_ue", {}).get("apoio", AGENTE_APOIO_MINIMO))
        comissao_ue_pct = d.get("agentes_ue", {}).get("comissao_pct", 0)
        custo_ue        = (agentes_ue_n * apoio_ue_unit
                           + val_enc_ue * comissao_ue_pct / 100.0
                           + max(0, agentes_ue_n - agentes_ue_ant) * AGENTE_CUSTO_ANGARIACAO)

        apoio_nafta_unit   = max(AGENTE_APOIO_MINIMO, d.get("dist_nafta", {}).get("apoio", AGENTE_APOIO_MINIMO))
        comissao_nafta_pct = d.get("dist_nafta", {}).get("comissao_pct", 0)
        custo_nafta        = (dist_nafta_n * apoio_nafta_unit
                              + val_vend_nafta * comissao_nafta_pct / 100.0
                              + max(0, dist_nafta_n - dist_nafta_ant) * AGENTE_CUSTO_ANGARIACAO)

        return custo_ue + custo_nafta

    def _calcular_transportes(self, entregas_reais, agentes_ue_n):
        """Custo total de transporte para todos os mercados."""
        custo = 0.0
        for m in MERCADOS:
            total_cont = 0
            for p in PRODUTOS:
                qtd = entregas_reais[p].get(m, 0)
                if qtd > 0:
                    total_cont += math.ceil(qtd / CAPACIDADE_CONTENTOR[p])
            if total_cont == 0:
                continue
            if m == "UE":
                dist = max(50, 2_000 / max(1, agentes_ue_n))
                dias = math.ceil(dist / KM_MAX_DIA)
                custo += total_cont * dias * CUSTO_DIARIO_CONTENTOR
            elif m == "NAFTA":
                dias_port = math.ceil(DIST_PORTO_NAFTA_KM / KM_MAX_DIA)
                custo += total_cont * (dias_port * CUSTO_DIARIO_CONTENTOR
                                       + CUSTO_TRAVESSIA_ATLANTICO)
            elif m == "Internet":
                dias = math.ceil(DIST_DISTRIBUIDOR_INTERNET_KM / KM_MAX_DIA)
                custo += total_cont * dias * CUSTO_DIARIO_CONTENTOR
        return custo
