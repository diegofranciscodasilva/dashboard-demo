"use strict";

/* =========================================================
   UTILIDADES COMUNS
   ========================================================= */
const $ = (s, el = document) => el.querySelector(s);
const brl = (v) => Number(v).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
const css = (v) => getComputedStyle(document.documentElement).getPropertyValue(v).trim();
const PALETA = ["#2563eb", "#f59e0b", "#16a34a", "#8b5cf6", "#ef4444"];

// Escapa texto antes de inserir via innerHTML (evita XSS)
const esc = (t) => { const d = document.createElement("div"); d.textContent = t ?? ""; return d.innerHTML; };

// Mostra um aviso de erro no topo da página por alguns segundos
function mostrarErro(msg) {
    const el = $("#erro-global");
    if (!el) return console.error(msg);
    el.textContent = msg;
    el.hidden = false;
    clearTimeout(mostrarErro.timer);
    mostrarErro.timer = setTimeout(() => (el.hidden = true), 6000);
}

// fetch com tratamento de erro; usa a mensagem "erro" devolvida pela API
async function api(url, opts) {
    let r;
    try { r = await fetch(url, opts); }
    catch { throw new Error("Sem conexão com o servidor."); }
    const corpo = await r.json().catch(() => ({}));
    if (!r.ok) throw new Error(corpo.erro || `Erro ${r.status} em ${url}`);
    return corpo;
}

// Cores do Chart.js acompanham o tema atual
function aplicarTemaCharts() {
    Chart.defaults.color = css("--suave");
    Chart.defaults.borderColor = css("--borda");
}

// Registro de gráficos: recria se já existir (evita sobreposição)
const graficos = {};
function desenhar(id, config) {
    graficos[id]?.destroy();
    graficos[id] = new Chart($("#" + id), config);
    return graficos[id];
}

/* =========================================================
   CABEÇALHO: tema, menu mobile e ano do rodapé
   ========================================================= */
$("#btn-tema")?.addEventListener("click", () => {
    const novo = document.documentElement.dataset.tema === "dark" ? "light" : "dark";
    document.documentElement.dataset.tema = novo;
    localStorage.setItem("tema", novo);
    if (window.Chart) {
        aplicarTemaCharts();
        Object.values(graficos).forEach((g) => g.update());
    }
});

const btnMenu = $("#btn-menu"), menu = $("#menu");
function fecharMenu() { menu.classList.remove("aberto"); btnMenu.setAttribute("aria-expanded", "false"); }
btnMenu?.addEventListener("click", () => {
    const aberto = menu.classList.toggle("aberto");
    btnMenu.setAttribute("aria-expanded", String(aberto));
});
document.addEventListener("keydown", (e) => e.key === "Escape" && fecharMenu());

const ano = $("#ano");
if (ano) ano.textContent = new Date().getFullYear();

/* =========================================================
   1) OPERACIONAL: atualização a cada 3 segundos
   ========================================================= */
function iniciarOperacional() {
    const COR_STATUS = { "Aberto": "erro", "Em andamento": "aviso", "Resolvido": "ok" };
    const HEX_STATUS = { "Aberto": "#dc2626", "Em andamento": "#f59e0b", "Resolvido": "#16a34a" };

    // Gráfico ao vivo: criado uma vez e apenas atualizado
    const live = desenhar("grafico-live", {
        type: "line",
        data: {
            labels: [], datasets: [
                { label: "CPU %", data: [], borderColor: PALETA[0], tension: 0.3 },
                { label: "Memória %", data: [], borderColor: PALETA[1], tension: 0.3 },
            ]
        },
        options: { animation: false, scales: { y: { min: 0, max: 100 } } },
    });
    const grafStatus = desenhar("grafico-status", {
        type: "bar",
        data: { labels: [], datasets: [{ data: [], backgroundColor: [] }] },
        options: { plugins: { legend: { display: false } } },
    });

    let ocupado = false;
    async function atualizar() {
        if (ocupado || document.hidden) return;  // evita chamadas sobrepostas e com aba oculta
        ocupado = true;
        try {
            const d = await api("/api/operacional");
            $("#cpu").textContent = d.metricas.cpu + "%";
            $("#memoria").textContent = d.metricas.memoria + "%";
            $("#disco").textContent = d.metricas.disco + "%";
            $("#aviso-simulado").hidden = !d.metricas.simulado;
            $("#abertos").textContent = d.status.find((s) => s.status === "Aberto")?.total ?? 0;

            // Janela deslizante com os últimos 20 pontos
            live.data.labels.push(new Date().toLocaleTimeString("pt-BR"));
            live.data.datasets[0].data.push(d.metricas.cpu);
            live.data.datasets[1].data.push(d.metricas.memoria);
            if (live.data.labels.length > 20) {
                live.data.labels.shift();
                live.data.datasets.forEach((ds) => ds.data.shift());
            }
            live.update();

            grafStatus.data.labels = d.status.map((s) => s.status);
            grafStatus.data.datasets[0].data = d.status.map((s) => s.total);
            grafStatus.data.datasets[0].backgroundColor = d.status.map((s) => HEX_STATUS[s.status]);
            grafStatus.update();

            $("#tabela-chamados tbody").innerHTML = d.recentes.map((c) =>
                `<tr><td>${c.id}</td><td>${esc(c.titulo)}</td><td>${esc(c.prioridade)}</td>
         <td><span class="badge ${COR_STATUS[c.status] || ""}">${esc(c.status)}</span></td></tr>`).join("");
        } catch (e) {
            mostrarErro(e.message);
        } finally {
            ocupado = false;
        }
    }

    atualizar();
    setInterval(atualizar, 3000);
    document.addEventListener("visibilitychange", () => { if (!document.hidden) atualizar(); });
}

/* =========================================================
   2) ANALÍTICO: filtros que recarregam os dados
   ========================================================= */
function iniciarAnalitico() {
    const selR = $("#f-regiao"), selC = $("#f-categoria");
    let primeiraVez = true;

    async function carregar() {
        try {
            const d = await api("/api/analitico?" + new URLSearchParams({ regiao: selR.value, categoria: selC.value }));

            if (primeiraVez) {  // preenche os filtros só na primeira carga
                d.filtros.regioes.forEach((r) => selR.add(new Option(r, r)));
                d.filtros.categorias.forEach((c) => selC.add(new Option(c, c)));
                primeiraVez = false;
            }

            desenhar("grafico-mensal", {
                type: "line",
                data: {
                    labels: d.mensal.map((m) => m.mes),
                    datasets: [{
                        label: "Vendas (R$)", data: d.mensal.map((m) => m.total),
                        borderColor: PALETA[0], tension: 0.3
                    }]
                },
            });
            desenhar("grafico-categoria", {
                type: "doughnut",
                data: {
                    labels: d.por_categoria.map((c) => c.categoria),
                    datasets: [{ data: d.por_categoria.map((c) => c.total), backgroundColor: PALETA }]
                },
            });
            $("#tabela-top tbody").innerHTML = d.top.map((p) =>
                `<tr><td>${esc(p.produto)}</td><td>${p.qtd}</td><td>${brl(p.total)}</td></tr>`).join("");
        } catch (e) { mostrarErro(e.message); }
    }

    selR.addEventListener("change", carregar);
    selC.addEventListener("change", carregar);
    carregar();
}

/* =========================================================
   3) EXECUTIVO: poucos KPIs, meta e tendência
   ========================================================= */
async function iniciarExecutivo() {
    try {
        const d = await api("/api/executivo");
        $("#k-receita").textContent = brl(d.receita);
        $("#k-pedidos").textContent = d.pedidos;
        $("#k-ticket").textContent = brl(d.ticket_medio);
        $("#k-meta-pct").textContent = d.atingimento + "%";

        const v = $("#k-variacao");
        v.textContent = `${d.variacao >= 0 ? "▲" : "▼"} ${Math.abs(d.variacao)}% vs. 30 dias anteriores`;
        v.className = d.variacao >= 0 ? "pos" : "neg";

        desenhar("grafico-meta", {
            type: "doughnut",
            data: {
                labels: ["Realizado", "Falta para a meta"],
                datasets: [{
                    data: [Math.min(d.receita, d.meta), Math.max(d.meta - d.receita, 0)],
                    backgroundColor: ["#16a34a", "#94a3b8"]
                }]
            },
            options: { cutout: "70%" },
        });
        desenhar("grafico-tendencia", {
            type: "line",
            data: {
                labels: d.tendencia.map((t) => t.mes),
                datasets: [{
                    label: "Receita (R$)", data: d.tendencia.map((t) => t.total),
                    borderColor: PALETA[0], fill: true, backgroundColor: "rgba(37,99,235,.12)", tension: 0.3
                }]
            },
        });
    } catch (e) { mostrarErro(e.message); }
}

/* =========================================================
   4) ADMINISTRATIVO: CRUD de usuários
   ========================================================= */
function iniciarAdmin() {
    const corpo = $("#tabela-usuarios tbody"), form = $("#form-usuario"), msg = $("#msg");

    async function listar() {
        try {
            const us = await api("/api/usuarios");
            corpo.innerHTML = us.map((u) => `
        <tr>
          <td>${esc(u.nome)}</td><td>${esc(u.email)}</td><td>${esc(u.perfil)}</td>
          <td><span class="badge ${u.ativo ? "ok" : "erro"}">${u.ativo ? "Ativo" : "Inativo"}</span></td>
          <td>
            <button class="btn pequeno" data-acao="toggle" data-id="${u.id}">${u.ativo ? "Desativar" : "Ativar"}</button>
            <button class="btn pequeno perigo" data-acao="remover" data-id="${u.id}">Excluir</button>
          </td>
        </tr>`).join("");
        } catch (e) { mostrarErro(e.message); }
    }

    // Criar usuário (a mensagem de erro vem do servidor)
    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        try {
            await api("/api/usuarios", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(Object.fromEntries(new FormData(form))),
            });
            form.reset();
            msg.textContent = "";
            listar();
        } catch (err) { msg.textContent = err.message; }
    });

    // Ações da tabela (delegação de eventos)
    corpo.addEventListener("click", async (e) => {
        const btn = e.target.closest("button");
        if (!btn) return;
        const url = `/api/usuarios/${btn.dataset.id}`;
        try {
            if (btn.dataset.acao === "toggle") await api(url, { method: "PATCH" });
            if (btn.dataset.acao === "remover") {
                if (!confirm("Excluir este usuário?")) return;
                await api(url, { method: "DELETE" });
            }
        } catch (err) { mostrarErro(err.message); }
        listar();
    });

    listar();
}

/* =========================================================
   5) CIENTÍFICO: média móvel, tendência e anomalias
   ========================================================= */
function iniciarCientifico() {
    const slider = $("#janela");

    async function carregar() {
        try {
            const d = await api("/api/cientifico?janela=" + slider.value);
            $("#s-media").textContent = d.stats.media + " °C";
            $("#s-desvio").textContent = d.stats.desvio;
            $("#s-minmax").textContent = `${d.stats.minimo} / ${d.stats.maximo}`;
            $("#s-incl").textContent = d.stats.inclinacao;

            desenhar("grafico-cientifico", {
                type: "line",
                data: {
                    labels: d.labels, datasets: [
                        { label: "Temperatura (°C)", data: d.valores, borderColor: PALETA[0], pointRadius: 0, borderWidth: 1 },
                        { label: `Média móvel (${d.janela})`, data: d.media_movel, borderColor: PALETA[1], pointRadius: 0 },
                        { label: "Tendência linear", data: d.tendencia, borderColor: PALETA[2], borderDash: [6, 4], pointRadius: 0 },
                        // Só mostra pontos nos índices marcados como anomalia
                        {
                            label: "Anomalias", data: d.valores.map((v, i) => (d.anomalias.includes(i) ? v : null)),
                            showLine: false, borderColor: "#dc2626", backgroundColor: "#dc2626", pointRadius: 6
                        },
                    ]
                },
                options: { animation: false, scales: { x: { ticks: { maxTicksLimit: 10 } } } },
            });
        } catch (e) { mostrarErro(e.message); }
    }

    // Debounce: evita uma requisição a cada pixel do slider
    let espera;
    slider.addEventListener("input", () => {
        $("#janela-valor").textContent = slider.value;
        clearTimeout(espera);
        espera = setTimeout(carregar, 150);
    });
    carregar();
}

/* =========================================================
   6) EMBUTIDO: gera o iframe e o código de incorporação
   ========================================================= */
function iniciarEmbutido() {
    const sel = $("#tema-widget"), frame = $("#frame-widget"), codigo = $("#codigo-embed");

    function atualizar() {
        const url = `${location.origin}/widget/vendas?tema=${sel.value}`;
        frame.src = url;
        codigo.value = `<iframe src="${url}" width="100%" height="320" style="border:0;border-radius:12px" loading="lazy" title="Widget de vendas"></iframe>`;
    }
    sel.addEventListener("change", atualizar);
    atualizar();
}

/* =========================================================
   INICIALIZAÇÃO: escolhe a função pela página atual
   ========================================================= */
const iniciadores = {
    operacional: iniciarOperacional,
    analitico: iniciarAnalitico,
    executivo: iniciarExecutivo,
    administrativo: iniciarAdmin,
    cientifico: iniciarCientifico,
    embutido: iniciarEmbutido,
};

document.addEventListener("DOMContentLoaded", () => {
    const iniciar = iniciadores[document.body.dataset.page];
    if (!iniciar) return;

    // Páginas que não usam gráficos funcionam mesmo sem o Chart.js
    const usaGraficos = !["administrativo", "embutido"].includes(document.body.dataset.page);
    if (usaGraficos) {
        if (!window.Chart) {
            return mostrarErro("Chart.js não carregou. Rode 'python baixar_chartjs.py' ou conecte-se à internet.");
        }
        aplicarTemaCharts();
    }
    iniciar();
});
