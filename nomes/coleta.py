"""Baixa os dados de nomes do Censo 2010 pela API pública do IBGE e salva em CSV.

Uso: python -m nomes.coleta

Gera:
- dados/ranking.csv  os 20 nomes mais registrados em cada década, por sexo
- dados/series.csv   quantas pessoas de cada um desses nomes nasceram em cada década

As respostas da API ficam guardadas em dados/brutos/ para não baixar de novo.
"""

from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd

from .transformar import ler_periodo

API = "https://servicodados.ibge.gov.br/api/v2/censos/nomes"
DECADAS = list(range(1930, 2010, 10))  # a API usa o ano inicial: 1930 = [1930, 1940)
SEXOS = {"F": "feminino", "M": "masculino"}
PASTA = Path(__file__).resolve().parent.parent / "dados"


def baixar_json(url: str, tentativas: int = 4) -> list:
    cache = PASTA / "brutos" / (urllib.parse.quote(url.removeprefix(API), safe="") + ".json")
    if cache.exists():
        return json.loads(cache.read_text(encoding="utf-8"))

    for tentativa in range(1, tentativas + 1):
        try:
            with urllib.request.urlopen(url, timeout=30) as resposta:
                dados = json.load(resposta)
            break
        except OSError:
            if tentativa == tentativas:
                raise
            time.sleep(2**tentativa)  # espera cada vez mais antes de tentar de novo

    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(dados, ensure_ascii=False), encoding="utf-8")
    return dados


def coletar_ranking() -> pd.DataFrame:
    linhas = []
    for decada in DECADAS:
        for sigla, sexo in SEXOS.items():
            resposta = baixar_json(f"{API}/ranking?decada={decada}&sexo={sigla}")
            for item in resposta[0]["res"]:
                linhas.append(
                    {
                        "decada": decada,
                        "sexo": sexo,
                        "posicao": item["ranking"],
                        "nome": item["nome"],
                        "frequencia": item["frequencia"],
                    }
                )
    return pd.DataFrame(linhas)


def coletar_series(ranking: pd.DataFrame) -> pd.DataFrame:
    linhas = []
    for sexo, grupo in ranking.groupby("sexo"):
        sigla = next(s for s, nome in SEXOS.items() if nome == sexo)
        nomes = sorted(grupo["nome"].unique())
        # A API aceita vários nomes de uma vez separados por "|"; 10 por pedido é seguro.
        for inicio in range(0, len(nomes), 10):
            lote = "|".join(nomes[inicio : inicio + 10])
            for registro in baixar_json(f"{API}/{urllib.parse.quote(lote)}?sexo={sigla}"):
                for ponto in registro["res"]:
                    decada = ler_periodo(ponto["periodo"])
                    if decada is not None:
                        linhas.append(
                            {
                                "nome": registro["nome"],
                                "sexo": sexo,
                                "decada": decada,
                                "frequencia": ponto["frequencia"],
                            }
                        )
    return pd.DataFrame(linhas).sort_values(["sexo", "nome", "decada"], ignore_index=True)


def main() -> None:
    PASTA.mkdir(exist_ok=True)
    ranking = coletar_ranking()
    ranking.to_csv(PASTA / "ranking.csv", index=False)
    series = coletar_series(ranking)
    series.to_csv(PASTA / "series.csv", index=False)
    print(f"ranking.csv: {len(ranking)} linhas · series.csv: {len(series)} linhas")


if __name__ == "__main__":
    main()
