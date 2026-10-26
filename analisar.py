"""Roda a análise completa a partir de dados/*.csv.

Uso: python analisar.py

Gera os gráficos em graficos/ e as tabelas em RESULTADOS.md.
Para baixar os dados de novo do IBGE: python -m nomes.coleta
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from nomes import graficos
from nomes.transformar import concentracao, crescimento, mais_comuns, nome_proprio, novatos, picos, posicoes

RAIZ = Path(__file__).resolve().parent


def tabela_md(df: pd.DataFrame) -> str:
    cabecalho = "| " + " | ".join(map(str, df.columns)) + " |"
    separador = "|" + "---|" * len(df.columns)
    linhas = ["| " + " | ".join(map(str, linha)) + " |" for linha in df.itertuples(index=False)]
    return "\n".join([cabecalho, separador, *linhas])


def main() -> None:
    ranking = pd.read_csv(RAIZ / "dados" / "ranking.csv")
    series = pd.read_csv(RAIZ / "dados" / "series.csv")
    pasta = RAIZ / "graficos"
    pasta.mkdir(exist_ok=True)

    ultima = int(ranking["decada"].max())
    conc = concentracao(ranking)
    quedas = picos(series).sort_values("variacao_desde_pico")
    subidas = crescimento(series, 1980, ultima)

    graficos.grafico_concentracao(conc, pasta / "concentracao.png")
    graficos.grafico_curvas(
        series,
        {
            "Maiores quedas desde o auge": list(zip(quedas["nome"][:4], quedas["sexo"][:4], strict=True)),
            f"Maiores altas (1980s → {ultima}s)": list(zip(subidas["nome"][:4], subidas["sexo"][:4], strict=True)),
        },
        pasta / "ascensao-e-queda.png",
    )
    for sexo in ("feminino", "masculino"):
        graficos.grafico_posicoes(posicoes(ranking, sexo), sexo, pasta / f"posicoes-{sexo}.png")

    topo = mais_comuns(ranking).reset_index()
    topo["decada"] = topo["decada"].astype(str) + "s"
    conc_largo = conc.pivot(index="decada", columns="sexo", values="participacao_lider").reset_index()
    conc_largo["decada"] = conc_largo["decada"].astype(str) + "s"
    estreantes = novatos(ranking, ultima).assign(nome=lambda d: d["nome"].map(nome_proprio))
    fmt_quedas = quedas.head(10).assign(nome=lambda d: d["nome"].map(nome_proprio))
    fmt_subidas = subidas.head(10).assign(nome=lambda d: d["nome"].map(nome_proprio))

    partes = [
        "# Resultados",
        "",
        "Gerado automaticamente por `python analisar.py`. Não edite à mão.",
        "",
        "## Os 5 nomes mais comuns por década",
        tabela_md(topo.rename(columns={"decada": "Década", "feminino": "Feminino", "masculino": "Masculino"})),
        "",
        "## Participação do 1º lugar dentro do top 20 (%)",
        tabela_md(conc_largo.rename(columns={"decada": "Década", "feminino": "Feminino", "masculino": "Masculino"})),
        "",
        f"## Estreantes no top 20 dos anos {ultima}",
        tabela_md(estreantes[["sexo", "posicao", "nome"]].rename(columns=str.capitalize)),
        "",
        "## Maiores quedas desde o auge",
        tabela_md(
            fmt_quedas[["nome", "sexo", "decada_pico", "frequencia_pico", "frequencia_ultima", "variacao_desde_pico"]]
        ),
        "",
        f"## Maiores altas entre os anos 1980 e {ultima}",
        tabela_md(fmt_subidas[["nome", "sexo", "de", "ate", "variacao"]].astype({"de": int, "ate": int})),
        "",
    ]
    (RAIZ / "RESULTADOS.md").write_text("\n".join(partes), encoding="utf-8")
    print(f"Pronto: {len(list(pasta.glob('*.png')))} gráficos em graficos/ e tabelas em RESULTADOS.md")


if __name__ == "__main__":
    main()
