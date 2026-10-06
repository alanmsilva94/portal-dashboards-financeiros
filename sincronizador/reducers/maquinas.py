"""
Reducer do dashboard 'maquinas' (Máquinas de Cartões).

A planilha original tem ~248 mil linhas e 63 colunas na aba Igrejas, mas o dashboard
só trabalha com um "cubo" agregado por PDV x mês x canal x tipo x bandeira x status
(ver Maquinas_Maquinas/js/models/CuboModel.js). Este reducer faz essa agregação ANTES
de subir ao Drive, sem alterar nenhum número exibido:

  * Cartões e Pix: uma linha por (mês, PDV, tipo, bandeira, status) com Valor = soma
    e a nova coluna "Qtd" = nº de transações. O dashboard (PlanilhaModel) entende "Qtd".
    A data vira o 1º dia do mês (o dashboard só usa ano-mês).
    As chaves de agrupamento são os valores BRUTOS da planilha: qualquer normalização
    posterior (capitalização, acentos, trim) acontece no navegador, igual ao original.
    Linhas que o original descartaria (data, PDV ou valor inválidos) são descartadas aqui.
  * Maquinas: mantida inteira (já é pequena), todas as linhas.
  * Igrejas: só as colunas usadas e só as igrejas referenciadas por alguma máquina
    (a observação/endereços/telefones etc. eram quase todo o peso).
  * Abas não reconhecidas são removidas.

Se alguma aba não puder ser mapeada com segurança (coluna essencial ausente), ela é
repassada sem alteração: o dashboard então se comporta como antes (e avisa).

Roda no sincronizador: reduzir(abas, relPath) -> abas.
"""
import re
import unicodedata
from datetime import datetime

MARCA_DATA = "\u0001D:"
SEM_LOCAL = "Sem localidade"

# ---- dicionários espelhados de js/models/PlanilhaModel.js ------------------------------
ABAS = {
    "igrejas": ["igrejas", "igreja", "cadastroigrejas", "unidades"],
    "maquinas": ["maquinas", "maquina", "pdvs", "pdv", "terminais", "pos"],
    "cartoes": ["cartoes", "cartao", "cartaodecredito", "vendascartao", "transacoescartao"],
    "pix": ["pix", "transacoespix", "vendaspix"],
}

COLS_IGREJAS = {
    "igreja_id": ["ID", "Id Igreja", "ID_Igreja", "Codigo"],
    "igreja_nome": ["Nome", "Razao Social"],
    "igreja_fantasia": ["N Fantasia", "Nome Fantasia"],
    "igreja_desc": [
        "Desc Igreja", "Desc.Igreja", "Desc. Igreja", "Descricao Igreja", "Descricao da Igreja",
        "Desc da Igreja", "Tipo Igreja", "Tipo de Igreja", "Classificacao",
        "Classificacao da Unidade", "Classificacao Igreja", "Perfil Igreja",
    ],
    "estado": ["Estado", "UF"],
    "municipio": ["Municipio", "Cidade"],
    "regiao": ["Desc.Regiao", "Desc Regiao", "Regiao"],
    "status_igreja": ["Status"],
    "qtd_membros": ["Qtd.Membros", "Qtd Membros", "Membros"],
    "tipo_imovel": ["Tipo Imovel", "Tipo do Imovel"],
}
# cabeçalho canônico gravado na saída (o dashboard reconhece todos por alias)
CANON_IGREJAS = {
    "igreja_id": "ID", "igreja_nome": "Nome", "igreja_fantasia": "N Fantasia",
    "igreja_desc": "Desc Igreja", "estado": "Estado", "municipio": "Municipio",
    "regiao": "Desc.Regiao", "status_igreja": "Status", "qtd_membros": "Qtd.Membros",
    "tipo_imovel": "Tipo Imovel",
}
COLS_MAQUINAS = {
    "pdv": ["PDV", "Pdv", "Ponto de Venda"],
    "numero_serie": ["N de serie", "Numero de serie", "Serie", "Serial"],
    "modelo": ["Modelo"],
    "igreja_id": ["ID_Igreja", "ID Igreja", "IdIgreja", "ID"],
}
CANON_MAQUINAS = {"pdv": "PDV", "numero_serie": "N de serie", "modelo": "Modelo", "igreja_id": "ID_Igreja"}
COLS_CARTOES = {
    "data": ["Data", "Data Transacao", "Data da Venda"],
    "pdv": ["Pdv", "PDV"],
    "tipo": ["Tipo", "Tipo Transacao", "Modalidade"],
    "bandeira": ["Bandeira"],
    "valor": ["Valor", "Valor Transacao"],
    "status": ["Status", "Situacao"],
}
COLS_PIX = {
    "data": ["Data", "Data Transacao"],
    "status": ["Status", "Situacao"],
    "pdv": ["PDV", "Pdv"],
    "valor": ["Valor transacao", "Valor", "Valor da transacao"],
}


# ---- utilitários espelhados de js/utils/texto.js ---------------------------------------
def slug(v):
    if v is None:
        return ""
    s = unicodedata.normalize("NFD", str(v))
    s = re.sub(r"[̀-ͯ]", "", s).lower()
    return re.sub(r"[^a-z0-9]", "", s)


def achar_coluna(cabecalhos, aliases):
    """Índice do cabeçalho real (mesma regra do JS: exato por slug, depois parcial) ou None."""
    mapa = {}
    for i, c in enumerate(cabecalhos):
        mapa[slug(c)] = i  # o último duplicado vence, como no Map do JS
    for alias in aliases:
        k = slug(alias)
        if k in mapa:
            return mapa[k]
    for alias in aliases:
        k = slug(alias)
        if not k:
            continue
        for chave, i in mapa.items():
            if k in chave or chave in k:
                return i
    return None


def texto(v, padrao=None):
    if v is None:
        return padrao
    t = re.sub(r"\s+", " ", str(v).strip())
    if not t or t == "-" or t.lower() == "nan":
        return padrao
    return t


def chave(v):
    if v is None:
        return None
    t = re.sub(r"\.0$", "", str(v).strip()).upper()
    if not t or t in ("NAN", "NONE"):
        return None
    return t


def para_float(v):
    if isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return float(v) if v == v and v not in (float("inf"), float("-inf")) else None
    if v is None:
        return None
    t = re.sub(r"[\s ]", "", re.sub(r"r\$", "", str(v).strip(), flags=re.I))
    if not t:
        return None
    negativo = False
    if t.startswith("(") and t.endswith(")"):
        negativo = True
        t = t[1:-1]
    if "," in t:
        t = t.replace(".", "").replace(",", ".", 1)
    m = re.match(r"^[+-]?(\d+\.?\d*|\.\d+)([eE][+-]?\d+)?", t)  # parseFloat
    if not m:
        return None
    n = float(m.group(0))
    return -n if negativo else n


def para_ano_mes(v):
    """(ano, mes) de uma data como o dashboard a leria, ou None se for inválida."""
    if v is None or v == "" or v == 0:
        return None
    if isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        if v != v:
            return None
        d = datetime(1899, 12, 30) + __import__("datetime").timedelta(days=float(v))
        return d.year, d.month
    t = str(v).strip()
    if t.startswith(MARCA_DATA):
        try:
            d = datetime.fromisoformat(t[len(MARCA_DATA):])
            return d.year, d.month
        except ValueError:
            return None
    m = re.match(r"^(\d{1,2})[/\-.](\d{1,2})[/\-.](\d{2,4})", t)
    if m:
        ano = int(m.group(3))
        if ano < 100:
            ano += 2000
        return (ano, int(m.group(2))) if 1 <= int(m.group(2)) <= 12 else None
    m = re.match(r"^(\d{4})[/\-.](\d{1,2})[/\-.](\d{1,2})", t)
    if m:
        return (int(m.group(1)), int(m.group(2))) if 1 <= int(m.group(2)) <= 12 else None
    return None  # formato exótico: o original tentaria new Date(t); aqui o repassamos como inválido


def identificar_aba(nome, cabecalhos):
    s = slug(nome)
    for tipo, aliases in ABAS.items():
        if any(slug(a) == s for a in aliases):
            return tipo
    for tipo, aliases in ABAS.items():
        if any(slug(a) in s for a in aliases):
            return tipo
    cols = [slug(c) for c in cabecalhos]
    if "bandeira" in cols and "valor" in cols:
        return "cartoes"
    if any("valortransacao" in c for c in cols):
        return "pix"
    if "idigreja" in cols or ("modelo" in cols and "pdv" in cols):
        return "maquinas"
    if "descregiao" in cols or "qtdmembros" in cols:
        return "igrejas"
    return None


def _mapear(cab, mapa):
    return {dest: achar_coluna(cab, aliases) for dest, aliases in mapa.items()}


def _celula(lin, i):
    return lin[i] if i is not None and i < len(lin) else None


def _num(x):
    x = round(x, 6)
    return int(x) if x == int(x) and abs(x) < 1e15 else x


# ---- reduções por aba ------------------------------------------------------------------
def _fatos(linhas, col, canon_cols, extra_cols_pix):
    """Agrupa em (ano-mes, pdv, tipo, bandeira, status) com soma e contagem."""
    grupos = {}
    for lin in linhas[1:]:
        ym = para_ano_mes(_celula(lin, col["data"]))
        pdv_raw = _celula(lin, col["pdv"])
        valor = para_float(_celula(lin, col["valor"]))
        if ym is None or chave(pdv_raw) is None or valor is None:
            continue
        k = (
            ym, pdv_raw,
            _celula(lin, col.get("tipo")), _celula(lin, col.get("bandeira")),
            _celula(lin, col["status"]),
        )
        g = grupos.get(k)
        if g:
            g[0] += valor
            g[1] += 1
        else:
            grupos[k] = [valor, 1]
    return grupos


def _reduzir_cartoes(linhas):
    col = _mapear(linhas[0], COLS_CARTOES)
    if any(col[c] is None for c in ("data", "pdv", "valor")):
        return linhas
    grupos = _fatos(linhas, col, None, None)
    saida = [["Data", "Pdv", "Tipo", "Bandeira", "Valor", "Status", "Qtd"]]
    for (ym, pdv, tipo, band, status), (valor, qtd) in sorted(grupos.items(), key=lambda kv: (kv[0][0], str(kv[0][1]))):
        saida.append([f"{MARCA_DATA}{ym[0]:04d}-{ym[1]:02d}-01T00:00:00", pdv, tipo, band, _num(valor), status, qtd])
    return saida


def _reduzir_pix(linhas):
    col = _mapear(linhas[0], COLS_PIX)
    if any(col[c] is None for c in ("data", "pdv", "valor")):
        return linhas
    grupos = _fatos(linhas, col, None, None)
    saida = [["Data", "Status", "PDV", "Valor", "Qtd"]]
    for (ym, pdv, _t, _b, status), (valor, qtd) in sorted(grupos.items(), key=lambda kv: (kv[0][0], str(kv[0][1]))):
        saida.append([f"{MARCA_DATA}{ym[0]:04d}-{ym[1]:02d}-01T00:00:00", status, pdv, _num(valor), qtd])
    return saida


def _ids_das_maquinas(linhas):
    col = _mapear(linhas[0], COLS_MAQUINAS)
    ids = set()
    if col["pdv"] is None or col["igreja_id"] is None:
        return None
    for lin in linhas[1:]:
        if chave(_celula(lin, col["pdv"])) is None:
            continue
        i = chave(_celula(lin, col["igreja_id"]))
        if i:
            ids.add(i)
    return ids


def _reduzir_igrejas(linhas, ids_ref):
    col = _mapear(linhas[0], COLS_IGREJAS)
    if col["igreja_id"] is None or ids_ref is None:
        return linhas
    campos = [c for c in CANON_IGREJAS if col[c] is not None]
    # última linha de cada ID vence (igrejas.set(id, ...) no original)
    por_id = {}
    for lin in linhas[1:]:
        i = chave(_celula(lin, col["igreja_id"]))
        if i:
            por_id[i] = lin
    manter = [lin for i, lin in por_id.items() if i in ids_ref]
    # o dashboard avisa se uma coluna de localização vem vazia em TODAS as igrejas: preserva esse sinal
    for campo in ("igreja_desc", "regiao", "estado"):
        if col[campo] is None:
            continue
        if all(texto(_celula(lin, col[campo])) is None for lin in manter):
            extra = next((lin for i, lin in por_id.items()
                          if i not in ids_ref and texto(_celula(lin, col[campo])) is not None), None)
            if extra is not None:
                manter.append(extra)
    saida = [[CANON_IGREJAS[c] for c in campos]]
    for lin in manter:
        saida.append([_celula(lin, col[c]) for c in campos])
    return saida


def reduzir(abas, relPath):
    tipos = {}
    for nome, linhas in abas.items():
        if linhas:
            tipos[nome] = identificar_aba(nome, [str(c) for c in linhas[0]])
    ids_ref = None
    for nome, t in tipos.items():
        if t == "maquinas":
            r = _ids_das_maquinas([[str(c) if c is not None else "" for c in abas[nome][0]]] + abas[nome][1:])
            if r is not None:
                ids_ref = (ids_ref or set()) | r
    saida = {}
    for nome, t in tipos.items():
        linhas = abas[nome]
        cab = [str(c) if c is not None else "" for c in linhas[0]]
        linhas = [cab] + linhas[1:]
        if t == "cartoes":
            saida[nome] = _reduzir_cartoes(linhas)
        elif t == "pix":
            saida[nome] = _reduzir_pix(linhas)
        elif t == "igrejas":
            saida[nome] = _reduzir_igrejas(linhas, ids_ref)
        elif t == "maquinas":
            saida[nome] = linhas
        # t is None: aba ignorada pelo dashboard -> descartada
    return saida
