"""Cria o banco SQLite com dados fictícios.
Uso manual (recria e reinicia os dados): python seed.py
O app.py também chama criar_banco() automaticamente se o banco não existir.
"""
import math
import random
import sqlite3
from contextlib import closing
from datetime import datetime, timedelta
from pathlib import Path

SCHEMA = """
DROP TABLE IF EXISTS vendas;
DROP TABLE IF EXISTS chamados;
DROP TABLE IF EXISTS usuarios;
DROP TABLE IF EXISTS medicoes;

CREATE TABLE vendas (
    id INTEGER PRIMARY KEY, data TEXT, produto TEXT, categoria TEXT,
    regiao TEXT, quantidade INTEGER, valor REAL
);
CREATE INDEX idx_vendas_data ON vendas (data);
CREATE TABLE chamados (
    id INTEGER PRIMARY KEY, titulo TEXT, status TEXT, prioridade TEXT
);
CREATE TABLE usuarios (
    id INTEGER PRIMARY KEY, nome TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE, perfil TEXT NOT NULL, ativo INTEGER DEFAULT 1
);
CREATE TABLE medicoes (
    id INTEGER PRIMARY KEY, ts TEXT, temperatura REAL
);
"""

PRODUTOS = {
    "Notebook": ("Eletrônicos", 3500), "Smartphone": ("Eletrônicos", 2000),
    "Fone": ("Acessórios", 250), "Mouse": ("Acessórios", 90),
    "Cadeira": ("Móveis", 900), "Mesa": ("Móveis", 700),
}
REGIOES = ["Sul", "Sudeste", "Nordeste", "Centro-Oeste", "Norte"]
INDICES_ANOMALIA = (60, 140, 200)  # leituras com picos injetados


def criar_banco(caminho) -> None:
    """Cria (ou recria) o banco no caminho informado."""
    rng = random.Random(42)  # mesma sequência a cada execução
    hoje = datetime.now()
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)

    with closing(sqlite3.connect(caminho)) as conn:
        conn.executescript(SCHEMA)

        # ---- Vendas (365 dias) ----
        vendas = []
        for d in range(365):
            dia = (hoje - timedelta(days=d)).strftime("%Y-%m-%d")
            for _ in range(rng.randint(3, 7)):
                produto = rng.choice(list(PRODUTOS))
                categoria, preco = PRODUTOS[produto]
                qtd = rng.randint(1, 3)
                valor = round(preco * qtd * rng.uniform(0.9, 1.1), 2)
                vendas.append((dia, produto, categoria, rng.choice(REGIOES), qtd, valor))
        conn.executemany(
            "INSERT INTO vendas (data, produto, categoria, regiao, quantidade, valor) "
            "VALUES (?, ?, ?, ?, ?, ?)", vendas)

        # ---- Chamados ----
        problemas = ["de rede", "no sistema", "de acesso", "na impressora"]
        conn.executemany(
            "INSERT INTO chamados (titulo, status, prioridade) VALUES (?, ?, ?)",
            [(f"Chamado #{i}: problema {rng.choice(problemas)}",
              rng.choice(["Aberto", "Em andamento", "Resolvido"]),
              rng.choice(["Baixa", "Média", "Alta"])) for i in range(1, 41)])

        # ---- Usuários ----
        conn.executemany(
            "INSERT INTO usuarios (nome, email, perfil) VALUES (?, ?, ?)", [
                ("Ana Souza", "ana@exemplo.com", "Administrador"),
                ("Bruno Lima", "bruno@exemplo.com", "Editor"),
                ("Carla Dias", "carla@exemplo.com", "Leitor"),
                ("Diego Alves", "diego@exemplo.com", "Editor"),
            ])

        # ---- Medições (sensor a cada 5 min, com 3 anomalias) ----
        inicio = hoje - timedelta(minutes=5 * 240)
        medicoes = []
        for i in range(240):
            temp = 22 + 2.5 * math.sin(i / 25) + 0.01 * i + rng.gauss(0, 0.3)
            if i in INDICES_ANOMALIA:
                temp += rng.choice([-1, 1]) * 5
            ts = (inicio + timedelta(minutes=5 * i)).strftime("%d/%m %H:%M")
            medicoes.append((ts, round(temp, 2)))
        conn.executemany("INSERT INTO medicoes (ts, temperatura) VALUES (?, ?)", medicoes)

        conn.commit()


if __name__ == "__main__":
    destino = Path(__file__).resolve().with_name("dados.db")
    criar_banco(destino)
    print(f"Banco criado em {destino}")
    