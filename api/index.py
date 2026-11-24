"""Entrada serverless da Vercel: expõe o objeto `app` do Flask."""
import sys
from pathlib import Path

# Garante que o app.py (raiz do projeto) seja encontrado
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import app  # noqa: E402,F401
