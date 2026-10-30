"""Calculadora Financeira - versão para celular (Flet -> APK).

Para testar no computador:  pip install flet==0.28.3  e depois  python main.py
Para gerar o APK:           flet build apk
"""
import flet as ft

from calculos import (CALCULADORAS, TECLAS, CalculadoraComum, CamposVazios,
                      ErroDeCalculo, executar)


def main(page: ft.Page):
    page.title = "Calculadora Financeira"
    page.theme = ft.Theme(color_scheme_seed="#0b6b57")
    page.dark_theme = ft.Theme(color_scheme_seed="#0b6b57")
    page.theme_mode = ft.ThemeMode.SYSTEM
    page.padding = 0
    page.scroll = ft.ScrollMode.AUTO

    comum = CalculadoraComum()
    atual = {"calc": CALCULADORAS[0], "campos": {}}
    resultado = ft.Column(spacing=4)
    corpo = ft.Column(spacing=12)

    mudo = ft.Colors.ON_SURFACE_VARIANT

    # ---------- formulários ----------
    def recalcular(e=None):
        resultado.controls.clear()
        brutos = {k: (c.value or "") for k, c in atual["campos"].items()}
        try:
            linhas = executar(atual["calc"], brutos)
        except CamposVazios as ex:
            resultado.controls.append(ft.Text(str(ex), color=mudo))
        except ErroDeCalculo as ex:
            resultado.controls.append(ft.Text(str(ex), color=ft.Colors.ERROR, weight=ft.FontWeight.BOLD))
        else:
            resultado.controls.append(ft.Text(linhas[0][0], color=mudo))
            resultado.controls.append(ft.Text(linhas[0][1], size=34, weight=ft.FontWeight.BOLD,
                                              color=ft.Colors.PRIMARY))
            for rot, val in linhas[1:]:
                resultado.controls.append(ft.Row(
                    [ft.Text(rot), ft.Text(val, weight=ft.FontWeight.BOLD)],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN))
        page.update()

    def montar_formulario(calc):
        campos, itens = {}, [ft.Text(calc.descricao, color=mudo)]
        for c in calc.campos:
            if c.opcoes:
                ctl = ft.Dropdown(label=c.rotulo, value=c.opcoes[0],
                                  options=[ft.dropdown.Option(o) for o in c.opcoes],
                                  on_change=recalcular)
            else:
                ctl = ft.TextField(label=c.rotulo + (" (opcional)" if c.opcional else ""),
                                   prefix_text=(c.prefixo + " ") if c.prefixo else None,
                                   suffix_text=c.sufixo or None,
                                   keyboard_type=ft.KeyboardType.NUMBER, on_change=recalcular)
            campos[c.chave] = ctl
            itens.append(ctl)
        atual["campos"] = campos
        return itens + [ft.Divider(), resultado]

    # ---------- calculadora comum ----------
    v_hist = ft.Text("", size=12, color=mudo, text_align=ft.TextAlign.RIGHT)
    v_expr = ft.Text("0", size=36, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.RIGHT)
    v_previa = ft.Text("", size=18, color=mudo, text_align=ft.TextAlign.RIGHT)

    def atualizar_visor():
        v_expr.value = comum.expressao or "0"
        v_expr.size = 36 if len(v_expr.value) <= 12 else 24
        v_previa.value = comum.erro or (("= " + comum.previa) if comum.previa else "")
        v_previa.color = ft.Colors.ERROR if comum.erro else mudo
        v_hist.value = "\n".join(f"{a} = {b}" for a, b in comum.historico[-3:])
        page.update()

    def pressionar(t):
        comum.tecla(t)
        atualizar_visor()

    def estilo(t):
        if t == "=":
            return ft.ButtonStyle(bgcolor=ft.Colors.PRIMARY, color=ft.Colors.ON_PRIMARY)
        if t in "+−×÷^%":
            return ft.ButtonStyle(bgcolor=ft.Colors.PRIMARY_CONTAINER, color=ft.Colors.ON_PRIMARY_CONTAINER)
        return None

    def copiar(e):
        if comum.valor_atual:
            page.set_clipboard(comum.valor_atual)

    def montar_teclado():
        visor = ft.Container(
            padding=12, border_radius=12, bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
            content=ft.Column([ft.Row([v_hist], alignment=ft.MainAxisAlignment.END),
                               ft.Row([v_expr], alignment=ft.MainAxisAlignment.END),
                               ft.Row([v_previa], alignment=ft.MainAxisAlignment.END)], spacing=2))
        linhas = [ft.Row([ft.ElevatedButton(text=t, expand=3 if t == "=" else 1, height=58,
                                            style=estilo(t), on_click=lambda e, t=t: pressionar(t))
                          for t in linha], spacing=8)
                  for linha in TECLAS]
        return [visor] + linhas + [ft.TextButton("Copiar resultado", on_click=copiar)]

    # ---------- navegação ----------
    def selecionar(calc):
        atual["calc"] = calc
        corpo.controls = montar_teclado() if calc.especial else montar_formulario(calc)
        if calc.especial:
            atualizar_visor()
        else:
            recalcular()

    def trocar(e):
        selecionar(next(c for c in CALCULADORAS if c.id == menu.value))

    menu = ft.Dropdown(label="Operação", value=CALCULADORAS[0].id, on_change=trocar,
                       options=[ft.dropdown.Option(key=c.id, text=c.nome) for c in CALCULADORAS])

    page.add(ft.SafeArea(ft.Container(
        padding=16,
        content=ft.Column([ft.Text("Calculadora Financeira", size=22, weight=ft.FontWeight.W_800),
                           menu, corpo], spacing=14))))
    selecionar(CALCULADORAS[0])


ft.app(target=main)
