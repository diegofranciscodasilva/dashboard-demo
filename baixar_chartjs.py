"""Baixa o Chart.js para static/vendor (permite rodar sem internet).
Execute uma vez, com internet: python baixar_chartjs.py
"""
from pathlib import Path
from urllib.request import urlopen

URL = "https://cdn.jsdelivr.net/npm/chart.js@4.4.7/dist/chart.umd.js"
DESTINO = Path(__file__).resolve().parent / "static" / "vendor" / "chart.umd.js"

DESTINO.parent.mkdir(parents=True, exist_ok=True)
with urlopen(URL, timeout=30) as resposta:
    DESTINO.write_bytes(resposta.read())
print(f"Chart.js salvo em {DESTINO}")
