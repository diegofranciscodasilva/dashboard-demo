# Dashboards Demo

Seis dashboards (operacional, analítico, executivo, administrativo, científico e embutido)
com Flask, SQLite, NumPy e Chart.js.

## Rodar localmente

1. `python -m venv .venv` e ative o ambiente
2. `pip install -r requirements.txt`
3. `python baixar_chartjs.py` (uma vez, com internet)
4. `python app.py` e abra http://127.0.0.1:5000

## Testes

`python test_smoke.py`

## Deploy

Repositório no GitHub + importação na Vercel (preset "Other").
