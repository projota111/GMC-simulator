"""
Tabelas de Parâmetros GMC (Global Management Challenge)
Fonte: Manual GMC, Tabelas 1-27
"""

# ---------------------------------------------------------------------------
# Tabela 1 – Demografia dos mercados
# ---------------------------------------------------------------------------
DEMOGRAFIA = {
    "UE":       {"populacao_M": 501,  "pib_per_capita": 34_222, "acesso_internet_pct": 67.3},
    "NAFTA":    {"populacao_M": 453,  "pib_per_capita": 37_315, "acesso_internet_pct": 65.7},
    "INTERNET": {"populacao_M": 3504, "pib_per_capita":  5_390, "acesso_internet_pct": 23.8},
}

# ---------------------------------------------------------------------------
# Tabela 2 – Custos de marketing (informação paga)
# ---------------------------------------------------------------------------
CUSTO_INFO_QUOTAS      = 5_000   # € quotas de mercado
CUSTO_INFO_ACTIVIDADES = 7_500   # € actividade das empresas

# ---------------------------------------------------------------------------
# Tabela 3 – Custos de agentes / distribuidores
# ---------------------------------------------------------------------------
AGENTE_APOIO_MINIMO   = 5_000   # € / agente / trimestre
AGENTE_CUSTO_ANGARIACAO = 7_500 # € por tentativa de angariação
AGENTE_CUSTO_RESCISAO   = 5_000 # € por rescisão

# ---------------------------------------------------------------------------
# Tabela 4 – Custos Internet (ISP)
# ---------------------------------------------------------------------------
ISP_PCT_VENDAS          = 0.03   # 3 % das vendas Internet
ISP_CUSTO_ADESAO        = 7_500  # € (primeira vez ou reativação)
ISP_CUSTO_POR_PORTA     = 1_000  # € / porta / trimestre
ISP_CUSTO_RESCISAO      = 5_000  # € (encerrar website)

# ---------------------------------------------------------------------------
# Tabela 5 – Parâmetros de fabrico por unidade
# ---------------------------------------------------------------------------
TEMPO_MAQUINACAO = {"P1": 60, "P2": 75, "P3": 120}   # minutos por unidade
TEMPO_MONTAGEM_MIN = {"P1": 100, "P2": 150, "P3": 300}  # minutos mínimos
MP_POR_PRODUTO   = {"P1": 1,  "P2": 2,  "P3": 3}      # unidades de MP por produto

# ---------------------------------------------------------------------------
# Tabela 6 – Custos de conservação de máquinas
# ---------------------------------------------------------------------------
CUSTO_CONSERVACAO_HORA       = 85    # € / hora contratada / máquina
CUSTO_CONSERVACAO_EMERGENCIA = 175   # € / hora de emergência (acima do contratado)

# ---------------------------------------------------------------------------
# Tabela 7 – Horas-máquina por turno e operários não-especializados necessários
# ---------------------------------------------------------------------------
HORAS_MAQUINA_POR_TURNO = {1: 576, 2: 1_068, 3: 1_602}  # horas / máquina / trimestre
OPERARIOS_NAO_ESP_POR_MAQUINA = {1: 4, 2: 8, 3: 12}       # operários / máquina

# ---------------------------------------------------------------------------
# Tabela 8 – Valorização de produtos rejeitados (sucata)
# ---------------------------------------------------------------------------
VALOR_SUCATA = {"P1": 40, "P2": 80, "P3": 120}  # € / unidade

# ---------------------------------------------------------------------------
# Tabela 9 – Preços do serviço de garantia
# ---------------------------------------------------------------------------
CUSTO_GARANTIA = {"P1": 60, "P2": 150, "P3": 250}  # € / unidade reparada

# ---------------------------------------------------------------------------
# Tabela 10 – Custos de produção
# ---------------------------------------------------------------------------
CUSTO_SUPERVISAO_POR_TURNO  = 12_500  # € / turno
CUSTO_OVERHEAD_POR_MAQUINA  =  3_500  # € / máquina / trimestre
CUSTO_OPERACAO_POR_HORA     =      8  # € / hora-máquina
CUSTO_PLANEAMENTO_POR_UNIDADE =    1  # € / unidade planeada
CUSTO_INSPECAO_POR_UNIDADE  =      1  # € / unidade montada

# ---------------------------------------------------------------------------
# Tabela 11 – Capacidade do contentor (unidades por contentor)
# ---------------------------------------------------------------------------
CAPACIDADE_CONTENTOR = {"P1": 500, "P2": 250, "P3": 125}  # unidades / contentor

# ---------------------------------------------------------------------------
# Tabela 12 – Parâmetros de transporte
# ---------------------------------------------------------------------------
CUSTO_DIARIO_CONTENTOR      =   650    # € / contentor / dia
DIST_PORTO_NAFTA_KM         =   250    # km até porto de embarque para NAFTA
CUSTO_TRAVESSIA_ATLANTICO   = 8_000    # € / contentor (travessia NAFTA)
DIST_DISTRIBUIDOR_INTERNET_KM = 150    # km até distribuidor Internet
KM_MAX_DIA                  =   400    # km / dia / viatura

# ---------------------------------------------------------------------------
# Tabela 13 – Compras e armazenagem
# ---------------------------------------------------------------------------
GASTOS_GERAIS_COMPRAS_TRIMESTRE = 7_500  # € fixos / trimestre
PENALIZACAO_COMPRA_IMPREVISTA   = 0.10   # 10 % acima do preço de ocasião
CUSTO_MP_EXTRA_PCT              = 0.50   # 50 % acima do preço de ocasião
ARMAZENAGEM_EXTERNA_MP          = 2.50   # € / unidade de MP / trimestre (média)
ARMAZENAGEM_EXTERNA_COMPONENTE  = 3.00   # € / unidade de componente
ARMAZENAGEM_PRODUTO_UE_INTERNET = 3.50   # € / unidade produto UE/Internet
ARMAZENAGEM_PRODUTO_NAFTA_USD   = 4.00   # USD / unidade produto NAFTA

# ---------------------------------------------------------------------------
# Tabela 14 – Cálculo de stock médio
# ---------------------------------------------------------------------------
# Stock médio = 0.5 × (valor inicial + valor final)

# ---------------------------------------------------------------------------
# Tabela 15 – Custos do departamento de recursos humanos
# ---------------------------------------------------------------------------
CUSTO_RECRUTAMENTO_ESP     = 2_000   # € / operário especializado recrutado
CUSTO_RESCISAO_ESP         = 5_000   # € / operário especializado despedido
CUSTO_TREINO_ESP           = 8_500   # € / operário especializado formado
CUSTO_RECRUTAMENTO_NAO_ESP = 1_000   # € / operário não especializado
CUSTO_RESCISAO_NAO_ESP     = 2_000   # € / operário não especializado despedido
CUSTO_CONSULTOR_DIA        = 1_000   # € / dia de consultor de formação

# ---------------------------------------------------------------------------
# Tabela 16 – Horas-homem por turno e subsídios
# Operários ESPECIALIZADOS só trabalham 1 turno (dia)
# ---------------------------------------------------------------------------
# 1 turno: 420h base + 84h sáb (+50%) + 72h dom (+100%) = 576h totais
HORAS_ESP_BASE          = 420   # horas ao salário base por trimestre
HORAS_ESP_SABADO        =  84   # horas sábado (base + 50%)
HORAS_ESP_DOMINGO       =  72   # horas domingo (base + 100%)
HORAS_ESP_TOTAL         = 576   # máximo de horas por trabalhador esp.

# Subsídio de turno para não-especializados (% sobre salário base, aplicado a todas as horas)
SUBSIDIO_TURNO = {1: 0, 2: 1/3, 3: 2/3}

# Horas não-esp por turno (mesma estrutura de sáb/dom do que o turno 1 de esp, repetido)
HORAS_NAO_ESP_BASE      = 420
HORAS_NAO_ESP_SABADO    =  42   # turno 2 e 3
HORAS_NAO_ESP_DOMINGO   =  72
# Turno 1: 420+84+72=576; Turno 2 e 3: 420+42+72=534

# ---------------------------------------------------------------------------
# Tabela 17 – Horas mínimas e salários
# ---------------------------------------------------------------------------
HORAS_MIN_NAO_ESP_TRIMESTRE = 360   # horas mínimas garantidas / não-esp / trimestre
HORAS_GREVE_POR_SEMANA       =  48  # horas perdidas / semana de greve / esp
SALARIO_HORA_MIN_ESP         =   9  # € / hora (mínimo legal, em euros)
PCT_SALARIO_NAO_ESP          = 0.65 # salário não-esp = 65 % do salário base dos esp

# ---------------------------------------------------------------------------
# Tabela 18 – Custos das máquinas
# ---------------------------------------------------------------------------
CUSTO_MAQUINA         = 300_000  # € / máquina (nova)
TAXA_AMORTIZACAO_TRIM =   0.025  # 2.5 % / trimestre (quotas decrescentes)
CUSTO_DESMONTAGEM     =  60_000  # € / máquina vendida

# ---------------------------------------------------------------------------
# Tabela 19 – Cálculo dos limites financeiros
# ---------------------------------------------------------------------------
def calcular_limite_financiamento(ativo_nao_corrente, inventario, clientes,
                                   impostos_pagar, fornecedores):
    """Limite de Financiamentos Obtidos autorizado."""
    limite = (0.50 * (ativo_nao_corrente + inventario)
              + 0.90 * clientes
              - 1.00 * (impostos_pagar + fornecedores))
    return max(0, limite)


def calcular_potencial_credito(cotacao_acoes, num_acoes, emprestimos_prazo,
                                limite_financiamento):
    """Potencial de crédito para novos empréstimos a prazo."""
    pot = (0.50 * cotacao_acoes * num_acoes
           - emprestimos_prazo
           - limite_financiamento)
    return max(0, pot)


def calcular_capacidade_credito(potencial_credito, caixa):
    """Capacidade de crédito (para compra de máquinas / expansão)."""
    return max(0, potencial_credito + caixa)

# ---------------------------------------------------------------------------
# Tabela 20 – Parâmetros financeiros
# ---------------------------------------------------------------------------
CUSTO_CONTROLO_CREDITO_UE_NAFTA = 1    # € / unidade vendida (UE + NAFTA)
CUSTO_CARTAO_CREDITO_INTERNET   = 1    # € / unidade vendida (Internet)
CUSTOS_FIXOS_FABRICA_M2         = 20   # € / m² / trimestre
TAXA_IMPOSTO                    = 0.30 # 30 % sobre lucro tributável acumulado (trimestre 4)
TAXA_EMPRESTIMO_PRAZO_ANUAL     = 0.10 # 10 % anual (fixa)

def taxa_deposito(taxa_bce: float) -> float:
    return taxa_bce

def taxa_financiamento_autorizado(taxa_bce: float) -> float:
    return taxa_bce + 0.04

def taxa_financiamento_nao_autorizado(taxa_bce: float) -> float:
    return taxa_bce + 0.10

# ---------------------------------------------------------------------------
# Tabela 21 – Valorização do inventário
# ---------------------------------------------------------------------------
FATOR_VALORIZACAO_MP       = 0.90   # 90 % do menor dos 3 preços
FATOR_VALORIZACAO_PRODUTOS = 1.10   # 110 % do custo total

# Custo de produtos = 110% de:
#   (MP valorizada + custo maquinação não-esp + custo montagem esp)

# ---------------------------------------------------------------------------
# Tabela 22 – Seguros
# ---------------------------------------------------------------------------
SEGUROS = {
    0: {"franquia_pct": 1.00, "premio_pct": 0.000},  # sem seguro (franquia = tudo)
    1: {"franquia_pct": 0.001, "premio_pct": 0.006},
    2: {"franquia_pct": 0.002, "premio_pct": 0.0035},
    3: {"franquia_pct": 0.003, "premio_pct": 0.002},
    4: {"franquia_pct": 0.004, "premio_pct": 0.001},
}

# ---------------------------------------------------------------------------
# Tabela 23 – Prazos de pagamento de clientes (dias)
# ---------------------------------------------------------------------------
PRAZO_PAGAMENTO_CLIENTE = {
    "Internet": 0,    # cartão de crédito – imediato
    "UE":      60,    # agentes UE – 60 dias
    "NAFTA":   90,    # distribuidores NAFTA – 90 dias
}

# ---------------------------------------------------------------------------
# Tabela 24 – Prazos de pagamento a fornecedores
# (pago próximo trimestre vs trimestre a seguir ao próximo)
# Percentagens que são pagas no próprio trimestre (resto paga-se no seguinte)
# ---------------------------------------------------------------------------
PAGAMENTO_PROPRIO_TRIMESTRE = {
    "publicidade":           0.00,  # pago no trimestre seguinte
    "ISP":                   1.00,
    "agentes_distribuidores":1.00,
    "garantia":              0.00,
    "website_desenvolvimento":0.00,
    "pessoal":               1.00,
    "conservacao":           0.00,
    "armazenagem":           0.00,
    "informacoes":           0.00,
    "seguros":               1.00,
    "mp_componentes":        0.50,  # 50% agora, 50% depois
    "transportes":           0.00,
    "investimento_capital":  1.00,
    "juros":                 1.00,
}

# ---------------------------------------------------------------------------
# Tabela 25 – Capacidade do website (visitas / hora)
# ---------------------------------------------------------------------------
CAPACIDADE_WEBSITE = {
    1:  {"teorica": 12,  "real": 2},
    2:  {"teorica": 24,  "real": 7},
    5:  {"teorica": 60,  "real": 31},
    10: {"teorica": 120, "real": 81},
    20: {"teorica": 240, "real": 190},
    50: {"teorica": 600, "real": 537},
}

# ---------------------------------------------------------------------------
# Tabela 26 – Requisitos de espaço (m²)
# ---------------------------------------------------------------------------
PCT_USO_TERRENO      = 0.80   # 80 % do terreno pode ser coberto
PCT_USO_FABRICA      = 0.75   # 75 % da área da fábrica usável para produção
ESPACO_POR_MAQUINA   = 25     # m² por máquina
ESPACO_POR_ESP       = 10     # m² por operário especializado
ESPACO_MP_POR_1000U  =  5     # m² por 1000 unidades de MP
ESPACO_WIP = {"P1": 0.25, "P2": 0.50, "P3": 1.00}  # m² / unidade WIP/componente

# ---------------------------------------------------------------------------
# Tabela 27 – Pegada de carbono (CO2e)
# ---------------------------------------------------------------------------
CO2_AQUECIMENTO_KWH_M2    = 50    # kWh / m² / trimestre
CO2_AQUECIMENTO_KG_M2     =  9.50 # kg CO2e / m² / trimestre
CO2_MAQUINACAO_KWH_HORA   =  6    # kWh / hora-máquina
CO2_MAQUINACAO_KG_HORA    =  2.82 # kg CO2e / hora-máquina
CO2_MONTAGEM_KWH_HORA     =  1    # kWh / hora-esp
CO2_MONTAGEM_KG_HORA      =  0.52 # kg CO2e / hora-esp
CUSTO_CO2_POR_TONELADA    = 40    # € / tonelada CO2e

# ---------------------------------------------------------------------------
# Constantes gerais
# ---------------------------------------------------------------------------
PRODUTOS   = ["P1", "P2", "P3"]
MERCADOS   = ["UE", "NAFTA", "Internet"]
NUM_TRIMESTRES_ANO = 4
