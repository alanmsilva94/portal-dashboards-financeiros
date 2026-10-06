/**
 * Quem pode entrar e em quais dashboards.
 * - Use ['*'] para liberar todos os dashboards, ou liste as chaves: 'analise', 'cartoes', 'fluxo', 'maquinas'.
 * - E-mails em minúsculas.
 * - LIBERAR_DOMINIO: se não estiver vazio, qualquer e-mail desse domínio que NÃO esteja na lista
 *   entra com os dashboards de DASHBOARDS_PADRAO.
 */
const ACESSOS = {
  'voce@empresa.exemplo.com': ['*']
  // 'fulano@empresa.exemplo.com': ['analise', 'fluxo'],
};

const LIBERAR_DOMINIO = '';                 // ex.: '@empresa.exemplo.com' (deixe '' para só quem está na lista)
const DASHBOARDS_PADRAO = [];               // ex.: ['analise']

function temAcesso_(email, chave) {
  email = String(email || '').toLowerCase();
  let lista = ACESSOS[email];
  if (!lista && LIBERAR_DOMINIO && email.slice(-LIBERAR_DOMINIO.length) === LIBERAR_DOMINIO) lista = DASHBOARDS_PADRAO;
  if (!lista) return false;
  if (!chave) return true;                  // entrar no portal
  return lista.indexOf('*') >= 0 || lista.indexOf(chave) >= 0;
}
