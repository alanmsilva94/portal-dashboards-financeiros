# Portal de Dashboards Financeiros

Portal web em **Google Apps Script** que reúne quatro dashboards financeiros (análise semanal de pagamentos, cartões corporativos, fluxo de caixa e máquinas de cartões) atrás de um único login, com página inicial, menu lateral, tema claro/escuro e controle de acesso por e-mail.

Todo o front-end é **HTML, CSS e JavaScript puros** (sem frameworks de interface). Os dados vêm de planilhas Excel, convertidas em JSON por um script Python e lidas pelo portal a partir do Google Drive.

> **Dados 100% fictícios.** Este repositório não contém nenhum dado real. As planilhas de exemplo são geradas por script (`gerar_dados_exemplo.py`) e qualquer semelhança com pessoas, empresas ou valores é coincidência.

## Funcionalidades

- **Login e controle de acesso** por e-mail Google, com lista de usuários e dashboards liberados por pessoa (`Acessos.gs`).
- **Página inicial** com a escolha do dashboard e resumo da situação dos dados.
- **Menu lateral compartilhado** (shell único): navegação entre dashboards, abas internas, filtros, busca, exportação e tema claro/escuro.
- **4 dashboards**:
  - *Análise Semanal*: pagamentos por semana, beneficiário, banco e departamento, com alertas por limite e conferência (Pendente / Autorizado / Verificar).
  - *Cartões Corporativos*: gastos por bandeira, natureza e departamento, árvore de decomposição, lançamentos paginados e exportação CSV.
  - *Fluxo de Caixa*: entradas, saídas, resultado operacional, setores e histórico, com gráficos interativos e tooltips.
  - *Máquinas de Cartões*: receita por máquina, localidade e estado.
- **Conferências compartilhadas** gravadas em uma planilha Google (somente o estado da marcação, sem registrar quem marcou).
- **Sincronizador Python**: converte os Excel em JSON (só o que mudou) e gera a pasta pronta para subir ao Drive.
- **Simulador local** para testar os dashboards sem publicar no Apps Script.
- **KPIs animados**, layout responsivo e acessível (foco visível, respeito a "reduzir movimento").

## Arquitetura

```
Excel (rede)  --exportar_para_drive.py-->  JSON no Google Drive  --Apps Script-->  Dashboard (navegador)
```

```
portal-dashboards-financeiros/
├── apps_script/           código publicado em script.google.com
│   ├── Code.gs            rotas (?p=), API de dados e de conferências
│   ├── Acessos.gs         quem entra e em quais dashboards
│   ├── shell_portal.html  layout compartilhado (CSS/JS puros)
│   ├── portal_dados.html  leitura dos JSON do Drive (google.script.run)
│   ├── portal_logo.html   logo de exemplo (placeholder)
│   ├── home.html, login.html, negado.html
│   └── dash_*.html        os 4 dashboards (+ partes)
├── sincronizador/         roda no seu computador
│   ├── exportar_para_drive.py
│   ├── config.json        pastas de origem/destino
│   └── reducers/          agregações para reduzir o tamanho dos JSON
├── _teste/harness.py      simulador local do Apps Script
├── dados_exemplo/         JSON fictícios prontos para o simulador
└── manual/                guias passo a passo
```

## Como executar

### 1. Teste local (sem Google, com dados de exemplo)

Requisito: Python 3.10+ (o simulador usa só a biblioteca padrão).

```bash
cd _teste
python harness.py fluxo --dados ../dados_exemplo --porta 8765
# abra http://localhost:8765/
```

Chaves disponíveis: `home`, `analise`, `cartoes`, `fluxo`, `maquinas`. A pasta `dados_exemplo/` já traz os JSON fictícios no formato que o portal lê. Para gerar os seus próprios: coloque os Excel nas pastas indicadas em `sincronizador/config.json` e rode `python exportar_para_drive.py --destino ../dados_para_drive` (requer `pip install openpyxl`).

Os quatro dashboards também existem como projetos independentes, com planilhas de exemplo e gerador de dados fictícios: *dashboard-analise-semanal*, *dashboard-cartoes-corporativos*, *dashboard-fluxo-de-caixa* e *dashboard-maquinas-cartoes*.

### 2. Publicar no Google Apps Script

1. Crie um projeto em [script.google.com](https://script.google.com) e copie os arquivos de `apps_script/`.
2. Em *Configurações do projeto → Propriedades do script*, crie `PASTA_DADOS_ID` com o ID da pasta do Drive que receberá os JSON.
3. Edite `Acessos.gs` com os e-mails autorizados.
4. *Implantar → Nova implantação → App da Web*: executar como **Eu**, acesso conforme sua necessidade.
5. Suba os JSON gerados para a pasta do Drive (uma subpasta por dashboard).

Os guias em [`manual/`](manual/) detalham a atualização dos dados e a liberação de acesso.

## Tecnologias

Google Apps Script (HtmlService, DriveApp, SpreadsheetApp, LockService) · HTML5 · CSS3 (variáveis, `color-mix`, grid) · JavaScript (ES2020) · Chart.js · Plotly.js · SheetJS · Python 3 (openpyxl)

## Segurança e privacidade

- Nenhum dado real, e-mail, ID de planilha/pasta ou chave consta no repositório.
- O acesso é validado no servidor (`Session.getActiveUser()` + `Acessos.gs`), não apenas no navegador.
- Os dados ficam no Drive do dono do projeto; os usuários não precisam de acesso à pasta.

## Licença

MIT — veja [LICENSE](LICENSE).
