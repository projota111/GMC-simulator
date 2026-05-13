"""
GMC Simulator – Interface Streamlit
"""
from __future__ import annotations
import copy
import streamlit as st
import pandas as pd

# ── importação do motor ──────────────────────────────────────────────────────
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from gmc_engine import Empresa, ESTADO_INICIAL_PADRAO
from utils.validacao import validar_decisoes

# ── configuração da página ───────────────────────────────────────────────────
st.set_page_config(
    page_title="GMC Simulator",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── inicialização do estado da sessão ────────────────────────────────────────
if "empresa" not in st.session_state:
    st.session_state.empresa = Empresa()
if "historico" not in st.session_state:
    st.session_state.historico = []


# ============================================================================
# SIDEBAR – decisões
# ============================================================================
def sidebar_decisoes() -> dict:
    st.sidebar.header("Decisões do Trimestre")

    e = st.session_state.empresa.estado
    d: dict = {}

    # ── Informação do trimestre ──────────────────────────────────────────────
    st.sidebar.caption(f"**Ano {e['ano']} · Q{e['trimestre']}**")
    st.sidebar.divider()

    # ── Parâmetros de mercado (exógenos / actualizáveis) ─────────────────────
    with st.sidebar.expander("📈 Parâmetros de Mercado", expanded=False):
        d["taxa_bce_ue"]        = st.number_input("Taxa BCE (% a.a.)", 0.0, 10.0,
                                                   float(e.get("taxa_bce_ue", 0.015))*100, 0.1) / 100
        d["taxa_cambio_eur_usd"] = st.number_input("Taxa Câmbio €/$", 0.50, 2.00,
                                                    float(e.get("taxa_cambio_eur_usd", 0.73)), 0.01)
        d["preco_mp_spot_usd"]   = st.number_input("MP Spot ($/1000u)", 0.0, 500_000.0,
                                                    float(e.get("preco_mp_spot_usd", 74_574.0)), 100.0)
        d["preco_mp_3m_usd"]     = st.number_input("MP 3M ($/1000u)", 0.0, 500_000.0,
                                                    float(e.get("preco_mp_3m_usd", 73_402.0)), 100.0)
        d["preco_mp_6m_usd"]     = st.number_input("MP 6M ($/1000u)", 0.0, 500_000.0,
                                                    float(e.get("preco_mp_6m_usd", 72_229.0)), 100.0)

    # ── Produção ─────────────────────────────────────────────────────────────
    with st.sidebar.expander("⚙️ Produção", expanded=True):
        d["turnos"] = st.selectbox("Turnos", [1, 2, 3], index=0)

        st.markdown("**Tempo de montagem (min)**")
        d["tempo_montagem"] = {
            "P1": st.number_input("P1 (min, ≥100)", 100, 600, 100, 10),
            "P2": st.number_input("P2 (min, ≥150)", 150, 900, 150, 10),
            "P3": st.number_input("P3 (min, ≥300)", 300, 1800, 300, 10),
        }

        st.markdown("**Máquinas**")
        col1, col2 = st.columns(2)
        with col1:
            maq_comprar = st.number_input("Comprar", 0, 20, 0, 1)
        with col2:
            maq_vender  = st.number_input("Vender", 0, e.get("maquinas", 0), 0, 1)
        d["maquinas"] = {"comprar": maq_comprar, "vender": maq_vender}

        st.markdown("**Horas de conservação/manutenção por máquina**")
        d["horas_conservacao"] = st.number_input("Horas contratadas", 0, 500, 0, 5)

    # ── Matéria-prima ────────────────────────────────────────────────────────
    with st.sidebar.expander("📦 Matéria-Prima", expanded=True):
        st.markdown("**Compra de MP (unidades)**")
        d["compra_mp"] = {
            "spot":   st.number_input("Spot",    0, 1_000_000, 0, 100),
            "3m":     st.number_input("3 Meses", 0, 1_000_000, 0, 100),
            "6m":     st.number_input("6 Meses", 0, 1_000_000, 0, 100),
        }
        st.markdown("**% MP Extra (qualidade)**")
        d["mp_extra_pct"] = {
            "P1": st.slider("P1 extra %", 0, 100, 0),
            "P2": st.slider("P2 extra %", 0, 100, 0),
            "P3": st.slider("P3 extra %", 0, 100, 0),
        }

    # ── Plano de produção ────────────────────────────────────────────────────
    with st.sidebar.expander("🏗️ Plano de Produção", expanded=True):
        st.markdown("**Unidades a produzir**")
        d["producao"] = {
            "P1": st.number_input("Produção P1", 0, 10_000, 0, 10),
            "P2": st.number_input("Produção P2", 0, 10_000, 0, 10),
            "P3": st.number_input("Produção P3", 0, 10_000, 0, 10),
        }

    # ── Vendas / Entregas ────────────────────────────────────────────────────
    with st.sidebar.expander("🛒 Vendas & Preços", expanded=True):
        entregas, precos = {}, {}
        for p in ["P1", "P2", "P3"]:
            st.markdown(f"**{p}**")
            cols = st.columns(3)
            ent_p, prec_p = {}, {}
            for i, m in enumerate(["UE", "NAFTA", "Internet"]):
                with cols[i]:
                    ent_p[m]  = st.number_input(f"Entr {m}", 0, 50_000, 0, 5, key=f"ent_{p}_{m}")
                    prec_p[m] = st.number_input(f"Preço {m} (€)", 0.0, 100_000.0,
                                                 200.0 if p == "P1" else 350.0 if p == "P2" else 700.0,
                                                 10.0, key=f"prec_{p}_{m}")
            entregas[p] = ent_p
            precos[p]   = prec_p
        d["entregas"] = entregas
        d["precos"]   = precos

    # ── Agentes / Distribuidores ─────────────────────────────────────────────
    with st.sidebar.expander("🌍 Agentes & Distribuidores", expanded=False):
        st.markdown("**Agentes UE**")
        d["agentes_ue"] = {
            "total":       st.number_input("Total agentes UE", 0, 50, e.get("agentes_ue", 0), 1),
            "apoio":       st.number_input("Apoio/agente (€)", 0, 100_000, 5_000, 500),
            "comissao_pct": st.slider("Comissão UE (%)", 0.0, 20.0, 3.0, 0.5),
        }
        st.markdown("**Distribuidores NAFTA**")
        d["dist_nafta"] = {
            "total":       st.number_input("Total dist NAFTA", 0, 20, e.get("dist_nafta", 0), 1),
            "apoio":       st.number_input("Apoio/dist NAFTA (€)", 0, 200_000, 10_000, 1_000),
            "comissao_pct": st.slider("Comissão NAFTA (%)", 0.0, 25.0, 5.0, 0.5),
        }
        st.markdown("**Distribuidor Internet**")
        d["dist_internet"] = {
            "ativo": st.checkbox("Activo", value=e.get("dist_internet", 0) > 0),
            "apoio": st.number_input("Apoio Internet (€)", 0, 100_000, 0, 500),
            "comissao_pct": st.slider("Comissão Internet (%)", 0.0, 20.0, 3.0, 0.5),
        }
        d["portas_website"] = st.number_input("Portas website (ISP)", 0, 100, e.get("portas_website", 0), 1)

    # ── Recursos Humanos ─────────────────────────────────────────────────────
    with st.sidebar.expander("👷 Recursos Humanos", expanded=False):
        salario = st.number_input("Salário/hora esp (€)", 5.0, 50.0,
                                   e.get("salario_hora", 9.0), 0.5)
        d["operarios_esp"] = {
            "recrutar":    st.number_input("Recrutar esp", 0, 50, 0, 1),
            "treinar":     st.number_input("Treinar não-esp→esp", 0, 20, 0, 1),
            "despedir":    st.number_input("Despedir esp", 0, e.get("operarios_esp", 0), 0, 1),
            "salario_hora": salario * 100,  # em cêntimos internamente
        }
        d["dias_formacao"] = st.number_input("Dias formação (consultor)", 0, 30, 0, 1)

    # ── Publicidade ──────────────────────────────────────────────────────────
    with st.sidebar.expander("📣 Publicidade", expanded=False):
        pub = {"imagem_corporativa": st.number_input("Imagem corporativa (€)", 0, 2_000_000, 0, 1_000)}
        for p in ["P1", "P2", "P3"]:
            pub[p] = {}
            for m in ["UE", "NAFTA", "Internet"]:
                pub[p][m] = st.number_input(f"Pub {p} {m} (€)", 0, 500_000, 0, 500, key=f"pub_{p}_{m}")
        d["publicidade"] = pub
        d["orcamento_gestao"] = st.number_input("Orçamento gestão (€)", 0, 500_000, 40_000, 1_000)
        d["investimento_id"]  = st.number_input("I&D (€)", 0, 1_000_000, 0, 5_000)

    # ── Fábrica / Expansão ───────────────────────────────────────────────────
    with st.sidebar.expander("🏗️ Fábrica & Expansão", expanded=False):
        d["expansao_fabrica"] = st.number_input("Expandir fábrica (m²)", 0, 5_000, 0, 100)
        d["plano_seguro"]     = st.selectbox("Plano de seguro", [0, 1, 2, 3, 4],
                                              index=e.get("plano_seguro", 0))

    # ── Finanças ─────────────────────────────────────────────────────────────
    with st.sidebar.expander("💰 Finanças", expanded=False):
        d["deposito_prazo"] = st.number_input("Depósito a prazo (€)", 0, 10_000_000,
                                               int(e.get("deposito_prazo", 0)), 50_000)
        d["emprestimo_prazo_novo"] = st.number_input("Novo empréstimo prazo (€)", 0, 10_000_000, 0, 50_000)
        d["emprestimo_prazo_reembolso"] = st.number_input("Reembolso empréstimo (€)", 0,
                                                            int(e.get("emprestimo_prazo", 0)), 0, 50_000)
        d["dividendo_pct"] = st.slider("Dividendo (% do capital)", 0.0, 20.0, 0.0, 0.5)

    return d


# ============================================================================
# DASHBOARD PRINCIPAL
# ============================================================================

def mostrar_dashboard(relatorio: dict | None = None):
    st.title("🏭 GMC Simulator")

    e = st.session_state.empresa.estado
    hist = st.session_state.historico

    # ── Métricas-chave ───────────────────────────────────────────────────────
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Cash (€)", f"{e.get('cash', 0):,.0f}")
    col2.metric("Máquinas", e.get("maquinas", 0))
    col3.metric("Esp.", e.get("operarios_esp", 0))
    col4.metric("Inv. MP", e.get("inventario_mp", 0))
    col5.metric("Cotação (€)", f"{e.get('cotacao', 0):.2f}")

    if relatorio:
        st.divider()
        _mostrar_relatorio(relatorio)

    if hist:
        st.divider()
        _mostrar_historico(hist)


def _mostrar_relatorio(r: dict):
    st.subheader("Relatório do Trimestre")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("#### Demonstração de Resultados")
        dr = r.get("dr", {})
        df_dr = pd.DataFrame([
            ("Vendas",                      dr.get("vendas", 0)),
            ("Custo de Vendas",            -dr.get("custo_vendas", 0)),
            ("Resultado Bruto",             dr.get("resultado_bruto", 0)),
            ("Despesas Adm.",              -dr.get("despesas_adm", 0)),
            ("Amortizações",               -dr.get("depreciacao", 0)),
            ("EBIT",                        dr.get("ebit", 0)),
            ("Juros Obtidos",               dr.get("juros_obtidos", 0)),
            ("Juros Pagos",                -dr.get("juros_pagos", 0)),
            ("EBT",                         dr.get("ebt", 0)),
            ("Imposto",                    -dr.get("imposto", 0)),
            ("Resultado Líquido",           dr.get("resultado_liquido", 0)),
        ], columns=["Item", "€"])
        df_dr["€"] = df_dr["€"].apply(lambda x: f"{x:,.0f}")
        st.dataframe(df_dr, hide_index=True, use_container_width=True)

    with col2:
        st.markdown("#### Balanço")
        bal = r.get("balanco", {})
        df_bal = pd.DataFrame([
            ("Caixa & Equiv.",              bal.get("caixa", 0)),
            ("Depósito a Prazo",            bal.get("deposito_prazo", 0)),
            ("Clientes",                    bal.get("clientes", 0)),
            ("Inventários",                 bal.get("inventarios", 0)),
            ("Imobilizado (líq.)",          bal.get("imobilizado", 0)),
            ("Total Activo",                bal.get("total_ativo", 0)),
            ("---",                         None),
            ("Fornecedores",               -bal.get("fornecedores", 0)),
            ("Impostos a Pagar",           -bal.get("impostos_pagar", 0)),
            ("Empréstimos",                -bal.get("emprestimo_prazo", 0)),
            ("Capital Social",              bal.get("capital_social", 0)),
            ("Resultados Transitados",      bal.get("resultados_transitados", 0)),
            ("Total CP+Passivo",            bal.get("total_cp_passivo", 0)),
        ], columns=["Item", "€"])
        df_bal["€"] = df_bal["€"].apply(lambda x: f"{x:,.0f}" if x is not None else "")
        st.dataframe(df_bal, hide_index=True, use_container_width=True)

    with col3:
        st.markdown("#### Produção")
        prod = r.get("producao", {})
        df_prod_rows = []
        for p in ["P1", "P2", "P3"]:
            df_prod_rows.append((p, "Produzidas", prod.get("produzidas", {}).get(p, 0)))
            df_prod_rows.append((p, "Vendidas",   sum(r.get("vendas_un", {}).get(p, {}).values())))
            df_prod_rows.append((p, "Rejeitadas", prod.get("rejeitados", {}).get(p, 0)))
        df_prod = pd.DataFrame(df_prod_rows, columns=["Produto", "Métrica", "Unidades"])
        st.dataframe(df_prod, hide_index=True, use_container_width=True)

        st.markdown("**Custos de Produção**")
        custos = r.get("custos_prod", {})
        df_cust = pd.DataFrame([
            ("Maquinação",   custos.get("maquinacao", 0)),
            ("Sal. Não-Esp", custos.get("salarios_nao_esp", 0)),
            ("Sal. Esp",     custos.get("salarios_esp", 0)),
            ("Controlo Qual.", custos.get("controlo_qualidade", 0)),
            ("Transportes",  custos.get("transportes", 0)),
        ], columns=["Item", "€"])
        df_cust["€"] = df_cust["€"].apply(lambda x: f"{x:,.0f}")
        st.dataframe(df_cust, hide_index=True, use_container_width=True)

    # ── Alertas ──────────────────────────────────────────────────────────────
    alertas = r.get("alertas", [])
    if alertas:
        st.divider()
        st.subheader("⚠️ Alertas")
        for a in alertas:
            if a["tipo"] == "erro":
                st.error(f"🔴 {a['msg']}")
            elif a["tipo"] == "aviso":
                st.warning(f"🟡 {a['msg']}")
            else:
                st.info(f"🔵 {a['msg']}")


def _mostrar_historico(hist: list[dict]):
    st.subheader("📊 Evolução Histórica")

    df_hist = pd.DataFrame([{
        "Trimestre":  f"Y{h['ano']}Q{h['trimestre']}",
        "Vendas (€)": h.get("dr", {}).get("vendas", 0),
        "Res. Líq.":  h.get("dr", {}).get("resultado_liquido", 0),
        "Cash (€)":   h.get("estado_final", {}).get("cash", 0),
        "Cotação (€)": h.get("estado_final", {}).get("cotacao", 0),
    } for h in hist])

    col1, col2 = st.columns(2)
    with col1:
        st.line_chart(df_hist.set_index("Trimestre")[["Vendas (€)", "Res. Líq."]])
    with col2:
        st.line_chart(df_hist.set_index("Trimestre")[["Cash (€)", "Cotação (€)"]])


# ============================================================================
# PAINEL DE VALIDAÇÃO PRÉVIA
# ============================================================================

def painel_validacao(decisoes: dict):
    e = st.session_state.empresa.estado
    alertas = validar_decisoes(decisoes, e)
    erros   = [a for a in alertas if a.tipo == "erro"]
    avisos  = [a for a in alertas if a.tipo == "aviso"]

    with st.expander(f"🔍 Validação prévia — {len(erros)} erro(s), {len(avisos)} aviso(s)",
                     expanded=bool(erros)):
        for a in alertas:
            if a.tipo == "erro":
                st.error(f"🔴 {a.msg}")
            elif a.tipo == "aviso":
                st.warning(f"🟡 {a.msg}")
            else:
                st.info(a.msg)
        if not alertas:
            st.success("Nenhum problema detectado.")

    return erros


# ============================================================================
# PAINEL DE ESTADO ACTUAL
# ============================================================================

def painel_estado():
    e = st.session_state.empresa.estado
    with st.expander("📋 Estado actual da empresa", expanded=False):
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("**Produção**")
            st.write(f"Máquinas: {e.get('maquinas', 0)}")
            st.write(f"Eficiência: {e.get('eficiencia_maquinas', 100):.1f}%")
            st.write(f"Turnos anteriores: {e.get('turnos', 1)}")
            st.write(f"Esp.: {e.get('operarios_esp', 0)}")
            st.write(f"Não-Esp.: {e.get('operarios_nao_esp', 0)}")
        with col2:
            st.markdown("**Inventário**")
            st.write(f"MP em stock: {e.get('inventario_mp', 0):,} u")
            inv = e.get("inventario_produtos", {})
            for p in ["P1", "P2", "P3"]:
                total = sum(inv.get(p, {}).values())
                st.write(f"{p}: {total:,} u")
        with col3:
            st.markdown("**Financeiro**")
            st.write(f"Cash: {e.get('cash', 0):,.0f} €")
            st.write(f"Depósito: {e.get('deposito_prazo', 0):,.0f} €")
            st.write(f"Empréstimo: {e.get('emprestimo_prazo', 0):,.0f} €")
            st.write(f"Limite desc.: {e.get('limite_financiamento', 0):,.0f} €")
            st.write(f"Cotação: {e.get('cotacao', 0):.2f} €")


# ============================================================================
# RESET / IMPORTAR ESTADO
# ============================================================================

def painel_controlo():
    st.sidebar.divider()
    st.sidebar.subheader("⚙️ Controlo")

    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button("🔄 Reset", use_container_width=True):
            st.session_state.empresa  = Empresa()
            st.session_state.historico = []
            st.rerun()
    with col2:
        if st.button("📤 Exportar", use_container_width=True):
            import json
            estado_json = json.dumps(st.session_state.empresa.estado, indent=2,
                                     default=str)
            st.sidebar.download_button("⬇️ Download estado",
                                        data=estado_json,
                                        file_name=f"gmc_estado_Y{st.session_state.empresa.estado['ano']}Q{st.session_state.empresa.estado['trimestre']}.json",
                                        mime="application/json")

    # Importar estado JSON
    uploaded = st.sidebar.file_uploader("📥 Importar estado (.json)", type="json")
    if uploaded:
        import json
        estado = json.load(uploaded)
        st.session_state.empresa = Empresa(estado)
        st.rerun()


# ============================================================================
# MAIN
# ============================================================================

def main():
    decisoes = sidebar_decisoes()
    painel_controlo()

    # ── Guia rápido (só aparece antes da primeira simulação) ─────────────────
    if not st.session_state.historico:
        st.title("🏭 GMC Simulator")
        st.info("""
**Como usar esta app:**

1. **Barra lateral (esquerda)** → introduz as tuas decisões para o trimestre:
   - Turnos de produção, matéria-prima a comprar, unidades a produzir
   - Preços e entregas por mercado (UE / NAFTA / Internet)
   - Agentes, recursos humanos, publicidade, finanças

2. **Validação prévia** (abaixo) → mostra erros antes de simular

3. **Botão "Simular Trimestre"** → calcula o resultado e avança o trimestre

4. **Dashboard** → mostra a Demonstração de Resultados, Balanço e produção
        """)
        st.divider()

    # Validação prévia
    erros = painel_validacao(decisoes)

    # Estado actual
    painel_estado()

    # Botão simular
    st.divider()
    simular_col, _ = st.columns([1, 4])
    with simular_col:
        simular = st.button("▶️ Simular Trimestre", type="primary",
                             use_container_width=True, disabled=bool(erros))

    relatorio = None
    if simular:
        try:
            ano_antes = st.session_state.empresa.estado["ano"]
            trim_antes = st.session_state.empresa.estado["trimestre"]

            relatorio = st.session_state.empresa.simular_trimestre(decisoes)
            relatorio["ano"] = ano_antes
            relatorio["trimestre"] = trim_antes
            relatorio["estado_final"] = copy.deepcopy(st.session_state.empresa.estado)

            st.session_state.historico.append(relatorio)
            st.success(f"✅ Simulação Y{ano_antes}Q{trim_antes} concluída!")
        except Exception as ex:
            st.error(f"Erro na simulação: {ex}")
            import traceback
            st.code(traceback.format_exc())

    mostrar_dashboard(relatorio)


if __name__ == "__main__":
    main()
