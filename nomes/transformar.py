"""Transformações e métricas sobre os dados de nomes. Funções puras, testadas em tests/."""

from __future__ import annotations

import re

import pandas as pd


def ler_periodo(periodo: str) -> int | None:
    """Converte o período da API na década inicial: "[1950,1960[" -> 1950.

    O IBGE agrupa quem nasceu antes de 1930 como "1930[": esse grupo mistura
    várias décadas, então é deixado de fora (None).
    """
    achado = re.fullmatch(r"\[(\d{4}),(\d{4})\[", periodo.strip())
    return int(achado.group(1)) if achado else None


def rotulo_decada(decada: int) -> str:
    return f"{decada}s"


def nome_proprio(nome: str) -> str:
    """O IBGE devolve "MARIA" e "JOAO", sem acento; aqui fica "Maria" e "Joao"."""
    return nome.title()


def mais_comuns(ranking: pd.DataFrame, n: int = 5) -> pd.DataFrame:
    """Tabela com os n primeiros nomes de cada década (linhas) e sexo (colunas)."""
    topo = ranking[ranking["posicao"] <= n].sort_values(["decada", "sexo", "posicao"])
    return (
        topo.assign(nome=topo["nome"].map(nome_proprio))
        .groupby(["decada", "sexo"])["nome"]
        .agg(", ".join)
        .unstack("sexo")
    )


def concentracao(ranking: pd.DataFrame) -> pd.DataFrame:
    """Quanto o primeiro colocado representa dentro do top 20, por década e sexo (em %).

    Quanto maior, mais as famílias escolhiam o mesmo nome.
    """
    agrupado = ranking.groupby(["decada", "sexo"])
    lider = ranking[ranking["posicao"] == 1].set_index(["decada", "sexo"])
    tabela = pd.DataFrame(
        {
            "lider": lider["nome"].map(nome_proprio),
            "participacao_lider": lider["frequencia"] / agrupado["frequencia"].sum() * 100,
        }
    )
    return tabela.round({"participacao_lider": 1}).reset_index()


def novatos(ranking: pd.DataFrame, decada: int) -> pd.DataFrame:
    """Nomes que estão no top 20 da década informada e nunca tinham aparecido antes."""
    anteriores = ranking.loc[ranking["decada"] < decada, ["nome", "sexo"]].drop_duplicates()
    atual = ranking[ranking["decada"] == decada]
    marcado = atual.merge(anteriores, on=["nome", "sexo"], how="left", indicator=True)
    return (
        marcado[marcado["_merge"] == "left_only"]
        .drop(columns="_merge")
        .sort_values(["sexo", "posicao"], ignore_index=True)
    )


def picos(series: pd.DataFrame) -> pd.DataFrame:
    """Para cada nome: a década em que mais foi registrado e quanto caiu ou subiu desde então."""
    indice_pico = series.groupby(["nome", "sexo"])["frequencia"].idxmax()
    pico = series.loc[indice_pico, ["nome", "sexo", "decada", "frequencia"]]
    ultima = series[series["decada"] == series["decada"].max()][["nome", "sexo", "frequencia"]]
    tabela = pico.merge(ultima, on=["nome", "sexo"], suffixes=("_pico", "_ultima"))
    tabela["variacao_desde_pico"] = (tabela["frequencia_ultima"] / tabela["frequencia_pico"] - 1) * 100
    return tabela.rename(columns={"decada": "decada_pico"}).round({"variacao_desde_pico": 1}).reset_index(drop=True)


def crescimento(series: pd.DataFrame, de: int, ate: int) -> pd.DataFrame:
    """Variação percentual de cada nome entre duas décadas, do maior crescimento para a maior queda."""
    largo = series.pivot_table(index=["nome", "sexo"], columns="decada", values="frequencia")
    tabela = pd.DataFrame({"de": largo[de], "ate": largo[ate]}).dropna()
    tabela = tabela[tabela["de"] > 0]
    tabela["variacao"] = ((tabela["ate"] / tabela["de"] - 1) * 100).round(1)
    return tabela.sort_values("variacao", ascending=False).reset_index()


def posicoes(ranking: pd.DataFrame, sexo: str, top: int = 10) -> pd.DataFrame:
    """Matriz nome x década com a posição no ranking, para nomes que já estiveram no top `top`."""
    do_sexo = ranking[ranking["sexo"] == sexo]
    escolhidos = do_sexo.loc[do_sexo["posicao"] <= top, "nome"].unique()
    matriz = do_sexo[do_sexo["nome"].isin(escolhidos)].pivot_table(index="nome", columns="decada", values="posicao")
    # Ordena pela década em que o nome teve a melhor posição (os mais antigos em cima)
    # e, no empate, pela melhor posição alcançada.
    chave = pd.DataFrame({"decada": matriz.idxmin(axis=1), "melhor": matriz.min(axis=1)})
    matriz = matriz.loc[chave.sort_values(["decada", "melhor"]).index]
    matriz.index = matriz.index.map(nome_proprio)
    return matriz
