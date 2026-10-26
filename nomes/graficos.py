"""Gráficos da análise, com um visual único para todos."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # gera imagens sem abrir janela (funciona também no GitHub Actions)
import matplotlib.pyplot as plt
import pandas as pd

from .transformar import nome_proprio, rotulo_decada

CORES = {"feminino": "#c2410c", "masculino": "#1d4ed8"}
PALETA = ["#1d4ed8", "#c2410c", "#15803d", "#7c3aed"]

plt.rcParams.update(
    {
        "figure.dpi": 130,
        "font.size": 10,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.alpha": 0.25,
        "axes.titleweight": "bold",
        "axes.titlelocation": "left",
    }
)

FONTE = "Fonte: IBGE, Censo Demográfico 2010 (API de nomes). Pessoas vivas em 2010, por década de nascimento."


def _finalizar(figura, caminho: Path) -> None:
    figura.text(0.01, 0.01, FONTE, fontsize=7, color="#6b7280")
    figura.tight_layout(rect=(0, 0.03, 1, 1))
    figura.savefig(caminho, bbox_inches="tight")
    plt.close(figura)


def grafico_concentracao(tabela: pd.DataFrame, caminho: Path) -> None:
    figura, eixo = plt.subplots(figsize=(8, 4.2))
    for sexo, grupo in tabela.groupby("sexo"):
        eixo.plot(grupo["decada"], grupo["participacao_lider"], marker="o", lw=2.2, color=CORES[sexo], label=sexo)
        for _, linha in grupo.iloc[[0, -1]].iterrows():
            eixo.annotate(
                f"{linha['lider']} {linha['participacao_lider']:.0f}%",
                (linha["decada"], linha["participacao_lider"]),
                textcoords="offset points",
                xytext=(0, 8 if sexo == "feminino" else -14),
                ha="center",
                fontsize=8,
                color=CORES[sexo],
            )
    eixo.set_title("O nome mais popular perdeu espaço")
    eixo.set_ylabel("% do 1º lugar dentro do top 20")
    eixo.set_xticks(tabela["decada"].unique(), [rotulo_decada(d) for d in tabela["decada"].unique()])
    eixo.set_ylim(0, 72)
    eixo.legend(frameon=False)
    _finalizar(figura, caminho)


def grafico_curvas(series: pd.DataFrame, grupos: dict[str, list[tuple[str, str]]], caminho: Path) -> None:
    figura, eixos = plt.subplots(1, len(grupos), figsize=(11, 4.2), sharey=False)
    for eixo, (titulo, nomes) in zip(eixos, grupos.items(), strict=True):
        for cor, (nome, sexo) in zip(PALETA, nomes, strict=False):
            dados = series[(series["nome"] == nome) & (series["sexo"] == sexo)]
            eixo.plot(
                dados["decada"],
                dados["frequencia"] / 1000,
                marker="o",
                ms=3.5,
                lw=2,
                color=cor,
                label=nome_proprio(nome),
            )
        eixo.set_title(titulo)
        eixo.set_ylabel("nascimentos (mil)")
        decadas = sorted(series["decada"].unique())
        eixo.set_xticks(decadas, [rotulo_decada(d)[2:] for d in decadas])
        eixo.legend(frameon=False, fontsize=8)
    _finalizar(figura, caminho)


def grafico_posicoes(matriz: pd.DataFrame, sexo: str, caminho: Path) -> None:
    figura, eixo = plt.subplots(figsize=(7.5, 0.32 * len(matriz) + 1.4))
    imagem = eixo.imshow(matriz.values, cmap="viridis_r", vmin=1, vmax=20, aspect="auto")
    for i, linha in enumerate(matriz.to_numpy()):
        for j, valor in enumerate(linha):
            if pd.notna(valor):
                # Posições altas ficam claras (amarelo) no mapa de cores: texto escuro nelas.
                cor = "black" if valor < 9 else "white"
                eixo.text(j, i, f"{valor:.0f}", ha="center", va="center", fontsize=7, color=cor)
    eixo.set_xticks(range(len(matriz.columns)), [rotulo_decada(d) for d in matriz.columns])
    eixo.set_yticks(range(len(matriz.index)), matriz.index)
    eixo.grid(False)
    eixo.set_title(f"Posição no ranking ({sexo}): nomes que chegaram ao top 10")
    barra = figura.colorbar(imagem, ax=eixo, shrink=0.6, ticks=[1, 5, 10, 15, 20])
    barra.set_label("posição (vazio = fora do top 20)")
    barra.ax.invert_yaxis()
    _finalizar(figura, caminho)
