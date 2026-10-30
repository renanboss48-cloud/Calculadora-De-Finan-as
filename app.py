"""Calculadora Financeira - versão para computador (tkinter, já vem com o Python)."""
import tkinter as tk
from tkinter import ttk

from calculos import (CALCULADORAS, TECLAS, CalculadoraComum, CamposVazios,
                      ErroDeCalculo, executar)

COR_FUNDO = "#f2f4f3"
COR_PAINEL = "#ffffff"
COR_TEXTO = "#12241f"
COR_MUDO = "#5d6f69"
COR_DESTAQUE = "#0b6b57"
COR_SUAVE = "#e3efeb"
COR_ERRO = "#a33a2a"
FONTE = "Segoe UI"

TECLAS_FISICAS = {"*": "×", "/": "÷", "-": "−", ".": ",", ",": ",", "=": "=", "x": "×",
                  "+": "+", "(": "(", ")": ")", "%": "%", "^": "^"}


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Calculadora Financeira")
        self.geometry("900x640")
        self.minsize(760, 600)
        self.configure(bg=COR_FUNDO)
        self.atual = None
        self.vars = {}
        self.texto_resultado = ""
        self.comum = CalculadoraComum()
        self._estilo()
        self._layout()
        self.bind("<Key>", self._tecla_fisica)
        self.lista.selection_set(0)
        self.mostrar(0)

    # ---------- estrutura ----------
    def _estilo(self):
        s = ttk.Style(self)
        s.theme_use("clam")
        s.configure("TEntry", padding=6)
        s.configure("TCombobox", padding=6)
        s.configure("Destaque.TButton", background=COR_DESTAQUE, foreground="white",
                    padding=(14, 8), font=(FONTE, 10, "bold"))
        s.map("Destaque.TButton", background=[("active", "#095646")])
        s.configure("TButton", padding=(14, 8), font=(FONTE, 10))

    def _layout(self):
        tk.Label(self, text="Calculadora Financeira", bg=COR_FUNDO, fg=COR_TEXTO,
                 font=(FONTE, 18, "bold")).grid(row=0, column=0, columnspan=2, sticky="w", padx=20, pady=(16, 8))
        self.lista = tk.Listbox(self, exportselection=False, activestyle="none", bd=0,
                                highlightthickness=0, font=(FONTE, 11), bg=COR_FUNDO, fg=COR_TEXTO,
                                selectbackground=COR_SUAVE, selectforeground=COR_TEXTO, width=26)
        for c in CALCULADORAS:
            self.lista.insert("end", "  " + c.nome)
        self.lista.grid(row=1, column=0, sticky="ns", padx=(20, 10), pady=(0, 20))
        self.lista.bind("<<ListboxSelect>>", lambda e: self.mostrar(self.lista.curselection()[0]))
        self.painel = tk.Frame(self, bg=COR_PAINEL, highlightbackground="#d9e0dd", highlightthickness=1)
        self.painel.grid(row=1, column=1, sticky="nsew", padx=(0, 20), pady=(0, 20))
        self.rowconfigure(1, weight=1)
        self.columnconfigure(1, weight=1)

    def mostrar(self, indice):
        self.atual = CALCULADORAS[indice]
        for w in self.painel.winfo_children():
            w.destroy()
        p = tk.Frame(self.painel, bg=COR_PAINEL)
        p.pack(fill="both", expand=True, padx=24, pady=20)
        tk.Label(p, text=self.atual.nome, bg=COR_PAINEL, fg=COR_TEXTO,
                 font=(FONTE, 15, "bold")).pack(anchor="w")
        tk.Label(p, text=self.atual.descricao, bg=COR_PAINEL, fg=COR_MUDO, font=(FONTE, 10),
                 wraplength=540, justify="left").pack(anchor="w", pady=(2, 12))
        if self.atual.especial:
            self._montar_teclado(p)
        else:
            self._montar_formulario(p, indice)

    # ---------- calculadora comum ----------
    def _montar_teclado(self, p):
        visor = tk.Frame(p, bg=COR_FUNDO)
        visor.pack(fill="x", pady=(0, 10))
        self.l_hist = tk.Label(visor, bg=COR_FUNDO, fg=COR_MUDO, font=(FONTE, 10), anchor="e", justify="right")
        self.l_expr = tk.Label(visor, bg=COR_FUNDO, fg=COR_TEXTO, font=(FONTE, 28, "bold"), anchor="e")
        self.l_previa = tk.Label(visor, bg=COR_FUNDO, fg=COR_MUDO, font=(FONTE, 13), anchor="e")
        for l in (self.l_hist, self.l_expr, self.l_previa):
            l.pack(fill="x", padx=12, pady=1)
        grade = tk.Frame(p, bg=COR_PAINEL)
        grade.pack(fill="both", expand=True)
        for c in range(4):
            grade.columnconfigure(c, weight=1, uniform="k")
        for r, linha in enumerate(TECLAS):
            grade.rowconfigure(r, weight=1)
            for c, t in enumerate(linha):
                if t == "=":
                    bg, fg = COR_DESTAQUE, "white"
                elif t in "+−×÷^%":
                    bg, fg = COR_SUAVE, COR_DESTAQUE
                elif t in "C()⌫":
                    bg, fg = "#e9ecea", COR_TEXTO
                else:
                    bg, fg = COR_FUNDO, COR_TEXTO
                tk.Button(grade, text=t, font=(FONTE, 15, "bold"), relief="flat", bd=0, bg=bg, fg=fg,
                          activebackground=bg, takefocus=0, cursor="hand2",
                          command=lambda t=t: self.pressionar(t)
                          ).grid(row=r, column=c, columnspan=3 if t == "=" else 1,
                                 sticky="nsew", padx=3, pady=3)
        ttk.Button(p, text="Copiar resultado", style="Destaque.TButton",
                   command=self.copiar).pack(anchor="w", pady=(10, 0))
        self._atualizar_visor()

    def pressionar(self, t):
        self.comum.tecla(t)
        self._atualizar_visor()

    def _atualizar_visor(self):
        c = self.comum
        texto = c.expressao or "0"
        self.l_expr.config(text=texto, font=(FONTE, 28 if len(texto) <= 16 else 18, "bold"))
        self.l_previa.config(text=c.erro or (("= " + c.previa) if c.previa else " "),
                             fg=COR_ERRO if c.erro else COR_MUDO)
        self.l_hist.config(text="\n".join(f"{a} = {b}" for a, b in c.historico[-3:]) or " ")

    def _tecla_fisica(self, ev):
        if not (self.atual and self.atual.especial):
            return
        if ev.keysym in ("Return", "KP_Enter"):
            t = "="
        elif ev.keysym == "BackSpace":
            t = "⌫"
        elif ev.keysym == "Escape":
            t = "C"
        elif ev.char and ev.char in "0123456789":
            t = ev.char
        else:
            t = TECLAS_FISICAS.get(ev.char)
        if t:
            self.pressionar(t)

    # ---------- demais calculadoras ----------
    def _montar_formulario(self, p, indice):
        self.vars = {}
        for campo in self.atual.campos:
            linha = tk.Frame(p, bg=COR_PAINEL)
            linha.pack(fill="x", pady=5)
            rotulo = campo.rotulo + (" (opcional)" if campo.opcional else "")
            tk.Label(linha, text=rotulo, bg=COR_PAINEL, fg=COR_TEXTO, width=22, anchor="w",
                     font=(FONTE, 10, "bold")).pack(side="left")
            var = tk.StringVar(value=campo.opcoes[0] if campo.opcoes else "")
            self.vars[campo.chave] = var
            if campo.prefixo:
                tk.Label(linha, text=campo.prefixo, bg=COR_PAINEL, fg=COR_MUDO).pack(side="left", padx=(0, 4))
            if campo.opcoes:
                w = ttk.Combobox(linha, textvariable=var, values=campo.opcoes, state="readonly", width=18)
            else:
                w = ttk.Entry(linha, textvariable=var, width=20)
            w.pack(side="left")
            if campo.sufixo:
                tk.Label(linha, text=campo.sufixo, bg=COR_PAINEL, fg=COR_MUDO).pack(side="left", padx=6)
            var.trace_add("write", lambda *_: self.calcular())
        self.area = tk.Frame(p, bg=COR_PAINEL)
        self.area.pack(fill="both", expand=True, pady=(18, 0))
        botoes = tk.Frame(p, bg=COR_PAINEL)
        botoes.pack(anchor="w")
        ttk.Button(botoes, text="Limpar", command=lambda: self.mostrar(indice)).pack(side="left", padx=(0, 8))
        ttk.Button(botoes, text="Copiar resultado", style="Destaque.TButton",
                   command=self.copiar).pack(side="left")
        self.calcular()

    def calcular(self):
        for w in self.area.winfo_children():
            w.destroy()
        self.texto_resultado = ""
        try:
            linhas = executar(self.atual, {k: v.get() for k, v in self.vars.items()})
        except CamposVazios as e:
            self._msg(str(e), COR_MUDO)
            return
        except ErroDeCalculo as e:
            self._msg(str(e), COR_ERRO)
            return
        tk.Label(self.area, text=linhas[0][0], bg=COR_PAINEL, fg=COR_MUDO, font=(FONTE, 10)).pack(anchor="w")
        tk.Label(self.area, text=linhas[0][1], bg=COR_PAINEL, fg=COR_DESTAQUE,
                 font=(FONTE, 26, "bold")).pack(anchor="w")
        for rot, val in linhas[1:]:
            l = tk.Frame(self.area, bg=COR_PAINEL)
            l.pack(fill="x", pady=2)
            tk.Label(l, text=rot, bg=COR_PAINEL, fg=COR_TEXTO, font=(FONTE, 10)).pack(side="left")
            tk.Label(l, text=val, bg=COR_PAINEL, fg=COR_TEXTO, font=(FONTE, 10, "bold")).pack(side="right")
        self.texto_resultado = "\n".join(f"{r}: {v}" for r, v in linhas)

    def _msg(self, texto, cor):
        tk.Label(self.area, text=texto, bg=COR_PAINEL, fg=cor, font=(FONTE, 10),
                 wraplength=540, justify="left").pack(anchor="w")

    def copiar(self):
        texto = self.comum.valor_atual if self.atual.especial else self.texto_resultado
        if texto:
            self.clipboard_clear()
            self.clipboard_append(texto)


if __name__ == "__main__":
    App().mainloop()
