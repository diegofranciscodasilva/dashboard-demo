# Dashboards Demo

Demonstração de seis tipos de dashboards construída com Flask, SQLite, NumPy e Chart.js. O projeto reúne visualização de dados, métricas do sistema, filtros, CRUD, análise científica e incorporação por iframe em uma aplicação responsiva.

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.0%2B-000000?logo=flask)
![SQLite](https://img.shields.io/badge/SQLite-3-003B57?logo=sqlite&logoColor=white)
![Chart.js](https://img.shields.io/badge/Chart.js-4.4-FF6384?logo=chartdotjs&logoColor=white)
![Vercel](https://img.shields.io/badge/Vercel-Serverless-000000?logo=vercel)

## Dashboards disponíveis

| Dashboard      | Rota              | Recursos                                                              |
| -------------- | ----------------- | --------------------------------------------------------------------- |
| Operacional    | `/operacional`    | CPU, memória e disco; chamados por status e chamados recentes         |
| Analítico      | `/analitico`      | Filtros por região e categoria; vendas mensais, categorias e produtos |
| Executivo      | `/executivo`      | Receita, pedidos, ticket médio, meta e comparação mensal              |
| Administrativo | `/administrativo` | CRUD de usuários em uma interface administrativa                      |
| Científico     | `/cientifico`     | Média móvel, regressão linear, estatísticas e detecção de anomalias   |
| Embutido       | `/embutido`       | Widget em claro ou escuro e código pronto para iframe                 |

O projeto também disponibiliza o widget em `/widget/vendas?tema=light` ou `/widget/vendas?tema=dark`.

## Tecnologias

- **Backend:** Flask
- **Dados:** SQLite
- **Análise:** NumPy
- **Gráficos:** Chart.js
- **Métricas locais:** psutil
- **Frontend:** HTML, CSS e JavaScript
- **Hospedagem:** Vercel (entrada serverless)

## Começando

### Pré-requisitos

- Python 3.10 ou superior
- pip

### Instalação no Windows

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### Instalação no Linux ou macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### Executar

```bash
python app.py
```

Acesse [http://127.0.0.1:5000](http://127.0.0.1:5000).

Na primeira execução, o banco `dados.db` é criado automaticamente com dados fictícios determinísticos.

## Banco de dados

O arquivo `dados.db` contém dados de demonstração nas seguintes tabelas:

- `vendas`: data, produto, categoria, região, quantidade e valor
- `chamados`: título, status e prioridade
- `usuarios`: nome, e-mail, perfil e situação
- `medicoes`: timestamp e temperatura

Para recriar o banco manualmente:

```bash
python seed.py
```

Esse comando substitui os dados atuais por dados fictícios previstos pelo gerador.

## APIs

| Método   | Rota                              | Descrição                                           |
| -------- | --------------------------------- | --------------------------------------------------- |
| `GET`    | `/api/operacional`                | Métricas do sistema e chamados                      |
| `GET`    | `/api/analitico`                  | Vendas com filtros opcionais `regiao` e `categoria` |
| `GET`    | `/api/executivo`                  | Indicadores executivos e tendência mensal           |
| `GET`    | `/api/usuarios`                   | Lista usuários                                      |
| `POST`   | `/api/usuarios`                   | Cria um usuário                                     |
| `PATCH`  | `/api/usuarios/<id>`              | Alterna ativo/inativo                               |
| `DELETE` | `/api/usuarios/<id>`              | Remove um usuário                                   |
| `GET`    | `/api/cientifico?janela=<numero>` | Série, média móvel, tendência e anomalias           |

Exemplo de criação de usuário:

```bash
curl -X POST http://127.0.0.1:5000/api/usuarios \
  -H "Content-Type: application/json" \
  -d "{\"nome\":\"Maria Silva\",\"email\":\"maria@exemplo.com\",\"perfil\":\"Leitor\"}"
```

Perfis válidos: `Administrador`, `Editor` e `Leitor`.

## Chart.js

Uma cópia local de Chart.js já pode ser usada pela aplicação em `static/vendor/chart.umd.js`. Caso o arquivo não exista ou precise ser atualizado:

```bash
python baixar_chartjs.py
```

O comando exige conexão com a internet. Os templates também possuem uma alternativa via CDN.

## Testes

Os testes de fumaça verificam páginas, APIs, respostas 404, parâmetros inválidos, detecção de anomalias e o fluxo completo de CRUD:

```bash
python test_smoke.py
```

## Implantação na Vercel

O projeto já inclui `vercel.json` e `api/index.py` para execução serverless.

1. Importe o repositório na Vercel.
2. Selecione o preset **Other**.
3. Implante sem configurar comandos adicionais de build.

Na nuvem:

- o banco SQLite é criado em `/tmp/dados.db`;
- os dados podem ser perdidos quando a instância serverless é reiniciada ou substituída;
- as métricas de CPU, memória e disco são simuladas;
- o CRUD público é limitado a 50 usuários.

Para uma implantação com dados persistentes, configure um banco externo e adapte o módulo de acesso em `app.py`.

## Estrutura principal

```text
dashboards-demo/
├── app.py                 # Aplicação Flask, páginas e APIs
├── seed.py                # Criação e reinicialização do banco SQLite
├── dados.db               # Banco local de demonstração
├── api/index.py           # Entrada serverless da Vercel
├── templates/             # Páginas HTML
├── static/
│   ├── css/               # Estilos e temas
│   ├── js/                # Consumo das APIs e gráficos
│   └── vendor/            # Dependências locais
├── test_smoke.py          # Testes de fumaça
├── requirements.txt       # Dependências Python
└── vercel.json            # Configuração de implantação
```

## Observações

Este projeto é uma demonstração. O CRUD não possui autenticação ou autorização e o SQLite em `/tmp` não oferece persistência confiável na Vercel. Para uso em produção, adicione autenticação, controle de acesso, migrações e um banco persistente.

## 👨‍💻 Autor

### Diego Francisco da Silva

Desenvolvedor Front-End em formação e estudante de Engenharia de Software.

- **[Site Empresa](https://diegofranciscodasilva.github.io/dev-software-web/)**: dev.software.web
- **[LinkedIn](https://www.linkedin.com/in/diego-francisco-da-silva/)**: diego-francisco-da-silva
- **[GitHub](https://github.com/diegofranciscodasilva)**: diegofranciscodasilva
- **[Instagram](https://www.instagram.com/diego_francisco_da_silva/)**: @diego_francisco_da_silva
- **[Instagram](https://www.instagram.com/dev.software.web/)**: @dev.software.web

---

Feito com ❤️ por Diego.
