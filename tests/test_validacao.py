"""
Testes de validação e motor GMC
Executar: python -m pytest tests/ -v
"""
import sys
import os
import copy
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from gmc_engine import Empresa, ESTADO_INICIAL_PADRAO
from utils.validacao import validar_decisoes


# ── Decisões mínimas válidas ─────────────────────────────────────────────────
DECISOES_MINIMAS = {
    "turnos": 1,
    "tempo_montagem": {"P1": 100, "P2": 150, "P3": 300},
    "maquinas": {"comprar": 0, "vender": 0},
    "compra_mp": {"spot": 0, "3m": 0, "6m": 0},
    "mp_extra_pct": {"P1": 0, "P2": 0, "P3": 0},
    "producao": {"P1": 0, "P2": 0, "P3": 0},
    "entregas": {
        "P1": {"UE": 0, "NAFTA": 0, "Internet": 0},
        "P2": {"UE": 0, "NAFTA": 0, "Internet": 0},
        "P3": {"UE": 0, "NAFTA": 0, "Internet": 0},
    },
    "precos": {
        "P1": {"UE": 200.0, "NAFTA": 210.0, "Internet": 195.0},
        "P2": {"UE": 350.0, "NAFTA": 365.0, "Internet": 340.0},
        "P3": {"UE": 700.0, "NAFTA": 720.0, "Internet": 680.0},
    },
    "agentes_ue": {"total": 2, "apoio": 5_000, "comissao_pct": 3.0},
    "dist_nafta": {"total": 0, "apoio": 0, "comissao_pct": 0.0},
    "dist_internet": {"ativo": False, "apoio": 0, "comissao_pct": 0.0},
    "portas_website": 0,
    "operarios_esp": {"recrutar": 0, "treinar": 0, "despedir": 0, "salario_hora": 900},
    "dias_formacao": 0,
    "publicidade": {
        "imagem_corporativa": 0,
        "P1": {"UE": 0, "NAFTA": 0, "Internet": 0},
        "P2": {"UE": 0, "NAFTA": 0, "Internet": 0},
        "P3": {"UE": 0, "NAFTA": 0, "Internet": 0},
    },
    "orcamento_gestao": 40_000,
    "investimento_id": 0,
    "expansao_fabrica": 0,
    "plano_seguro": 0,
    "deposito_prazo": 2_400_000,
    "emprestimo_prazo_novo": 0,
    "emprestimo_prazo_reembolso": 0,
    "dividendo_pct": 0,
    "horas_conservacao": 0,
    "taxa_bce_ue": 0.015,
    "taxa_cambio_eur_usd": 0.73,
    "preco_mp_spot_usd": 74_574,
    "preco_mp_3m_usd": 73_402,
    "preco_mp_6m_usd": 72_229,
}


# ============================================================================
# Testes de validação
# ============================================================================

class TestValidacao:
    def _estado(self, **override):
        e = copy.deepcopy(ESTADO_INICIAL_PADRAO)
        e.update(override)
        return e

    def _decisoes(self, **override):
        d = copy.deepcopy(DECISOES_MINIMAS)
        d.update(override)
        return d

    def test_sem_alertas_decisoes_validas(self):
        alertas = validar_decisoes(DECISOES_MINIMAS, ESTADO_INICIAL_PADRAO)
        erros = [a for a in alertas if a.tipo == "erro"]
        assert erros == [], f"Erros inesperados: {[a.msg for a in erros]}"

    def test_preco_negativo_gera_erro(self):
        d = self._decisoes()
        d["precos"]["P1"]["UE"] = -1.0
        alertas = validar_decisoes(d, ESTADO_INICIAL_PADRAO)
        assert any(a.tipo == "erro" and "Preço negativo" in a.msg for a in alertas)

    def test_tempo_montagem_abaixo_minimo_gera_erro(self):
        d = self._decisoes()
        d["tempo_montagem"]["P1"] = 50  # mínimo é 100
        alertas = validar_decisoes(d, ESTADO_INICIAL_PADRAO)
        assert any(a.tipo == "erro" and "P1" in a.msg for a in alertas)

    def test_turnos_invalido(self):
        d = self._decisoes(turnos=4)
        alertas = validar_decisoes(d, ESTADO_INICIAL_PADRAO)
        assert any(a.tipo == "erro" and "turnos" in a.msg.lower() for a in alertas)

    def test_entrega_ue_sem_agentes(self):
        d = self._decisoes()
        d["entregas"]["P1"]["UE"] = 100
        d["agentes_ue"]["total"] = 0
        alertas = validar_decisoes(d, ESTADO_INICIAL_PADRAO)
        assert any(a.tipo == "erro" and "UE" in a.msg for a in alertas)

    def test_entrega_nafta_sem_distribuidores(self):
        d = self._decisoes()
        d["entregas"]["P1"]["NAFTA"] = 50
        # dist_nafta.total já é 0 nas decisões mínimas
        alertas = validar_decisoes(d, ESTADO_INICIAL_PADRAO)
        assert any(a.tipo == "erro" and "NAFTA" in a.msg for a in alertas)

    def test_eficiencia_baixa_gera_aviso(self):
        estado = self._estado(eficiencia_maquinas=70.0)
        alertas = validar_decisoes(DECISOES_MINIMAS, estado)
        assert any(a.tipo == "aviso" and "eficiência" in a.msg.lower() for a in alertas)

    def test_dividendos_acima_transitados_gera_erro(self):
        d = self._decisoes(dividendo_pct=10.0)
        estado = self._estado(capital_social=4_000_000, resultados_transitados=0)
        alertas = validar_decisoes(d, estado)
        assert any(a.tipo == "erro" and "ividendo" in a.msg for a in alertas)

    def test_capacidade_esp_insuficiente_gera_erro(self):
        d = self._decisoes()
        # Planear muitas entregas com apenas 11 esp
        d["entregas"] = {
            "P1": {"UE": 5000, "NAFTA": 0, "Internet": 0},
            "P2": {"UE": 0,    "NAFTA": 0, "Internet": 0},
            "P3": {"UE": 0,    "NAFTA": 0, "Internet": 0},
        }
        alertas = validar_decisoes(d, ESTADO_INICIAL_PADRAO)
        assert any("especializada" in a.msg.lower() or "esp" in a.msg.lower()
                   for a in alertas)


# ============================================================================
# Testes do motor (smoke tests)
# ============================================================================

class TestMotor:
    def _empresa(self):
        return Empresa(copy.deepcopy(ESTADO_INICIAL_PADRAO))

    def _decisoes_zero(self):
        return copy.deepcopy(DECISOES_MINIMAS)

    def test_simular_trimestre_retorna_dict(self):
        emp = self._empresa()
        resultado = emp.simular_trimestre(self._decisoes_zero())
        assert isinstance(resultado, dict)

    def test_estado_avanca_trimestre(self):
        emp = self._empresa()
        trimestre_antes = emp.estado["trimestre"]
        emp.simular_trimestre(self._decisoes_zero())
        assert emp.estado["trimestre"] != trimestre_antes or emp.estado["ano"] != 2015

    def test_resultado_contem_chaves_essenciais(self):
        emp = self._empresa()
        r = emp.simular_trimestre(self._decisoes_zero())
        for chave in ("dr", "balanco", "producao", "alertas"):
            assert chave in r, f"Chave '{chave}' ausente no relatório"

    def test_balanço_equilibrado(self):
        emp = self._empresa()
        r = emp.simular_trimestre(self._decisoes_zero())
        bal = r.get("balanco", {})
        total_ativo  = bal.get("total_ativo", 0)
        total_passivo = bal.get("total_cp_passivo", 0)
        if total_ativo and total_passivo:
            assert abs(total_ativo - total_passivo) < 1.0, (
                f"Balanço desequilibrado: Activo={total_ativo:.2f}, CP+Passivo={total_passivo:.2f}"
            )

    def test_producao_zero_com_zero_mp(self):
        emp = self._empresa()
        emp.estado["inventario_mp"] = 0
        emp.estado["mp_proximo_trim"] = 0
        d = self._decisoes_zero()
        d["producao"] = {"P1": 100, "P2": 0, "P3": 0}
        r = emp.simular_trimestre(d)
        # Sem MP, produção efectiva deve ser 0
        assert r.get("producao", {}).get("produzidas", {}).get("P1", 0) == 0

    def test_cash_diminui_com_gastos(self):
        emp = self._empresa()
        cash_antes = emp.estado["cash"]
        d = self._decisoes_zero()
        d["publicidade"]["imagem_corporativa"] = 100_000
        emp.simular_trimestre(d)
        assert emp.estado["cash"] < cash_antes

    def test_quatro_trimestres_sequenciais(self):
        emp = self._empresa()
        for q in range(4):
            d = self._decisoes_zero()
            r = emp.simular_trimestre(d)
            assert isinstance(r, dict), f"Q{q+1} falhou"

    def test_imposto_apenas_q4(self):
        emp = self._empresa()
        # Simular Q2, Q3, Q4 forçando lucro
        emp.estado["lucro_tributavel_acumulado"] = 500_000
        for q in range(3):
            emp.estado["trimestre"] = q + 2  # Q2, Q3, Q4
            d = self._decisoes_zero()
            r = emp.simular_trimestre(d)
            imp = r.get("dr", {}).get("imposto", 0)
            if q < 2:  # Q2 e Q3
                assert imp == 0, f"Imposto não deveria ser cobrado em Q{q+2}"
            # Q4 pode ter imposto

    def test_depreciacao_reduz_valor_maquinas(self):
        emp = self._empresa()
        valor_antes = emp.estado["valor_maquinas"]
        emp.simular_trimestre(self._decisoes_zero())
        valor_depois = emp.estado["valor_maquinas"]
        assert valor_depois <= valor_antes


# ============================================================================
# Testes de calibração com dados históricos Y15Q2
# ============================================================================

class TestCalibracao:
    """
    Validação contra o relatório histórico do Y15Q2.
    Tolerância: 5% (valores históricos aproximados da extracção do Excel).
    """

    TOLERANCIA = 0.05  # 5%

    # Valores de referência aproximados do histórico HstY15Q1
    REF_Y15Q2 = {
        # A preencher com os valores reais do relatório após extracção
        # "vendas": 0,
        # "resultado_liquido": 0,
        # "cash": 0,
    }

    def _perto(self, valor: float, referencia: float) -> bool:
        if referencia == 0:
            return abs(valor) < 1.0
        return abs(valor - referencia) / abs(referencia) <= self.TOLERANCIA

    def test_placeholder_calibracao(self):
        """Placeholder – preencher com valores históricos reais após validação."""
        emp = Empresa(copy.deepcopy(ESTADO_INICIAL_PADRAO))
        # Decisões Y15Q2 reais (a preencher com os valores submetidos no histórico)
        d = copy.deepcopy(DECISOES_MINIMAS)
        r = emp.simular_trimestre(d)
        # Quando os valores de referência estiverem preenchidos:
        for chave, ref in self.REF_Y15Q2.items():
            valor = r.get("dr", {}).get(chave, r.get(chave, None))
            if valor is not None and ref != 0:
                assert self._perto(valor, ref), (
                    f"{chave}: obtido {valor:.0f}, esperado {ref:.0f} (tol {self.TOLERANCIA*100:.0f}%)"
                )
