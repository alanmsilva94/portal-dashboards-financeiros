"""
Simula o Apps Script localmente para testar um dashboard no navegador.

    python harness.py <chave> [--dados PASTA_DOS_JSON] [--porta 8765]
    abre: http://localhost:8765/

- Renderiza apps_script/<arquivo>.html resolvendo <?!= include('x') ?>, <?= APP_URL ?>, <?= EMAIL ?>,
  <?= CHAVE ?> e <?!= JSON.stringify(...) ?> dessas variáveis.
- Injeta um stub de google.script.run (api_listar / api_ler) que lê os JSON gerados
  por sincronizador/exportar_para_drive.py (mesma estrutura do Drive).
- Qualquer outra função de servidor chamada pelo dashboard cai em erro claro no console.
"""
import argparse
import datetime as dt
import json
import re
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs

AQUI = Path(__file__).resolve().parent
APPS = AQUI.parent / "apps_script"
ARQUIVOS = {"home": "home", "analise": "dash_analise", "cartoes": "dash_cartoes", "fluxo": "dash_fluxo", "maquinas": "dash_maquinas"}
DASHBOARDS_TESTE = [
    {"chave": "analise", "titulo": "Análise Semanal", "desc": "Pagamentos por semana, empresa, banco e departamento.", "icone": ""},
    {"chave": "cartoes", "titulo": "Cartões Corporativos", "desc": "Controle de gastos do cartão de crédito.", "icone": ""},
    {"chave": "fluxo", "titulo": "Fluxo de Caixa", "desc": "Entradas e saídas, histórico desde 2018.", "icone": ""},
    {"chave": "maquinas", "titulo": "Máquinas de Cartões", "desc": "Receita por máquina, localidade e estado.", "icone": ""},
]
PASTAS = {"analise": "analise_semanal", "cartoes": "cartoes", "fluxo": "fluxo_de_caixa", "maquinas": "maquinas"}


def renderizar(arquivo, chave, porta):
    vars_ = {"APP_URL": f"http://localhost:{porta}/", "EMAIL": "teste@empresa.exemplo.com", "CHAVE": chave, "DASH": "",
             "DASHBOARDS": DASHBOARDS_TESTE}

    def include(m):
        return renderizar_texto((APPS / (m.group(1) + ".html")).read_text(encoding="utf-8"), vars_)

    return renderizar_texto((APPS / (arquivo + ".html")).read_text(encoding="utf-8"), vars_)


def renderizar_texto(t, vars_):
    # No Apps Script scriptlets dentro de comentarios HTML tambem sao avaliados; aqui os removemos
    # (com aviso) para o harness nao entrar em recursao infinita de include.
    def _tira(m):
        print("AVISO: comentario HTML com '<?' (o Apps Script avaliaria isto): " + m.group(0)[:70].replace("\n", " "), file=sys.stderr)
        return ""
    t = re.sub(r"<!--(?:(?!-->).)*?<\?.*?-->", _tira, t, flags=re.S)
    t = re.sub(r"<\?!=\s*include\('([\w\-]+)'\)\s*\?>",
               lambda m: renderizar_texto((APPS / (m.group(1) + ".html")).read_text(encoding="utf-8"), vars_), t)
    t = re.sub(r"<\?!=\s*JSON\.stringify\((\w+)\)\s*\?>", lambda m: json.dumps(vars_.get(m.group(1), "")), t)
    t = re.sub(r"<\?=\s*(\w+)\s*\?>", lambda m: str(vars_.get(m.group(1), "")), t)
    return t


CONF = {}  # conferências simuladas, em memória (zeram ao reiniciar o harness)

STUB = """<script>
window.google = { script: { run: (function () {
  function criar(ok, err) {
    var o = { withSuccessHandler: function (f) { return criar(f, err); }, withFailureHandler: function (f) { return criar(ok, f); } };
    ['api_listar', 'api_ler', 'api_conf_ler', 'api_conf_salvar'].forEach(function (fn) {
      o[fn] = function () {
        var a = Array.prototype.slice.call(arguments);
        fetch('/__api/' + fn + '?args=' + encodeURIComponent(JSON.stringify(a)))
          .then(function (r) { return r.json(); })
          .then(function (j) { if (j.erro) throw new Error(j.erro); ok && ok(j.ok); })
          .catch(function (e) { (err || function (x) { console.error('google.script.run', x); })(e); });
      };
    });
    return new Proxy(o, { get: function (t, k) { return k in t ? t[k] : function () { console.error('Função de servidor não simulada no harness: ' + String(k)); }; } });
  }
  return criar(null, null);
})() } };
</script>"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("chave", choices=ARQUIVOS)
    ap.add_argument("--dados", required=True, help="pasta-raiz com as subpastas geradas pelo sincronizador")
    ap.add_argument("--porta", type=int, default=8765)
    a = ap.parse_args()
    raiz = Path(a.dados) / PASTAS.get(a.chave, "")

    class H(BaseHTTPRequestHandler):
        def log_message(self, *x):
            pass

        def _send(self, code, body, tipo):
            b = body.encode("utf-8") if isinstance(body, str) else body
            self.send_response(code)
            self.send_header("Content-Type", tipo)
            self.send_header("Content-Length", str(len(b)))
            self.end_headers()
            self.wfile.write(b)

        def do_GET(self):
            u = urlparse(self.path)
            if u.path.startswith("/__api/"):
                fn = u.path.split("/")[-1]
                args = json.loads(parse_qs(u.query)["args"][0])
                try:
                    if fn == "api_listar":
                        pasta = (Path(a.dados) / PASTAS[args[0]]) if args and args[0] in PASTAS else raiz
                        m = json.loads((pasta / "manifest.json").read_text(encoding="utf-8"))
                        res = {"geradoEm": m["geradoEm"], "arquivos": m["arquivos"]}
                    elif fn == "api_conf_ler":
                        res = list(CONF.values())
                    elif fn == "api_conf_salvar":
                        agora = dt.datetime.now().isoformat(timespec="seconds")
                        for it in args[1] or []:
                            if it.get("v") is None:
                                CONF.pop(str(it["k"]), None)
                            else:
                                CONF[str(it["k"])] = {"k": str(it["k"]), "v": str(it["v"]), "por": "teste@empresa.exemplo.com", "em": agora}
                        res = list(CONF.values())
                    else:
                        res = json.loads((raiz / args[1]).read_text(encoding="utf-8"))
                    self._send(200, json.dumps({"ok": res}, ensure_ascii=False), "application/json; charset=utf-8")
                except Exception as e:
                    self._send(200, json.dumps({"erro": str(e)}), "application/json")
                return
            html = renderizar(ARQUIVOS[a.chave], a.chave, a.porta)
            html = re.sub(r"(<head[^>]*>)", lambda m: m.group(1) + STUB, html, count=1, flags=re.I) if re.search(r"<head", html, re.I) else STUB + html
            self._send(200, html, "text/html; charset=utf-8")

    print(f"Dashboard '{a.chave}' em http://localhost:{a.porta}/  (dados: {raiz})")
    ThreadingHTTPServer(("127.0.0.1", a.porta), H).serve_forever()


if __name__ == "__main__":
    main()
