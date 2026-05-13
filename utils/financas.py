"""
Cálculos financeiros – GMC Simulator
Demonstração de Resultados, Balanço, Fluxos de Caixa
"""
from __future__ import annotations
from tabelas import (
    TAXA_IMPOSTO, TAXA_EMPRESTIMO_PRAZO_ANUAL,
    taxa_deposito, taxa_financiamento_autorizado, taxa_financiamento_nao_autorizado,
    FATOR_VALORIZACAO_MP, FATOR_VALORIZACAO_PRODUTOS,
    CUSTO_CONTROLO_CREDITO_UE_NAFTA, CUSTO_CARTAO_CREDITO_INTERNET,
    CUSTOS_FIXOS_FABRICA_M2, TAXA_AMORTIZACAO_TRIM, CUSTO_DESMONTAGEM,
    SEGUROS, CUSTO_MP_EXTRA_PCT, PENALIZACAO_COMPRA_IMPREVISTA,
    PRAZO_PAGAMENTO_CLIENTE,
    MP_POR_PRODUTO, PRODUTOS, MERCADOS,
    HORAS_ESP_TOTAL, HORAS_NAO_ESP_BASE, HORAS_NAO_ESP_SABADO,
    HORAS_NAO_ESP_DOMINGO, SUBSIDIO_TURNO, PCT_SALARIO_NAO_ESP,
    CO2_AQUECIMENTO_KG_M2, CO2_MAQUINACAO_KG_HORA,
    CO2_MONTAGEM_KG_HORA, CUSTO_CO2_POR_TONELADA,
)


# ---------------------------------------------------------------------------
# Valorização de inventário
# ---------------------------------------------------------------------------

def valorizar_mp(unidades_mp: int, preco_spot_usd: float,
                  preco_3m_usd: float, preco_6m_usd: float,
                  taxa_cambio_eur_usd: float) -> float:
    """Valor do inventário de MP = 90% do menor preço × unidades (em €)."""
    preco_min_usd = min(preco_spot_usd, preco_3m_usd, preco_6m_usd)
    preco_min_eur = preco_min_usd * taxa_cambio_eur_usd / 1_000  # preço por unidade
    return FATOR_VALORIZACAO_MP * preco_min_eur * unidades_mp


def valorizar_produto(produto: str, unidades: int,
                       preco_mp_eur_unidade: float,
                       pct_mp_extra: float,
                       salario_hora_esp: float,
                       salario_hora_nao_esp: float,
                       tempo_montagem_min: int,
                       turnos: int) -> float:
    """
    Valor de inventário de produto acabado = 110% de:
      conteúdo MP (ajustado extra) + custo maquinação (não-esp) + custo montagem (esp)
    """
    from tabelas import TEMPO_MAQUINACAO, SUBSIDIO_TURNO
    fator_mp_extra = 1.0 + pct_mp_extra / 100.0 * CUSTO_MP_EXTRA_PCT
    custo_mp_unit = preco_mp_eur_unidade * MP_POR_PRODUTO[produto] * fator_mp_extra

    # Custo maquinação por unidade (não-esp × 4 op/máquina × tempo em horas)
    from tabelas import TEMPO_MAQUINACAO
    custo_maq_unit = (
        salario_hora_nao_esp * (1 + SUBSIDIO_TURNO[turnos]) * 4
        * (TEMPO_MAQUINACAO[produto] / 60.0)
    )
    # Custo montagem por unidade (esp × tempo em horas)
    custo_mon_unit = salario_hora_esp * (tempo_montagem_min / 60.0)

    custo_unit = custo_mp_unit + custo_maq_unit + custo_mon_unit
    return FATOR_VALORIZACAO_PRODUTOS * custo_unit * unidades


# ---------------------------------------------------------------------------
# Demonstração de Resultados
# ---------------------------------------------------------------------------

def calcular_vendas(unidades_vendidas: dict[str, dict[str, int]],
                     precos: dict[str, dict[str, float]],
                     unidades_sucata: dict[str, int],
                     valor_sucata: dict[str, float]) -> float:
    """Valor total das vendas no trimestre."""
    vendas = 0.0
    for p in PRODUTOS:
        for m in MERCADOS:
            vendas += unidades_vendidas.get(p, {}).get(m, 0) * precos.get(p, {}).get(m, 0)
        vendas += unidades_sucata.get(p, 0) * valor_sucata.get(p, 0)
    return vendas


def calcular_custo_vendas(inventario_inicial: float,
                           compra_componentes: float,
                           compra_mp: float,
                           custo_maquinacao: float,
                           salarios_nao_esp: float,
                           salarios_esp: float,
                           controlo_qualidade: float,
                           transportes: float,
                           inventario_final: float) -> float:
    return (inventario_inicial + compra_componentes + compra_mp
            + custo_maquinacao + salarios_nao_esp + salarios_esp
            + controlo_qualidade + transportes - inventario_final)


def calcular_depreciacao(valor_maquinas_anterior: float,
                          valor_maquinas_vendidas: float) -> float:
    """Depreciação trimestral pelo método das quotas decrescentes."""
    base = valor_maquinas_anterior - valor_maquinas_vendidas
    return max(0.0, base * TAXA_AMORTIZACAO_TRIM)


def calcular_juros_deposito(montante_deposito: float,
                             taxa_bce_anual: float) -> float:
    """Juros recebidos no trimestre sobre depósito a prazo."""
    return montante_deposito * taxa_deposito(taxa_bce_anual) / 4.0


def calcular_juros_financiamento(saldo_inicial_neg: float,
                                  saldo_final_neg: float,
                                  limite_autorizado: float,
                                  taxa_bce_anual: float) -> float:
    """
    Juros pagos por financiamentos obtidos.
    saldo_inicial_neg e saldo_final_neg são positivos quando há descoberto.
    Se excederem o limite, aplica-se a taxa mais alta a TUDO.
    """
    saldo_medio = (abs(saldo_inicial_neg) + abs(saldo_final_neg)) / 2.0
    if saldo_medio <= 0:
        return 0.0
    if saldo_medio > limite_autorizado:
        taxa = taxa_financiamento_nao_autorizado(taxa_bce_anual)
    else:
        taxa = taxa_financiamento_autorizado(taxa_bce_anual)
    return saldo_medio * taxa / 4.0


def calcular_juros_emprestimo_prazo(montante_emprestimo: float) -> float:
    """Juros anuais fixos sobre empréstimos a prazo (10% a.a.)."""
    return montante_emprestimo * TAXA_EMPRESTIMO_PRAZO_ANUAL / 4.0


def calcular_imposto(lucro_tributavel_acumulado: float,
                      trimestre: int) -> float:
    """Imposto calculado apenas no Q4; zero nos outros."""
    if trimestre == 4 and lucro_tributavel_acumulado > 0:
        return lucro_tributavel_acumulado * TAXA_IMPOSTO
    return 0.0


# ---------------------------------------------------------------------------
# Despesas Administrativas
# ---------------------------------------------------------------------------

def custo_publicidade(publicidade: dict) -> float:
    """Total gasto em publicidade (imagem + produtos × mercados)."""
    total = publicidade.get("imagem_corporativa", 0)
    for p in PRODUTOS:
        for m in MERCADOS:
            total += publicidade.get(p, {}).get(m, 0)
    return float(total)


def custo_agentes_distribuidores(agentes_ue: dict, dist_nafta: dict,
                                   dist_internet: dict,
                                   agentes_ue_anterior: int,
                                   dist_nafta_anterior: int,
                                   valor_encomendas_ue: float,
                                   valor_vendas_nafta: float) -> float:
    """
    Custo total de agentes e distribuidores:
    Apoio financeiro + comissões + angariação + rescisão.
    """
    from tabelas import AGENTE_APOIO_MINIMO, AGENTE_CUSTO_ANGARIACAO, AGENTE_CUSTO_RESCISAO
    custo = 0.0

    # Agentes UE
    n_ue = agentes_ue.get("total", 0)
    apoio_ue = max(AGENTE_APOIO_MINIMO, agentes_ue.get("apoio", 0)) * n_ue
    comissao_ue = valor_encomendas_ue * agentes_ue.get("comissao_pct", 0) / 100.0
    tentativas_ang_ue = max(0, n_ue - agentes_ue_anterior)
    custo += apoio_ue + comissao_ue + tentativas_ang_ue * AGENTE_CUSTO_ANGARIACAO

    # Distribuidores NAFTA
    n_nafta = dist_nafta.get("total", 0)
    apoio_nafta = max(AGENTE_APOIO_MINIMO, dist_nafta.get("apoio", 0)) * n_nafta
    comissao_nafta = valor_vendas_nafta * dist_nafta.get("comissao_pct", 0) / 100.0
    tentativas_ang_nafta = max(0, n_nafta - dist_nafta_anterior)
    custo += apoio_nafta + comissao_nafta + tentativas_ang_nafta * AGENTE_CUSTO_ANGARIACAO

    # Distribuidor Internet
    apoio_int = dist_internet.get("apoio", 0)
    custo += apoio_int

    return custo


def custo_departamento_vendas(valor_total_encomendas: float) -> float:
    """1% do valor das encomendas recebidas."""
    return valor_total_encomendas * 0.01


def custo_garantia(unidades_reparadas: dict[str, int],
                   custos_garantia: dict[str, float]) -> float:
    return sum(unidades_reparadas.get(p, 0) * custos_garantia[p]
               for p in PRODUTOS)


def custo_recrutamento_formacao(recrutar_esp: int, despedir_esp: int,
                                 treinar_nao_esp: int, recrutar_nao_esp: int,
                                 despedir_nao_esp: int,
                                 dias_formacao: int) -> float:
    from tabelas import (CUSTO_RECRUTAMENTO_ESP, CUSTO_RESCISAO_ESP,
                         CUSTO_TREINO_ESP, CUSTO_RECRUTAMENTO_NAO_ESP,
                         CUSTO_RESCISAO_NAO_ESP, CUSTO_CONSULTOR_DIA)
    return (
        max(0, recrutar_esp) * CUSTO_RECRUTAMENTO_ESP
        + max(0, despedir_esp) * CUSTO_RESCISAO_ESP
        + treinar_nao_esp * CUSTO_TREINO_ESP
        + max(0, recrutar_nao_esp) * CUSTO_RECRUTAMENTO_NAO_ESP
        + max(0, despedir_nao_esp) * CUSTO_RESCISAO_NAO_ESP
        + dias_formacao * CUSTO_CONSULTOR_DIA
    )


def custo_conservacao_maquinas(horas_contratadas: int, num_maquinas: int,
                                 horas_avaria: float) -> float:
    from tabelas import (CUSTO_CONSERVACAO_HORA, CUSTO_CONSERVACAO_EMERGENCIA)
    horas_total_contratadas = horas_contratadas * num_maquinas
    horas_emergencia = max(0.0, horas_avaria - horas_total_contratadas)
    return (horas_total_contratadas * CUSTO_CONSERVACAO_HORA
            + horas_emergencia * CUSTO_CONSERVACAO_EMERGENCIA)


def custo_armazenagem(mp_stock_medio: float, componentes_stock_medio: float,
                       produtos_stock_medio_ue: float,
                       produtos_stock_medio_nafta: float,
                       produtos_stock_medio_internet: float,
                       espaco_disponivel: float,
                       taxa_cambio_eur_usd: float) -> float:
    from tabelas import (GASTOS_GERAIS_COMPRAS_TRIMESTRE,
                         ARMAZENAGEM_EXTERNA_MP, ARMAZENAGEM_EXTERNA_COMPONENTE,
                         ARMAZENAGEM_PRODUTO_UE_INTERNET, ARMAZENAGEM_PRODUTO_NAFTA_USD)
    custo = GASTOS_GERAIS_COMPRAS_TRIMESTRE
    if espaco_disponivel < 0:
        excesso = abs(espaco_disponivel)
        # Custo de armazenagem externa para MP/componentes em excesso
        custo += mp_stock_medio * ARMAZENAGEM_EXTERNA_MP
        custo += componentes_stock_medio * ARMAZENAGEM_EXTERNA_COMPONENTE
    custo += produtos_stock_medio_ue * ARMAZENAGEM_PRODUTO_UE_INTERNET
    custo += produtos_stock_medio_internet * ARMAZENAGEM_PRODUTO_UE_INTERNET
    custo += produtos_stock_medio_nafta * ARMAZENAGEM_PRODUTO_NAFTA_USD * taxa_cambio_eur_usd
    return custo


def custo_isp(num_portas: int, vendas_internet: float,
              novo_isp: bool, encerrar_isp: bool) -> float:
    from tabelas import (ISP_CUSTO_POR_PORTA, ISP_PCT_VENDAS,
                         ISP_CUSTO_ADESAO, ISP_CUSTO_RESCISAO)
    custo = num_portas * ISP_CUSTO_POR_PORTA + vendas_internet * ISP_PCT_VENDAS
    if novo_isp:
        custo += ISP_CUSTO_ADESAO
    if encerrar_isp:
        custo += ISP_CUSTO_RESCISAO
    return custo


def custo_distribuidor_internet(valor_vendas_internet: float,
                                  comissao_pct: float,
                                  apoio: float) -> float:
    return valor_vendas_internet * comissao_pct / 100.0 + apoio


def custo_seguros(plano: int,
                   ativo_nao_corrente: float,
                   inventario: float) -> float:
    """Prémio de seguro = taxa % × (ANC + inventário)."""
    if plano == 0:
        return 0.0
    return (ativo_nao_corrente + inventario) * SEGUROS[plano]["premio_pct"]


def custo_fabrica_outros(area_fabrica: float, num_maquinas_vendidas: int,
                          co2_kg: float) -> float:
    """Custos fixos de fábrica + desmontagem + compensação carbono."""
    from tabelas import CUSTO_DESMONTAGEM
    return (
        area_fabrica * CUSTOS_FIXOS_FABRICA_M2
        + num_maquinas_vendidas * CUSTO_DESMONTAGEM
        + (co2_kg / 1_000) * CUSTO_CO2_POR_TONELADA
    )


# ---------------------------------------------------------------------------
# Balanço
# ---------------------------------------------------------------------------

def calcular_maquinas_valor(valor_anterior: float, depreciacao: float,
                              num_novas: int, valor_vendidas: float) -> float:
    """Valor líquido das máquinas após amortização e transações."""
    from tabelas import CUSTO_MAQUINA
    return (valor_anterior - depreciacao
            + num_novas * CUSTO_MAQUINA
            - valor_vendidas)


def calcular_clientes(clientes_anterior: float, vendas: float,
                       recebimentos: float) -> float:
    """Saldo de clientes (contas a receber)."""
    return clientes_anterior + vendas - recebimentos


def calcular_recebimentos(vendas_ue: float, vendas_nafta: float,
                           vendas_internet: float,
                           clientes_anterior: float) -> float:
    """
    Estimativa de recebimentos no trimestre.
    Internet: 100% imediato.
    UE (60 dias): ~2/3 do trimestre recebido = aprox. 50% das vendas atuais + saldo anterior.
    NAFTA (90 dias): ~1/3 recebido = aprox. 25% das vendas atuais.
    """
    receb_internet = vendas_internet
    receb_ue       = vendas_ue * 0.50
    receb_nafta    = vendas_nafta * 0.25
    receb_anterior = clientes_anterior * 0.90  # maioria dos saldos recebidos
    return receb_internet + receb_ue + receb_nafta + receb_anterior


def calcular_fornecedores(despesas_pagas_proximo_trim: float) -> float:
    """Saldo de fornecedores = valor que será pago no próximo trimestre."""
    return despesas_pagas_proximo_trim


# ---------------------------------------------------------------------------
# Fluxos de Caixa
# ---------------------------------------------------------------------------

def variacao_caixa(fluxo_operacional: float,
                   fluxo_investimento: float,
                   fluxo_financiamento: float) -> float:
    return fluxo_operacional + fluxo_investimento + fluxo_financiamento


def limite_financiamento_proximo_trimestre(ativo_nao_corrente: float,
                                            inventario: float,
                                            clientes: float,
                                            impostos_pagar: float,
                                            fornecedores: float) -> float:
    from tabelas import calcular_limite_financiamento
    return calcular_limite_financiamento(
        ativo_nao_corrente, inventario, clientes, impostos_pagar, fornecedores
    )
