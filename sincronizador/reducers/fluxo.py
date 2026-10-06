"""
Reducer do dashboard Fluxo de Caixa.

O dashboard só usa, de cada planilha:
  Entradas_AAAA.xlsx : Data | Entradas do dia (ou Entradas/Entrada/Valor/Valor (R$)/Total)
  Saidas_AAAA.xlsx   : Data | Departamento | Valor
e dele só sai a soma por mês (e por mês+departamento), a contagem de lançamentos, os avisos
(datas/valores inválidos, sem departamento, departamentos novos) e o último dia lançado.

Por isso cada arquivo é agregado por (dia, departamento) — ou só por dia, nas entradas — com
as colunas auxiliares abaixo, que o dashboard (dash_fluxo_base.html) soma de volta. Os números
finais são os mesmos da leitura linha a linha, e um Saidas de ~10 MB vira ~100 KB.

Saídas : Data | Departamento | Valor | Qtd | ValorInvalido | DataInvalida
Entradas: Data | Entradas do dia | Qtd | ValorInvalido | DataInvalida
  Qtd           = lançamentos agrupados na linha
  ValorInvalido = quantos desses tinham valor ilegível (contados como zero)
  DataInvalida  = (linha sem data) quantas linhas com conteúdo tinham data ilegível

A interpretação de datas/números/nomes espelha base-local.js (comoData, comoNumero, normalizar)
e a classificação por nome de arquivo/pasta espelha classificarArquivo().
Se a planilha não tiver as colunas esperadas, ela é devolvida sem alteração (o dashboard
mostrará o mesmo erro de antes).
"""
import calendar
import datetime as dt
import math
import re
import unicodedata

MARCA_DATA = "\u0001D:"
COLS_ENTRADAS = [["Data"], ["Entradas do dia", "Entradas", "Entrada", "Valor", "Valor (R$)", "Total"]]
COLS_SAIDAS = [["Data"], ["Departamento", "Setor", "Depto"], ["Valor", "Valor (R$)", "Total"]]


def normalizar(txt):
    s = "" if txt is None else str(txt)
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", s).strip().upper()


def _vazio(c):
    return c is None or c == ""


def como_data(v):
    """-> date ou None (mesmas regras de comoData)."""
    if v is None or isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        if math.isfinite(v) and v > 0:
            try:
                return dt.date(1899, 12, 30) + dt.timedelta(days=math.floor(v))
            except (OverflowError, ValueError):
                return None
        return None
    if isinstance(v, str):
        if v.startswith(MARCA_DATA):
            try:
                return dt.datetime.fromisoformat(v[len(MARCA_DATA):]).date()
            except ValueError:
                return None
        t = v.strip()
        m = re.match(r"^(\d{1,2})[/\-](\d{1,2})[/\-](\d{2,4})$", t)
        if m:
            ano = int(m.group(3))
            if ano < 100:
                ano += 2000
            return _date(ano, int(m.group(2)), int(m.group(1)))
        m = re.match(r"^(\d{4})-(\d{1,2})-(\d{1,2})", t)
        if m:
            return _date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    return None


def _date(a, m, d):
    """O JS não valida o dia (ex.: 31/02 cai em fevereiro); aqui o dia é limitado ao fim do mês."""
    if not (1 <= m <= 12 and 1 <= a <= 9999 and d >= 1):
        return None
    try:
        return dt.date(a, m, min(d, calendar.monthrange(a, m)[1]))
    except ValueError:
        return None


_NUM = re.compile(r"^[+-]?(\d+\.?\d*|\.\d+)([eE][+-]?\d+)?")


def como_numero(v):
    """-> float ou None (mesmas regras de comoNumero)."""
    if v is None or v == "":
        return None
    if isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return float(v) if math.isfinite(v) else None
    t = re.sub(r"\s", "", str(v).replace("R$", ""))
    if not t:
        return None
    if "," in t:
        t = t.replace(".", "").replace(",", ".")
    m = _NUM.match(t)
    return float(m.group(0)) if m else None


def tipo_arquivo(rel):
    """'entradas' | 'saidas' | None, como classificarArquivo() + tipoDaPasta() do dashboard."""
    partes = unicodedata.normalize("NFC", rel).split("/")
    tipo_pasta = None
    for p in partes[:-1]:
        n = normalizar(p)
        if "SAIDA" in n:
            tipo_pasta = "saidas"
        elif "ENTRADA" in n:
            tipo_pasta = "entradas"
    base = normalizar(re.sub(r"\.xlsx$", "", partes[-1], flags=re.I))
    ano = re.search(r"(?:^|[^0-9])(20\d{2})(?:[^0-9]|$)", base)
    if "ENTRADA" in base:
        return "entradas"
    if "SAIDA" in base:
        return "saidas"
    if tipo_pasta:
        return tipo_pasta
    return "saidas" if ano else None


def _achar(cab, obrigatorias):
    idx = {}
    nomes_cab = [normalizar(c) for c in cab]
    for nomes in obrigatorias:
        pos = -1
        for n in nomes:
            alvo = normalizar(n)
            if alvo in nomes_cab:
                pos = nomes_cab.index(alvo)
                break
        if pos < 0:
            return None
        idx[nomes[0]] = pos
    return idx


def _extra(cab, nome):
    alvo = normalizar(nome)
    for i, c in enumerate(cab):
        if normalizar(c) == alvo:
            return i
    return -1


def _marca(d):
    return MARCA_DATA + dt.datetime(d.year, d.month, d.day).isoformat()


def reduzir(abas, relPath):
    if not abas:
        return abas
    tipo = tipo_arquivo(relPath)
    if tipo is None:
        return abas
    nome_aba = next(iter(abas))          # o dashboard só lê a primeira aba
    linhas = [l for l in abas[nome_aba] if any(not _vazio(c) for c in l)]
    if not linhas:
        return {nome_aba: linhas}
    cab = [("" if c is None else str(c).strip()) for c in linhas[0]]
    cols = _achar(cab, COLS_ENTRADAS if tipo == "entradas" else COLS_SAIDAS)
    if cols is None:
        return abas
    # já reduzido (ou com colunas de contagem de origem): não reagrega
    if _extra(cab, "Qtd") >= 0 and _extra(cab, "DataInvalida") >= 0:
        return {nome_aba: linhas}

    i_data = cols["Data"]
    i_val = cols["Entradas do dia"] if tipo == "entradas" else cols["Valor"]
    i_dep = cols["Departamento"] if tipo == "saidas" else None

    grupos = {}          # (data, dep) -> [valores, qtd, invalidos]
    data_invalida = 0
    for lin in linhas[1:]:
        def cel(i):
            return lin[i] if i < len(lin) else None
        d = como_data(cel(i_data))
        if d is None:
            data_invalida += 1       # a linha tem conteúdo (linhas vazias já saíram)
            continue
        v = como_numero(cel(i_val))
        dep = ""
        if i_dep is not None:
            bruto = cel(i_dep)
            dep = "" if bruto is None else str(bruto).strip()
        g = grupos.setdefault((d, dep), [[], 0, 0])
        if v is None:
            g[2] += 1
            v = 0.0
        g[0].append(v)
        g[1] += 1

    saida = []
    if tipo == "saidas":
        saida.append(["Data", "Departamento", "Valor", "Qtd", "ValorInvalido", "DataInvalida"])
        for (d, dep), (vals, qtd, inval) in sorted(grupos.items(), key=lambda kv: (kv[0][0], kv[0][1])):
            saida.append([_marca(d), dep or None, round(math.fsum(vals), 6), qtd, inval, 0])
        if data_invalida:
            saida.append([None, None, 0, 0, 0, data_invalida])
    else:
        saida.append(["Data", "Entradas do dia", "Qtd", "ValorInvalido", "DataInvalida"])
        for (d, _), (vals, qtd, inval) in sorted(grupos.items(), key=lambda kv: kv[0][0]):
            saida.append([_marca(d), round(math.fsum(vals), 6), qtd, inval, 0])
        if data_invalida:
            saida.append([None, 0, 0, 0, data_invalida])
    return {nome_aba: saida}
