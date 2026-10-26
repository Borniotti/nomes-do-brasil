import pandas as pd
import pytest

from nomes.transformar import (
    concentracao,
    crescimento,
    ler_periodo,
    mais_comuns,
    nome_proprio,
    novatos,
    picos,
    posicoes,
)


@pytest.mark.parametrize(
    ("periodo", "esperado"),
    [("[1950,1960[", 1950), ("[2000,2010[", 2000), ("1930[", None), ("qualquer", None)],
)
def test_ler_periodo(periodo, esperado):
    assert ler_periodo(periodo) == esperado


def test_nome_proprio():
    assert nome_proprio("MARIA EDUARDA") == "Maria Eduarda"


@pytest.fixture
def ranking():
    linhas = [
        (1950, "feminino", 1, "MARIA", 600),
        (1950, "feminino", 2, "ANA", 300),
        (1950, "feminino", 3, "VERA", 100),
        (1950, "masculino", 1, "JOSE", 500),
        (1950, "masculino", 2, "JOAO", 500),
        (2000, "feminino", 1, "MARIA", 200),
        (2000, "feminino", 2, "JULIA", 150),
        (2000, "feminino", 3, "ANA", 150),
        (2000, "masculino", 1, "LUCAS", 400),
        (2000, "masculino", 2, "JOSE", 100),
    ]
    return pd.DataFrame(linhas, columns=["decada", "sexo", "posicao", "nome", "frequencia"])


@pytest.fixture
def series():
    linhas = [
        ("VERA", "feminino", 1950, 100),
        ("VERA", "feminino", 1960, 300),
        ("VERA", "feminino", 2000, 30),
        ("JULIA", "feminino", 1950, 10),
        ("JULIA", "feminino", 1960, 20),
        ("JULIA", "feminino", 2000, 150),
    ]
    return pd.DataFrame(linhas, columns=["nome", "sexo", "decada", "frequencia"])


def test_mais_comuns(ranking):
    tabela = mais_comuns(ranking, n=2)
    assert tabela.loc[1950, "feminino"] == "Maria, Ana"
    assert tabela.loc[2000, "masculino"] == "Lucas, Jose"


def test_concentracao(ranking):
    tabela = concentracao(ranking).set_index(["decada", "sexo"])
    assert tabela.loc[(1950, "feminino"), "participacao_lider"] == 60.0
    assert tabela.loc[(2000, "feminino"), "participacao_lider"] == 40.0
    assert tabela.loc[(2000, "masculino"), "lider"] == "Lucas"


def test_novatos_ignoram_quem_ja_apareceu(ranking):
    estreantes = novatos(ranking, 2000)
    assert list(zip(estreantes["sexo"], estreantes["nome"], strict=True)) == [
        ("feminino", "JULIA"),
        ("masculino", "LUCAS"),
    ]


def test_novato_e_por_sexo(ranking):
    ranking.loc[len(ranking)] = [2000, "masculino", 3, "ANA", 50]  # já existia, mas no feminino
    assert "ANA" in set(novatos(ranking, 2000)["nome"])


def test_picos(series):
    tabela = picos(series).set_index("nome")
    assert tabela.loc["VERA", "decada_pico"] == 1960
    assert tabela.loc["VERA", "variacao_desde_pico"] == -90.0
    assert tabela.loc["JULIA", "decada_pico"] == 2000
    assert tabela.loc["JULIA", "variacao_desde_pico"] == 0.0


def test_crescimento_ordena_do_maior_para_o_menor(series):
    tabela = crescimento(series, 1950, 2000)
    assert list(tabela["nome"]) == ["JULIA", "VERA"]
    assert list(tabela["variacao"]) == [1400.0, -70.0]


def test_posicoes(ranking):
    matriz = posicoes(ranking, "feminino", top=2)
    assert list(matriz.index) == ["Maria", "Ana", "Julia"]
    assert matriz.loc["Julia", 2000] == 2
    assert pd.isna(matriz.loc["Julia", 1950])


def test_dados_reais_tem_formato_esperado():
    """Garante que os CSVs versionados continuam no formato que a análise espera."""
    ranking = pd.read_csv("dados/ranking.csv")
    series = pd.read_csv("dados/series.csv")
    assert set(ranking.columns) == {"decada", "sexo", "posicao", "nome", "frequencia"}
    assert ranking.groupby(["decada", "sexo"]).size().eq(20).all()
    assert (series["frequencia"] > 0).all()
    assert set(series["decada"]) == set(ranking["decada"])
