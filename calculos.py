"""Regras de negócio da Calculadora Financeira (sem interface).

Este arquivo é compartilhado pelas versões de computador (app.py) e de celular (main.py).
"""
import ast
import math
import re
from dataclasses import dataclass
from typing import Callable, Optional


class ErroDeCalculo(Exception):
    """Erro de entrada que pode ser mostrado ao usuário."""


class CamposVazios(ErroDeCalculo):
    """Ainda há campos obrigatórios sem preencher."""


# ---------- Formatação (padrão brasileiro) ----------
def _br(v: float, casas: int) -> str:
    return f"{v:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def brl(v: float) -> str:
    return "R$ " + _br(v, 2)


def pct(v: float) -> str:
    return _br(v, 2) + "%"


def num(v: float) -> str:
    return _br(v, 4).rstrip("0").rstrip(",")


FORMATADORES = {"brl": brl, "pct": pct, "num": num}


def converter_numero(texto: str) -> float:
    """Aceita '1,5' ou '1.5'. Levanta ValueError se for inválido."""
    n = float(texto.strip().replace(",", "."))
    if not math.isfinite(n):
        raise ValueError("número fora do alcance")
    return n


def formatar_resultado(v: float) -> str:
    """Formato do visor da calculadora comum: 14 | 2,5 | 0,3"""
    if not math.isfinite(v):
        raise ErroDeCalculo("Resultado fora do alcance.")
    if v == int(v) and abs(v) < 1e15:
        return str(int(v))
    return f"{v:.10g}".replace(".", ",")


# ---------- Avaliador seguro de expressões ----------
def _no(n):
    if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)) and not isinstance(n.value, bool):
        return float(n.value)
    if isinstance(n, ast.UnaryOp) and isinstance(n.op, (ast.USub, ast.UAdd)):
        x = _no(n.operand)
        return -x if isinstance(n.op, ast.USub) else x
    if isinstance(n, ast.BinOp):
        a, b, op = _no(n.left), _no(n.right), n.op
        if isinstance(op, ast.Add):
            return a + b
        if isinstance(op, ast.Sub):
            return a - b
        if isinstance(op, ast.Mult):
            return a * b
        if isinstance(op, ast.Div):
            if b == 0:
                raise ErroDeCalculo("Não é possível dividir por zero.")
            return a / b
        if isinstance(op, ast.Pow):
            if abs(b) > 1000:
                raise ErroDeCalculo("Expoente grande demais.")
            if a == 0 and b < 0:
                raise ErroDeCalculo("Não é possível dividir por zero.")
            r = a ** b
            if isinstance(r, complex):
                raise ErroDeCalculo("O resultado não é um número real.")
            return r
    raise ErroDeCalculo("Expressão inválida.")


def avaliar_expressao(texto: str) -> float:
    """Calcula '2+3×(4−1)^2', '200×10%', '2(3+4)'... respeitando a ordem das operações."""
    t = texto.strip()
    if not t:
        raise ErroDeCalculo("Digite uma conta.")
    t = (t.replace("×", "*").replace("÷", "/").replace("−", "-")
          .replace(",", ".").replace("^", "**"))
    t = re.sub(r"(\d+(?:\.\d+)?)%", r"(\1/100)", t)        # 10% -> (10/100)
    t = re.sub(r"(\d|\))\s*\(", r"\1*(", t)                 # 2(3) -> 2*(3)
    abertos = t.count("(") - t.count(")")
    if abertos < 0:
        raise ErroDeCalculo("Há parênteses sem abrir.")
    t += ")" * abertos                                       # fecha parênteses pendentes
    try:
        return _no(ast.parse(t, mode="eval").body)
    except SyntaxError:
        raise ErroDeCalculo("Expressão incompleta ou inválida.") from None
    except (OverflowError, ZeroDivisionError):
        raise ErroDeCalculo("O resultado é grande demais para ser calculado.") from None
    except (RecursionError, MemoryError):
        raise ErroDeCalculo("Expressão complexa demais.") from None


# ---------- Calculadora comum (visor + teclado) ----------
TECLAS = [["C", "(", ")", "⌫"],
          ["7", "8", "9", "÷"],
          ["4", "5", "6", "×"],
          ["1", "2", "3", "−"],
          ["0", ",", "%", "+"],
          ["^", "="]]


class CalculadoraComum:
    """Guarda o estado do visor. A interface só envia teclas e mostra o estado."""
    OPERADORES = "+−×÷^"

    def __init__(self):
        self.expressao = ""
        self.previa = ""
        self.erro = ""
        self.acabou = False
        self.historico: list[tuple[str, str]] = []

    @property
    def valor_atual(self) -> str:
        return self.expressao if self.acabou else (self.previa or self.expressao)

    def tecla(self, t: str):
        self.erro = ""
        if t == "C":
            self.expressao, self.acabou = "", False
        elif t == "⌫":
            self.acabou = False
            self.expressao = self.expressao[:-1]
        elif t == "=":
            self._igual()
        else:
            self._inserir(t)
        self._atualizar_previa()

    def _inserir(self, t: str):
        op = self.OPERADORES
        if self.acabou:
            self.acabou = False
            if t not in op and t != "%":     # número novo apaga o resultado; operador continua a conta
                self.expressao = ""
        e = self.expressao
        if t in op:
            if not e:
                if t == "−":
                    self.expressao = "−"
                return
            if e[-1] == "(":
                if t == "−":
                    self.expressao += t
                return
            if e[-1] in op:
                if t == "−" and e[-1] in "×÷^":      # 5×−3
                    self.expressao += t
                    return
                while e and e[-1] in op:             # troca o operador
                    e = e[:-1]
                self.expressao = e + t if e else ""
                return
        elif t == ",":
            ultimo = re.split(r"[+−×÷^()%]", e)[-1]
            if "," in ultimo:
                return
            if ultimo == "":
                t = "0,"
        elif t == "%":
            if not e or not e[-1].isdigit():
                return
        elif t == ")":
            if e.count("(") - e.count(")") <= 0 or not e or e[-1] in op + "(":
                return
        self.expressao += t

    def _igual(self):
        if not self.expressao:
            return
        try:
            txt = formatar_resultado(avaliar_expressao(self.expressao))
        except ErroDeCalculo as ex:
            self.erro = str(ex)
            return
        txt = txt.replace("-", "−")
        self.historico = (self.historico + [(self.expressao, txt)])[-20:]
        self.expressao, self.acabou = txt, True

    def _atualizar_previa(self):
        self.previa = ""
        if self.acabou or not self.expressao:
            return
        try:
            txt = formatar_resultado(avaliar_expressao(self.expressao)).replace("-", "−")
        except ErroDeCalculo:
            return
        if txt != self.expressao:
            self.previa = txt


# ---------- Modelo das demais calculadoras ----------
@dataclass
class Campo:
    chave: str
    rotulo: str
    prefixo: str = ""
    sufixo: str = ""
    percentual: bool = False        # usuário digita 1,5 e o valor vira 0.015
    opcional: bool = False
    opcoes: Optional[list] = None   # se existir, vira lista de escolha


@dataclass
class Calculadora:
    id: str
    nome: str
    descricao: str
    campos: list
    funcao: Optional[Callable]      # -> [(rótulo, valor, formato)]
    especial: bool = False          # True = usa o teclado da calculadora comum


def executar(calc: Calculadora, brutos: dict) -> list:
    """Valida os textos digitados, calcula e devolve [(rótulo, texto formatado)]."""
    valores = {}
    for campo in calc.campos:
        bruto = brutos.get(campo.chave, "")
        if campo.opcoes:
            valores[campo.chave] = bruto
            continue
        if bruto.strip() == "":
            if campo.opcional:
                valores[campo.chave] = 0.0
                continue
            raise CamposVazios("Preencha os campos para ver o resultado.")
        try:
            n = converter_numero(bruto)
        except ValueError:
            raise ErroDeCalculo(f"Valor inválido em “{campo.rotulo}”. Use apenas números.") from None
        valores[campo.chave] = n / 100 if campo.percentual else n
    try:
        linhas = calc.funcao(valores)
    except OverflowError:
        raise ErroDeCalculo("O resultado é grande demais para ser calculado.") from None
    return [(r, FORMATADORES[f](v)) for r, v, f in linhas]


# ---------- Cálculos ----------
def juros_simples(v):
    j = v["c"] * v["i"] * v["t"]
    return [("Montante", v["c"] + j, "brl"), ("Juros", j, "brl"), ("Capital", v["c"], "brl")]


def juros_compostos(v):
    g = (1 + v["i"]) ** v["t"]
    aportes = v["a"] * v["t"] if v["i"] == 0 else v["a"] * (g - 1) / v["i"]
    montante_final = v["c"] * g + aportes
    investido = v["c"] + v["a"] * v["t"]
    return [("Montante", montante_final, "brl"), ("Total investido", investido, "brl"),
            ("Juros ganhos", montante_final - investido, "brl")]


def montante(v):
    return [("Montante", v["c"] + v["j"], "brl")]


def parcela_price(v):
    if v["t"] <= 0:
        raise ErroDeCalculo("O número de parcelas deve ser maior que zero.")
    p = v["c"] / v["t"] if v["i"] == 0 else v["c"] * v["i"] / (1 - (1 + v["i"]) ** -v["t"])
    return [("Valor da parcela", p, "brl"), ("Total pago", p * v["t"], "brl"),
            ("Total de juros", p * v["t"] - v["c"], "brl")]


def valor_presente(v):
    d = 1 + v["i"] * v["t"]
    if d == 0:
        raise ErroDeCalculo("O denominador não pode ser zero. Revise a taxa e o tempo.")
    vp = v["c"] / d
    return [("Valor presente", vp, "brl"), ("Diferença", v["c"] - vp, "brl")]


def desconto(v):
    return [("Valor com desconto", v["c"] * (1 - v["d"]), "brl"), ("Economia", v["c"] * v["d"], "brl")]


def inflacao(v):
    if v["vp"] == 0:
        raise ErroDeCalculo("O valor passado não pode ser zero.")
    return [("Inflação", (v["va"] - v["vp"]) / v["vp"] * 100, "pct"), ("Diferença", v["va"] - v["vp"], "brl")]


def anos_meses(v):
    if v["m"] == "Meses para anos":
        return [("Anos", v["x"] / 12, "num")]
    return [("Meses", v["x"] * 12, "num")]


# ---------- Registro (as interfaces são montadas a partir daqui) ----------
_C = Campo("c", "Capital", prefixo="R$")
_I = Campo("i", "Taxa", sufixo="% por período", percentual=True)
_T = Campo("t", "Tempo", sufixo="períodos")

CALCULADORAS = [
    Calculadora("calculadora", "Calculadora comum",
                "Várias operações de uma vez, com parênteses, potência (^) e porcentagem.",
                [], None, especial=True),
    Calculadora("juros-simples", "Juros simples", "J = C × i × t. Juros sempre sobre o capital inicial.",
                [_C, _I, _T], juros_simples),
    Calculadora("juros-compostos", "Juros compostos", "M = C × (1 + i)^t. O aporte por período é opcional.",
                [_C, _I, _T, Campo("a", "Aporte por período", prefixo="R$", opcional=True)], juros_compostos),
    Calculadora("montante", "Montante", "M = C + J.",
                [_C, Campo("j", "Juros", prefixo="R$")], montante),
    Calculadora("parcela", "Parcela de financiamento",
                "Parcela fixa pela Tabela Price. Use taxa e prazo na mesma unidade.",
                [Campo("c", "Valor financiado", prefixo="R$"), _I,
                 Campo("t", "Número de parcelas", sufixo="parcelas")], parcela_price),
    Calculadora("valor-presente", "Valor presente", "VP = VF ÷ (1 + i × t), com juros simples.",
                [Campo("c", "Valor futuro", prefixo="R$"), _I, _T], valor_presente),
    Calculadora("desconto", "Desconto à vista", "Quanto você paga e quanto economiza.",
                [Campo("c", "Valor do produto", prefixo="R$"),
                 Campo("d", "Desconto", sufixo="%", percentual=True)], desconto),
    Calculadora("inflacao", "Inflação", "Variação percentual entre um valor passado e um atual.",
                [Campo("va", "Valor atual", prefixo="R$"), Campo("vp", "Valor passado", prefixo="R$")], inflacao),
    Calculadora("anos-meses", "Anos e meses", "Converte prazos entre anos e meses.",
                [Campo("x", "Valor"), Campo("m", "Converter", opcoes=["Anos para meses", "Meses para anos"])],
                anos_meses),
]
