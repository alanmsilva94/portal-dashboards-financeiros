/**
 * Portal de Dashboards Financeiros - Web App (Google Apps Script)
 *
 * Rotas (?p=):
 *   login    -> tela de entrada (padrão quando não há ?p=)
 *   home     -> escolha do dashboard
 *   analise | cartoes | fluxo | maquinas -> dashboards
 *
 * Implantação: Executar como "Eu" / Acesso "Qualquer pessoa da organização empresa.exemplo.com".
 * Assim a pasta de dados no Drive fica só com o dono, e quem decide quem entra é Acessos.gs.
 */

const DASHBOARDS = {
  analise: { titulo: 'Análise Semanal',        desc: 'Pagamentos por semana, empresa, banco e departamento.', arquivo: 'dash_analise', pasta: 'analise_semanal', icone: '📅' },
  cartoes: { titulo: 'Cartões Corporativos',      desc: 'Controle de gastos do cartão de crédito.',              arquivo: 'dash_cartoes', pasta: 'cartoes',         icone: '💳' },
  fluxo:   { titulo: 'Fluxo de Caixa',         desc: 'Entradas e saídas, histórico desde 2018.',              arquivo: 'dash_fluxo',   pasta: 'fluxo_de_caixa',  icone: '💰' },
  maquinas: { titulo: 'Máquinas de Cartões',    desc: 'Receita por máquina, localidade e estado.',             arquivo: 'dash_maquinas', pasta: 'maquinas',         icone: '🗺️' }
};

function doGet(e) {
  const p = String((e && e.parameter && e.parameter.p) || 'login').toLowerCase();
  const email = usuarioAtual_();

  if (!email || !temAcesso_(email)) return pagina_('negado', { email: email });
  if (p === 'login') return pagina_('login', { email: email });
  if (p === 'home') return pagina_('home', { email: email, dashboards: dashboardsDoUsuario_(email) });

  const d = DASHBOARDS[p];
  if (!d) return pagina_('home', { email: email, dashboards: dashboardsDoUsuario_(email) });
  if (!temAcesso_(email, p)) return pagina_('negado', { email: email, dash: d.titulo });
  return pagina_(d.arquivo, { email: email, chave: p, dashboards: dashboardsDoUsuario_(email) });
}

function pagina_(arquivo, vars) {
  const t = HtmlService.createTemplateFromFile(arquivo);
  t.APP_URL = ScriptApp.getService().getUrl();
  t.EMAIL = (vars && vars.email) || '';
  t.CHAVE = (vars && vars.chave) || '';
  t.DASH = (vars && vars.dash) || '';
  t.DASHBOARDS = (vars && vars.dashboards) || [];
  return t.evaluate()
    .setTitle('Portal Financeiro · Dashboards')
    .addMetaTag('viewport', 'width=device-width, initial-scale=1')
    .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
}

/** Usado nos HTMLs: include('arquivo') dentro de uma diretiva de template.
 *  O parcial também é avaliado como template (APP_URL, EMAIL), por isso ele não pode
 *  conter diretivas literais nem em comentários. */
function include(nome) {
  const t = HtmlService.createTemplateFromFile(nome);
  t.APP_URL = ScriptApp.getService().getUrl();
  t.EMAIL = usuarioAtual_();
  return t.evaluate().getContent();
}

function usuarioAtual_() {
  return String(Session.getActiveUser().getEmail() || '').toLowerCase();
}

function dashboardsDoUsuario_(email) {
  return Object.keys(DASHBOARDS)
    .filter(function (k) { return temAcesso_(email, k); })
    .map(function (k) {
      const d = DASHBOARDS[k];
      return { chave: k, titulo: d.titulo, desc: d.desc, icone: d.icone };
    });
}

/* ------------------------------------------------------------------ *
 *  API de dados (chamada pelos dashboards com google.script.run)
 *  Os dados ficam na pasta do Drive indicada na propriedade do script
 *  PASTA_DADOS_ID, uma subpasta por dashboard, gerada pelo
 *  sincronizador (exportar_para_drive.py).
 * ------------------------------------------------------------------ */

function pastaDados_(chave) {
  const d = DASHBOARDS[chave];
  if (!d) throw new Error('Dashboard desconhecido.');
  const email = usuarioAtual_();
  if (!email || !temAcesso_(email, chave)) throw new Error('Sem acesso a este dashboard.');
  const raizId = PropertiesService.getScriptProperties().getProperty('PASTA_DADOS_ID');
  if (!raizId) throw new Error('Configure a propriedade PASTA_DADOS_ID (Configurações do projeto > Propriedades do script).');
  const it = DriveApp.getFolderById(raizId).getFoldersByName(d.pasta);
  if (!it.hasNext()) throw new Error('Pasta de dados não encontrada no Drive: ' + d.pasta);
  return it.next();
}

function lerJson_(pasta, nomeArquivo) {
  // Se o mesmo nome foi enviado mais de uma vez ao Drive, usa a cópia mais recente.
  const it = pasta.getFilesByName(nomeArquivo);
  let melhor = null;
  while (it.hasNext()) {
    const f = it.next();
    if (!melhor || f.getLastUpdated().getTime() > melhor.getLastUpdated().getTime()) melhor = f;
  }
  if (!melhor) throw new Error('Arquivo de dados não encontrado: ' + nomeArquivo);
  return JSON.parse(melhor.getBlob().getDataAsString('UTF-8'));
}

/* ------------------------------------------------------------------ *
 *  Conferências compartilhadas (Google Sheets)
 *  Uma planilha 'Conferencias_Dashboards_Portal' é criada no Drive do dono
 *  na primeira gravação (ID guardado em CONFERENCIAS_SHEET_ID). Uma aba
 *  por dashboard: conf_<chave>. Colunas: k | v
 *    k = identificador da marca (definido pelo dashboard)
 *    v = situação da marca em JSON, ex.: {"e":"ok"} (definida pelo dashboard)
 *  Não se grava quem marcou nem quando: só a situação do botão.
 * ------------------------------------------------------------------ */

function abaConferencias_(chave) {
  const email = usuarioAtual_();
  if (!DASHBOARDS[chave] || !email || !temAcesso_(email, chave)) throw new Error('Sem acesso a este dashboard.');
  const props = PropertiesService.getScriptProperties();
  let id = props.getProperty('CONFERENCIAS_SHEET_ID');
  let ss;
  if (id) {
    ss = SpreadsheetApp.openById(id);
  } else {
    ss = SpreadsheetApp.create('Conferencias_Dashboards_Portal');
    props.setProperty('CONFERENCIAS_SHEET_ID', ss.getId());
  }
  const nome = 'conf_' + chave;
  let aba = ss.getSheetByName(nome);
  if (!aba) {
    aba = ss.insertSheet(nome);
    aba.getRange(1, 1, 1, 2).setValues([['k', 'v']]).setFontWeight('bold');
    aba.setFrozenRows(1);
  }
  return aba;
}

function lerConferencias_(aba) {
  const n = aba.getLastRow() - 1;
  if (n < 1) return [];
  return aba.getRange(2, 1, n, 4).getValues().map(function (r) {
    return { k: String(r[0]), v: String(r[1]), por: '', em: '' };
  });
}

/** Devolve todas as marcas do dashboard: [{k, v}] (por/em vêm vazios) */
function api_conf_ler(chave) {
  return lerConferencias_(abaConferencias_(chave));
}

/** Grava marcas. itens: [{k, v}]; v = null remove a marca. Devolve a lista completa atualizada. */
function api_conf_salvar(chave, itens) {
  const aba = abaConferencias_(chave);
  const lock = LockService.getScriptLock();
  lock.waitLock(30000);
  try {
    const atuais = lerConferencias_(aba);
    const mapa = {};
    atuais.forEach(function (x) { mapa[x.k] = x; });
    (itens || []).forEach(function (it) {
      const k = String(it.k);
      if (it.v === null || it.v === undefined) delete mapa[k];
      else mapa[k] = { k: k, v: String(it.v), por: '', em: '' };   // só a situação é guardada, sem quem/quando
    });
    const lista = Object.keys(mapa).map(function (k) { return mapa[k]; });
    if (aba.getLastRow() > 1) aba.getRange(2, 1, aba.getLastRow() - 1, 4).clearContent();
    if (lista.length) {
      aba.getRange(2, 1, lista.length, 2).setValues(lista.map(function (x) { return [x.k, x.v]; }));
    }
    return lista;
  } finally {
    lock.releaseLock();
  }
}

/** Lista os arquivos-base do dashboard: [{arquivo, relPath, mtime, linhas}] */
function api_listar(chave) {
  const m = lerJson_(pastaDados_(chave), 'manifest.json');
  return { geradoEm: m.geradoEm, arquivos: m.arquivos };
}

/** Devolve {abas: {nomeDaAba: [[linha], ...]}} de um arquivo listado no manifesto. */
function api_ler(chave, arquivo) {
  const pasta = pastaDados_(chave);
  const m = lerJson_(pasta, 'manifest.json');
  const ok = m.arquivos.some(function (a) {
    return a.arquivo === arquivo || (a.partes && a.partes.indexOf(arquivo) >= 0);
  });
  if (!ok) throw new Error('Arquivo não pertence ao manifesto.');
  return lerJson_(pasta, arquivo);
}
