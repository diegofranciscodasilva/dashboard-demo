"""Servidor Flask: páginas HTML e API JSON dos seis dashboards."""
import os
import random
import re
import shutil  # noqa: F401  (reservado para futuras rotinas de backup)
import sqlite3
from contextlib import closing
from pathlib import Path

import numpy as np
from flask import Flask, abort, jsonify, render_template, request

from seed import criar_banco

try:  # psutil é opcional: sem ele, as métricas são simuladas
    import psutil
except ImportError:
    psutil = None

# ---------------------------------------------------------------
# CONFIGURAÇÃO
# ---------------------------------------------------------------
BASE = Path(__file__).resolve().parent
app = Flask(__name__,
            template_folder=str(BASE / "templates"),
            static_folder=str(BASE / "static"))

EM_NUVEM = bool(os.environ.get("VERCEL"))
# Na Vercel só /tmp é gravável (e é descartado entre execuções)
DB = Path("/tmp/dados.db") if EM_NUVEM else BASE / "dados.db"

META_MENSAL = 400_000        # meta usada no dashboard executivo
LIMITE_USUARIOS = 50         # protege o CRUD em demonstração pública
JANELA_ANOMALIA = 11         # janela fixa usada na detecção de anomalias
LIMITE_Z = 3.0               # desvios-padrão do resíduo para marcar anomalia
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PERFIS = {"Administrador", "Editor", "Leitor"}
PAGINAS = {
    "operacional": "Operacional",
    "analitico": "Analítico",
    "executivo": "Executivo",
    "administrativo": "Administrativo",
    "cientifico": "Científico",
    "embutido": "Embutido",
}

# Cria o banco automaticamente se não existir (local ou nuvem)
if not DB.exists():
    criar_banco(DB)

if psutil:
    psutil.cpu_percent(interval=None)  # primeira leitura é sempre 0; "aquece"


# ---------------------------------------------------------------
# ACESSO AO BANCO
# ---------------------------------------------------------------
def conectar():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


def query(sql, params=(), one=False):
    """SELECT parametrizado. Retorna lista de dicts (ou um dict se one=True)."""
    with closing(conectar()) as conn:
        rows = [dict(r) for r in conn.execute(sql, params)]
    if one:
        return rows[0] if rows else None
    return rows


def execute(sql, params=()):
    """INSERT/UPDATE/DELETE parametrizado. Retorna (lastrowid, rowcount)."""
    with closing(conectar()) as conn:
        cur = conn.execute(sql, params)
        conn.commit()
        return cur.lastrowid, cur.rowcount


def inteiro(valor, padrao, minimo, maximo):
    """Converte para int com limites; valores inválidos usam o padrão."""
    try:
        n = int(valor)
    except (TypeError, ValueError):
        n = padrao
    return max(minimo, min(n, maximo))


# ---------------------------------------------------------------
# PÁGINAS
# ---------------------------------------------------------------
@app.get("/")
def index():
    return render_template("index.html", paginas=PAGINAS, pagina="")


@app.get("/widget/vendas")
def widget():
    tema = "dark" if request.args.get("tema") == "dark" else "light"
    return render_template("widget.html", tema=tema)


@app.get("/<nome>")
def dashboard(nome):
    if nome not in PAGINAS:
        abort(404)
    return render_template(f"{nome}.html", paginas=PAGINAS, pagina=nome)


@app.errorhandler(404)
def nao_encontrado(_erro):
    if request.path.startswith("/api/"):
        return jsonify(erro="Recurso não encontrado"), 404
    return render_template("404.html", paginas=PAGINAS, pagina=""), 404


@app.after_request
def cabecalhos(resp):
    resp.headers["X-Content-Type-Options"] = "nosniff"
    if request.path.startswith("/api/"):
        resp.headers["Cache-Control"] = "no-store"
    return resp


# ---------------------------------------------------------------
# 1) OPERACIONAL
# ---------------------------------------------------------------
def metricas_sistema():
    """Métricas reais no computador local; simuladas na nuvem."""
    if psutil and not EM_NUVEM:
        return {
            "cpu": psutil.cpu_percent(interval=None),
            "memoria": psutil.virtual_memory().percent,
            "disco": psutil.disk_usage(os.path.abspath(os.sep)).percent,
            "simulado": False,
        }
    return {
        "cpu": round(random.uniform(15, 70), 1),
        "memoria": round(random.uniform(40, 75), 1),
        "disco": round(random.uniform(45, 60), 1),
        "simulado": True,
    }


@app.get("/api/operacional")
def api_operacional():
    return jsonify(
        metricas=metricas_sistema(),
        status=query("SELECT status, COUNT(*) AS total FROM chamados GROUP BY status ORDER BY status"),
        recentes=query("SELECT id, titulo, status, prioridade FROM chamados ORDER BY id DESC LIMIT 8"),
    )


# ---------------------------------------------------------------
# 2) ANALÍTICO
# ---------------------------------------------------------------
@app.get("/api/analitico")
def api_analitico():
    regiao = request.args.get("regiao", "")
    categoria = request.args.get("categoria", "")

    where, params = "WHERE 1=1", []
    if regiao:
        where += " AND regiao = ?"
        params.append(regiao)
    if categoria:
        where += " AND categoria = ?"
        params.append(categoria)

    return jsonify(
        mensal=query(f"SELECT substr(data,1,7) AS mes, ROUND(SUM(valor),2) AS total "
                     f"FROM vendas {where} GROUP BY mes ORDER BY mes", params),
        por_categoria=query(f"SELECT categoria, ROUND(SUM(valor),2) AS total "
                            f"FROM vendas {where} GROUP BY categoria ORDER BY categoria", params),
        top=query(f"SELECT produto, SUM(quantidade) AS qtd, ROUND(SUM(valor),2) AS total "
                  f"FROM vendas {where} GROUP BY produto ORDER BY total DESC LIMIT 10", params),
        filtros={
            "regioes": [r["regiao"] for r in query("SELECT DISTINCT regiao FROM vendas ORDER BY 1")],
            "categorias": [r["categoria"] for r in query("SELECT DISTINCT categoria FROM vendas ORDER BY 1")],
        },
    )


# ---------------------------------------------------------------
# 3) EXECUTIVO
# ---------------------------------------------------------------
@app.get("/api/executivo")
def api_executivo():
    atual = query("SELECT COALESCE(SUM(valor),0) AS receita, COUNT(*) AS pedidos FROM vendas "
                  "WHERE data > date('now','-30 day')", one=True)
    anterior = query("SELECT COALESCE(SUM(valor),0) AS receita FROM vendas "
                     "WHERE data > date('now','-60 day') AND data <= date('now','-30 day')", one=True)
    receita, pedidos = atual["receita"], atual["pedidos"]
    variacao = (receita / anterior["receita"] - 1) * 100 if anterior["receita"] else 0
    return jsonify(
        receita=round(receita, 2),
        pedidos=pedidos,
        ticket_medio=round(receita / pedidos, 2) if pedidos else 0,
        variacao=round(variacao, 1),
        meta=META_MENSAL,
        atingimento=round(receita / META_MENSAL * 100, 1),
        tendencia=query("SELECT substr(data,1,7) AS mes, ROUND(SUM(valor),2) AS total "
                        "FROM vendas GROUP BY mes ORDER BY mes"),
    )


# ---------------------------------------------------------------
# 4) ADMINISTRATIVO (CRUD)
# ---------------------------------------------------------------
@app.get("/api/usuarios")
def listar_usuarios():
    return jsonify(query("SELECT * FROM usuarios ORDER BY id DESC"))


@app.post("/api/usuarios")
def criar_usuario():
    d = request.get_json(silent=True) or {}
    nome = str(d.get("nome", "")).strip()
    email = str(d.get("email", "")).strip().lower()
    perfil = d.get("perfil", "")

    if not (1 <= len(nome) <= 80) or not EMAIL_RE.match(email) or len(email) > 120 or perfil not in PERFIS:
        return jsonify(erro="Dados inválidos. Verifique nome, e-mail e perfil."), 400
    if query("SELECT COUNT(*) AS n FROM usuarios", one=True)["n"] >= LIMITE_USUARIOS:
        return jsonify(erro=f"Limite de {LIMITE_USUARIOS} usuários atingido (modo demonstração)."), 403
    try:
        uid, _ = execute("INSERT INTO usuarios (nome, email, perfil) VALUES (?, ?, ?)",
                         (nome, email, perfil))
    except sqlite3.IntegrityError:
        return jsonify(erro="E-mail já cadastrado."), 409
    return jsonify(id=uid), 201


@app.patch("/api/usuarios/<int:uid>")
def alternar_usuario(uid):
    _, alterados = execute("UPDATE usuarios SET ativo = 1 - ativo WHERE id = ?", (uid,))
    if not alterados:
        return jsonify(erro="Usuário não encontrado."), 404
    return jsonify(ok=True)


@app.delete("/api/usuarios/<int:uid>")
def remover_usuario(uid):
    _, removidos = execute("DELETE FROM usuarios WHERE id = ?", (uid,))
    if not removidos:
        return jsonify(erro="Usuário não encontrado."), 404
    return jsonify(ok=True)


# ---------------------------------------------------------------
# 5) CIENTÍFICO
# ---------------------------------------------------------------
@app.get("/api/cientifico")
def api_cientifico():
    rows = query("SELECT ts, temperatura FROM medicoes ORDER BY id")
    if not rows:
        return jsonify(labels=[], valores=[], media_movel=[], tendencia=[], anomalias=[],
                       janela=0, stats={"media": 0, "desvio": 0, "minimo": 0, "maximo": 0, "inclinacao": 0})

    y = np.array([r["temperatura"] for r in rows], dtype=float)
    x = np.arange(len(y))
    janela = inteiro(request.args.get("janela"), 10, 2, min(50, len(y)))

    # Média móvel (à direita): primeiros pontos ficam sem valor
    media = np.convolve(y, np.ones(janela) / janela, mode="valid")
    media_movel = [None] * (janela - 1) + [round(float(v), 2) for v in media]

    # Regressão linear (tendência)
    a, b = np.polyfit(x, y, 1)
    tendencia = [round(float(a * i + b), 2) for i in x]

    # Anomalias: z-score do RESÍDUO em relação a uma média móvel centrada.
    # (Usar z-score da série bruta marcaria pontos normais, pois há tendência e sazonalidade.)
    w = min(JANELA_ANOMALIA, len(y))
    preenchido = np.pad(y, (w // 2, w - 1 - w // 2), mode="edge")
    suave = np.convolve(preenchido, np.ones(w) / w, mode="valid")
    residuo = y - suave
    desvio_res = residuo.std()
    z = residuo / desvio_res if desvio_res > 0 else np.zeros_like(residuo)
    anomalias = [int(i) for i in np.where(np.abs(z) > LIMITE_Z)[0]]

    return jsonify(
        labels=[r["ts"] for r in rows],
        valores=y.tolist(),
        media_movel=media_movel,
        tendencia=tendencia,
        anomalias=anomalias,
        janela=janela,
        stats={
            "media": round(float(y.mean()), 2), "desvio": round(float(y.std()), 2),
            "minimo": round(float(y.min()), 2), "maximo": round(float(y.max()), 2),
            "inclinacao": round(float(a), 4),
        },
    )


if __name__ == "__main__":
    # Só executa localmente; a Vercel importa o objeto `app` diretamente
    app.run(host="127.0.0.1", port=5000, debug=True)
    