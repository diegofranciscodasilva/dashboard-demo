"""Teste de fumaça: verifica páginas, APIs e CRUD. Execute: python test_smoke.py"""
import unittest
import uuid

from app import app

PAGINAS = ["/", "/operacional", "/analitico", "/executivo",
           "/administrativo", "/cientifico", "/embutido", "/widget/vendas"]
APIS = ["/api/operacional", "/api/analitico", "/api/analitico?regiao=Sul",
        "/api/executivo", "/api/usuarios", "/api/cientifico?janela=15"]


class TesteDashboards(unittest.TestCase):
    def setUp(self):
        self.c = app.test_client()

    def test_paginas(self):
        for rota in PAGINAS:
            self.assertEqual(self.c.get(rota).status_code, 200, rota)

    def test_apis(self):
        for rota in APIS:
            r = self.c.get(rota)
            self.assertEqual(r.status_code, 200, rota)
            self.assertTrue(r.is_json, rota)

    def test_404(self):
        self.assertEqual(self.c.get("/nao-existe").status_code, 404)
        self.assertEqual(self.c.get("/api/nada").status_code, 404)

    def test_janela_invalida_nao_quebra(self):
        self.assertEqual(self.c.get("/api/cientifico?janela=abc").status_code, 200)
        self.assertEqual(self.c.get("/api/cientifico?janela=9999").status_code, 200)

    def test_anomalias_injetadas(self):
        d = self.c.get("/api/cientifico").get_json()
        self.assertTrue({60, 140, 200} <= set(d["anomalias"]))

    def test_crud_completo(self):
        email = f"{uuid.uuid4().hex[:8]}@teste.com"
        dados = {"nome": "Teste", "email": email, "perfil": "Leitor"}

        r = self.c.post("/api/usuarios", json=dados)
        self.assertEqual(r.status_code, 201)
        uid = r.get_json()["id"]

        self.assertEqual(self.c.post("/api/usuarios", json=dados).status_code, 409)       # duplicado
        self.assertEqual(self.c.post("/api/usuarios", json={"nome": ""}).status_code, 400)  # inválido
        self.assertEqual(self.c.patch(f"/api/usuarios/{uid}").status_code, 200)
        self.assertEqual(self.c.delete(f"/api/usuarios/{uid}").status_code, 200)
        self.assertEqual(self.c.delete(f"/api/usuarios/{uid}").status_code, 404)           # já removido


if __name__ == "__main__":
    unittest.main(verbosity=2)
    