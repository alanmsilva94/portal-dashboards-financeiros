"""
Converte os Excel (.xlsx) das pastas "bd" em JSON e grava na pasta do Google Drive
(sincronizada pelo Google Drive para computador). O Web App lê esses JSON.

Uso:
    python exportar_para_drive.py                # usa config.json ao lado do script
    python exportar_para_drive.py --forcar       # reconverte tudo, mesmo sem mudança
    python exportar_para_drive.py --so fluxo     # só um dashboard

Requisitos: pip install openpyxl

Formato gerado (por dashboard, em <destino>/<pasta>/):
    manifest.json                    {geradoEm, arquivos:[{arquivo, relPath, mtime, linhas}]}
    <relPath com "/" -> "__">.json   {abas:{"Aba1":[[c1,c2,...],...]}}
Datas viram o texto '\\u0001D:AAAA-MM-DDTHH:MM:SS' (a biblioteca portal_dados.html as reconverte).
"""
import argparse
import datetime as dt
import json
import sys
from pathlib import Path

import openpyxl

MARCA_DATA = "\u0001D:"


def converter(v):
    if isinstance(v, dt.datetime):
        return MARCA_DATA + v.replace(microsecond=0).isoformat()
    if isinstance(v, dt.date):
        return MARCA_DATA + dt.datetime(v.year, v.month, v.day).isoformat()
    if isinstance(v, dt.time):
        return v.strftime("%H:%M:%S")
    if isinstance(v, float) and v.is_integer() and abs(v) < 1e15:
        return int(v)
    return v


def ler_xlsx(caminho, cfg):
    colunas_max = cfg.get("colunas_max")
    ignorar_abas = {a.lower() for a in cfg.get("ignorar_abas", [])}
    wb = openpyxl.load_workbook(caminho, read_only=True, data_only=True)
    abas = {}
    total = 0
    for ws in wb.worksheets:
        if ws.title.lower() in ignorar_abas:
            continue
        linhas = []
        ws.reset_dimensions()  # planilhas que declaram A1:XFD1048576 fariam iterar milhões de células vazias
        for row in ws.iter_rows(values_only=True):
            lin = [converter(c) for c in (row[:colunas_max] if colunas_max else row)]
            while lin and lin[-1] in (None, ""):
                lin.pop()
            linhas.append(lin)
        while linhas and not linhas[-1]:
            linhas.pop()
        abas[ws.title] = linhas
        total += len(linhas)
    wb.close()
    return abas, total


def gravar_json(destino, obj):
    tmp = destino.with_suffix(".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    tmp.replace(destino)


def dividir(abas, max_linhas):
    """Quebra as abas em partes de até max_linhas linhas (0 = sem divisão).
    Cada parte repete todas as abas; a biblioteca do navegador junta as linhas na ordem."""
    if not max_linhas or all(len(v) <= max_linhas for v in abas.values()):
        return [abas]
    n = max(-(-len(v) // max_linhas) for v in abas.values())
    return [{k: v[i * max_linhas:(i + 1) * max_linhas] for k, v in abas.items()} for i in range(n)]


def carregar_reducer(cfg):
    """Opcional: "reducer": "reducers/maquinas.py" -> função reduzir(abas, relPath) -> abas
    para tirar colunas/linhas desnecessárias antes de subir ao Drive."""
    caminho = cfg.get("reducer")
    if not caminho:
        return None
    import importlib.util
    p = Path(caminho) if Path(caminho).is_absolute() else Path(__file__).resolve().parent / caminho
    spec = importlib.util.spec_from_file_location(p.stem, p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.reduzir


def exportar(chave, cfg, destino_raiz, forcar):
    reducer = carregar_reducer(cfg)
    origem = Path(cfg["origem"])
    saida = Path(destino_raiz) / cfg["pasta"]
    saida.mkdir(parents=True, exist_ok=True)
    manifest_path = saida / "manifest.json"
    anterior = {}
    if manifest_path.exists() and not forcar:
        try:
            anterior = {a["relPath"]: a for a in json.loads(manifest_path.read_text(encoding="utf-8"))["arquivos"]}
        except Exception:
            anterior = {}

    arquivos = []
    for padrao in cfg.get("padroes", ["**/*.xlsx"]):
        for f in sorted(origem.glob(padrao)):
            if f.name.startswith("~$") or f.suffix.lower() != ".xlsx":
                continue
            rel = f.relative_to(origem).as_posix()
            if any(a["relPath"] == rel for a in arquivos):
                continue
            mtime = int(f.stat().st_mtime)
            nome_json = rel.replace("/", "__").rsplit(".", 1)[0] + ".json"
            ant = anterior.get(rel)
            if ant and ant["mtime"] == mtime and (saida / nome_json).exists():
                arquivos.append(ant)
                print(f"  = {rel} (sem mudança)")
                continue
            try:
                abas, linhas = ler_xlsx(f, cfg)
            except Exception as e:  # arquivo aberto/bloqueado: mantém a versão anterior
                print(f"  ! {rel}: {e}", file=sys.stderr)
                if ant:
                    arquivos.append(ant)
                continue
            if reducer:
                abas = reducer(abas, rel)
                linhas = sum(len(v) for v in abas.values())
            partes = dividir(abas, cfg.get("linhas_por_parte", 0))
            for antigo in saida.glob(nome_json[:-5] + ".p*.json"):
                antigo.unlink()
            if len(partes) == 1:
                gravar_json(saida / nome_json, {"abas": partes[0]})
                entrada = {"arquivo": nome_json, "relPath": rel, "mtime": mtime, "linhas": linhas}
            else:
                nomes = [f"{nome_json[:-5]}.p{i + 1:03d}.json" for i in range(len(partes))]
                for n, p in zip(nomes, partes):
                    gravar_json(saida / n, {"abas": p})
                entrada = {"arquivo": nomes[0], "partes": nomes, "relPath": rel, "mtime": mtime, "linhas": linhas}
            arquivos.append(entrada)
            print(f"  + {rel} ({linhas} linhas, {len(partes)} parte(s))")

    gravar_json(manifest_path, {"geradoEm": dt.datetime.now().isoformat(timespec="seconds"), "arquivos": arquivos})
    print(f"[{chave}] {len(arquivos)} arquivo(s) -> {saida}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=str(Path(__file__).with_name("config.json")))
    ap.add_argument("--forcar", action="store_true")
    ap.add_argument("--so")
    ap.add_argument("--destino", help="sobrepõe o destino do config.json (ex.: uma pasta local para teste)")
    args = ap.parse_args()
    cfg = json.loads(Path(args.config).read_text(encoding="utf-8-sig"))
    destino = Path(args.destino or cfg["destino"])
    if not destino.exists() and not destino.parent.exists():
        sys.exit(
            f"ERRO: o destino '{destino}' não existe e a pasta acima dele também não.\n"
            "Se o Google Drive para computador não estiver instalado/aberto, a unidade (ex.: G:\\) não existe.\n"
            "Ajuste 'destino' no config.json para a pasta sincronizada do Drive, ou use --destino com uma pasta local."
        )
    for chave, c in cfg["dashboards"].items():
        if args.so and args.so != chave:
            continue
        print(f"[{chave}] lendo {c['origem']}")
        exportar(chave, c, destino, args.forcar)


if __name__ == "__main__":
    main()
