# GMC Simulator

Simulador Python do **Global Management Challenge** — replica a lógica do jogo para testar e validar decisões antes de as submeter na competição real.

## Estrutura

```
simulador/
├── tabelas.py          # Todas as tabelas de parâmetros GMC (Tabelas 1-27)
├── gmc_engine.py       # Motor de simulação (classe Empresa)
├── app.py              # Interface Streamlit
├── requirements.txt
├── tests/
│   └── test_validacao.py
└── utils/
    ├── producao.py     # Capacidade, produção, transportes, carbono
    ├── financas.py     # DR, Balanço, Fluxos de Caixa
    ├── rh.py           # Recursos Humanos
    └── validacao.py    # Alertas e validação prévia
```

## Instalação

```bash
pip install -r requirements.txt
```

## Executar a interface

```bash
streamlit run app.py
```

Ou com o Python do Anki (se não tiver Python no PATH):

```powershell
& "C:\Users\Freitas\AppData\Local\AnkiProgramFiles\.venv\Scripts\python.exe" -m streamlit run app.py
```

## Executar os testes

```bash
python -m pytest tests/ -v
```

## Utilização programática

```python
from gmc_engine import Empresa, ESTADO_INICIAL_PADRAO

empresa = Empresa()   # começa no estado Y15Q1

decisoes = {
    "turnos": 2,
    "tempo_montagem": {"P1": 120, "P2": 180, "P3": 360},
    "maquinas": {"comprar": 1, "vender": 0},
    "compra_mp": {"spot": 5000, "3m": 0, "6m": 0},
    "mp_extra_pct": {"P1": 0, "P2": 0, "P3": 0},
    "producao": {"P1": 200, "P2": 50, "P3": 20},
    "entregas": {
        "P1": {"UE": 150, "NAFTA": 0, "Internet": 0},
        "P2": {"UE": 40,  "NAFTA": 0, "Internet": 0},
        "P3": {"UE": 15,  "NAFTA": 0, "Internet": 0},
    },
    "precos": {
        "P1": {"UE": 220.0, "NAFTA": 230.0, "Internet": 210.0},
        "P2": {"UE": 380.0, "NAFTA": 395.0, "Internet": 365.0},
        "P3": {"UE": 750.0, "NAFTA": 775.0, "Internet": 720.0},
    },
    "agentes_ue": {"total": 2, "apoio": 5000, "comissao_pct": 3.0},
    "dist_nafta": {"total": 0, "apoio": 0, "comissao_pct": 0.0},
    "dist_internet": {"ativo": False, "apoio": 0, "comissao_pct": 0.0},
    "portas_website": 0,
    "operarios_esp": {"recrutar": 2, "treinar": 0, "despedir": 0, "salario_hora": 950},
    "dias_formacao": 0,
    "publicidade": {
        "imagem_corporativa": 20000,
        "P1": {"UE": 5000, "NAFTA": 0, "Internet": 0},
        "P2": {"UE": 3000, "NAFTA": 0, "Internet": 0},
        "P3": {"UE": 2000, "NAFTA": 0, "Internet": 0},
    },
    "orcamento_gestao": 40000,
    "investimento_id": 0,
    "expansao_fabrica": 0,
    "plano_seguro": 1,
    "deposito_prazo": 2400000,
    "emprestimo_prazo_novo": 0,
    "emprestimo_prazo_reembolso": 0,
    "dividendo_pct": 0,
    "horas_conservacao": 0,
    "taxa_bce_ue": 0.015,
    "taxa_cambio_eur_usd": 0.73,
    "preco_mp_spot_usd": 74574,
    "preco_mp_3m_usd": 73402,
    "preco_mp_6m_usd": 72229,
}

relatorio = empresa.simular_trimestre(decisoes)

print(f"Vendas: {relatorio['dr']['vendas']:,.0f} €")
print(f"Resultado Líquido: {relatorio['dr']['resultado_liquido']:,.0f} €")
print(f"Cash: {empresa.estado['cash']:,.0f} €")
print(f"Cotação: {empresa.estado['cotacao']:.2f} €")

# Alertas
for a in relatorio["alertas"]:
    print(f"[{a.tipo.upper()}] {a.msg}")
```

## Validação e calibração

O ficheiro `tests/test_validacao.py` contém testes de smoke e uma classe `TestCalibracao` com placeholders para validação contra dados históricos. Para calibrar:

1. Extrair os valores reais do Excel histórico (HstY15Q1.Xls, etc.)
2. Preencher `REF_Y15Q2` na classe `TestCalibracao` com as métricas-chave
3. Executar `pytest tests/ -v` e ajustar os parâmetros em `tabelas.py` até atingir <5% de erro

## Limitações conhecidas

- **Modelo de procura simplificado**: a função de encomendas real do GMC é proprietária. O simulador usa elasticidade-preço ≈ -2 com factor de publicidade e imagem.
- **Cotação**: calculada como valor contabilístico por acção (proxy). A fórmula real não é pública.
- **Greve**: o risco é estimado mas o impacto não é completamente modelado.
- **Subcontratação**: componentes chegam no trimestre seguinte conforme o contrato de subcontratação.
