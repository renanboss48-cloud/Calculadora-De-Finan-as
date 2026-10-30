import unittest
from calculos import (CALCULADORAS, CalculadoraComum, CamposVazios, ErroDeCalculo,
                      avaliar_expressao, brl, executar, juros_compostos, parcela_price, inflacao)


def digitar(c, teclas):
    for t in teclas:
        c.tecla(t)
    return c


class TestesFinanceiros(unittest.TestCase):
    def test_compostos(self):
        self.assertAlmostEqual(juros_compostos({"c": 1000, "i": 0.1, "t": 2, "a": 0})[0][1], 1210)

    def test_compostos_com_aporte(self):
        self.assertAlmostEqual(juros_compostos({"c": 0, "i": 0.01, "t": 12, "a": 100})[0][1], 1268.25, places=2)

    def test_price(self):
        self.assertAlmostEqual(parcela_price({"c": 10000, "i": 0.02, "t": 12})[0][1], 945.60, places=2)

    def test_inflacao(self):
        self.assertAlmostEqual(inflacao({"va": 110, "vp": 100})[0][1], 10)
        with self.assertRaises(ErroDeCalculo):
            inflacao({"va": 1, "vp": 0})

    def test_formato(self):
        self.assertEqual(brl(1234.5), "R$ 1.234,50")

    def test_executar(self):
        calc = next(c for c in CALCULADORAS if c.id == "desconto")
        self.assertEqual(executar(calc, {"c": "500", "d": "10"})[0][1], "R$ 450,00")
        with self.assertRaises(CamposVazios):
            executar(calc, {"c": "", "d": "10"})
        with self.assertRaises(ErroDeCalculo):
            executar(calc, {"c": "abc", "d": "10"})


class TestesExpressoes(unittest.TestCase):
    def test_ordem_das_operacoes(self):
        self.assertEqual(avaliar_expressao("2+3×4"), 14)
        self.assertEqual(avaliar_expressao("(2+3)×4"), 20)
        self.assertEqual(avaliar_expressao("2^3^2"), 512)

    def test_varias_operacoes(self):
        self.assertEqual(avaliar_expressao("100−20÷4+3×2"), 101)

    def test_decimais_e_porcentagem(self):
        self.assertAlmostEqual(avaliar_expressao("0,1+0,2"), 0.3)
        self.assertEqual(avaliar_expressao("200×10%"), 20)

    def test_negativos_e_multiplicacao_implicita(self):
        self.assertEqual(avaliar_expressao("5×−3"), -15)
        self.assertEqual(avaliar_expressao("2(3+4)"), 14)

    def test_parenteses_pendentes(self):
        self.assertEqual(avaliar_expressao("(1+2"), 3)

    def test_erros(self):
        for ruim in ["5÷0", "5+", "2)", "abc", "__import__('os')", "2**9999", "(−8)^0,5"]:
            with self.assertRaises(ErroDeCalculo, msg=ruim):
                avaliar_expressao(ruim)


class TestesVisor(unittest.TestCase):
    def test_conta_completa(self):
        c = digitar(CalculadoraComum(), "2+3×4")
        self.assertEqual(c.previa, "14")
        c.tecla("=")
        self.assertEqual((c.expressao, c.acabou), ("14", True))

    def test_continua_do_resultado(self):
        c = digitar(CalculadoraComum(), "2+3=")
        digitar(c, "×4=")
        self.assertEqual(c.expressao, "20")

    def test_numero_novo_apaga_resultado(self):
        c = digitar(CalculadoraComum(), "2+3=")
        digitar(c, "7")
        self.assertEqual(c.expressao, "7")

    def test_troca_de_operador(self):
        self.assertEqual(digitar(CalculadoraComum(), "5+×3").expressao, "5×3")

    def test_virgula_duplicada(self):
        self.assertEqual(digitar(CalculadoraComum(), "1,,5").expressao, "1,5")

    def test_erro_mantem_conta(self):
        c = digitar(CalculadoraComum(), "5÷0=")
        self.assertTrue(c.erro)
        self.assertEqual(c.expressao, "5÷0")

    def test_apagar_e_limpar(self):
        c = digitar(CalculadoraComum(), "123⌫")
        self.assertEqual(c.expressao, "12")
        c.tecla("C")
        self.assertEqual(c.expressao, "")


if __name__ == "__main__":
    unittest.main()
