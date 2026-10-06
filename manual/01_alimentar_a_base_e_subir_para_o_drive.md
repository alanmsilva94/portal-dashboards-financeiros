# Manual do Portal Financeiro — Parte 1
## Como alimentar a base de dados e subir para o Google Drive

**Para quem é:** quem atualiza os dados dos dashboards (Controladoria).
**Tempo médio:** 5 a 10 minutos por atualização.
**Frequência:** sempre que os Excel da rede mudarem (por exemplo, toda semana).

---

## 1. Entenda o caminho dos dados (30 segundos)

```
 Excel na rede  ──►  Script (exportar.bat)  ──►  Pasta no seu computador  ──►  Google Drive  ──►  Dashboard
 (você atualiza)     converte para JSON          dados_para_drive            (você envia)        (abre sozinho)
```

- O dashboard **não lê o Excel da rede**. Ele lê arquivos **JSON** que ficam no Google Drive.
- O **script** faz a conversão Excel → JSON para você.
- Depois você **envia** os JSON para o Drive. Isso é o que "atualiza" o portal.
- O dashboard mostra o horário em **"Dados de dd/mm/aaaa hh:mm"** (menu lateral, "Status da Sincronização"). Se esse horário mudou, a atualização funcionou.

> Você só mexe em dois lugares: **nos Excel** e **no Drive**. Todo o resto é automático.

---

## 2. De onde vem cada dashboard

| Dashboard | Pasta do Excel (rede) | Arquivo(s) lido(s) | Pasta no Drive |
|---|---|---|---|
| Análise Semanal | `Analise_Semanal\bd` | todos os `.xlsx` | `analise_semanal` |
| Cartões Corporativos | `Cartoes_Corporativos\Projeto_Web_Cartões` | `base_de_dados.xlsx` | `cartoes` |
| Fluxo de Caixa | `Fluxo_de_Caixa\bd` | todos os `.xlsx` (Entradas e Saídas por ano) | `fluxo_de_caixa` |
| Máquinas de Cartões | `Maquinas_Maquinas\bd` | todos os `.xlsx` | `maquinas` |

Todas ficam dentro de `<raiz-dos-dados>\`.

**Regras de ouro dos Excel**
1. **Não mude os nomes das colunas** (primeira linha das planilhas). O dashboard reconhece os dados por esses nomes.
2. **Salve e feche** o Excel antes de rodar o script. Arquivo aberto pode dar erro.
3. Para um **novo ano** (ex.: `Entradas_2027.xlsx`), basta colocar o arquivo na pasta `bd` correspondente. O script encontra sozinho.
4. Não deixe arquivos de teste ou cópias (`Cópia de ...xlsx`) dentro das pastas `bd`: eles seriam lidos também.

---

## 3. Passo a passo — atualização normal

### Passo 1 — Atualize os Excel
Abra o Excel da pasta correspondente, inclua os novos lançamentos, **salve e feche**.

### Passo 2 — Rode o conversor
1. Abra a pasta:
   `...\projeto_final_web\sincronizador`
2. Dê **dois cliques em `exportar.bat`**.
3. Abre uma janela preta com mensagens. Aguarde até aparecer **"Pronto"** e a frase *"Agora envie o conteúdo de cada subpasta..."*.
4. Aperte qualquer tecla para fechar.

**O que esperar na tela:** para cada dashboard, o script mostra se converteu arquivos ou se "nada mudou". Isso é normal: ele **só reconverte o que foi alterado**. Quem não mudou é pulado (por isso é rápido).

### Passo 3 — Veja o que foi gerado
Abra a pasta:
`...\projeto_final_web\dados_para_drive`

Dentro há uma subpasta por dashboard (`analise_semanal`, `cartoes`, `fluxo_de_caixa`, `maquinas`). Em cada uma:
- um ou mais arquivos `.json` com os dados;
- um arquivo **`manifest.json`** (a "lista de conteúdo" com a data/hora da geração). **Ele precisa ser enviado sempre.**

### Passo 4 — Envie para o Google Drive
1. Abra o navegador em **drive.google.com**, com a conta `voce@empresa.exemplo.com`.
2. Entre em **Meu Drive → `Dashboards_Portal_dados`**.
3. Entre na subpasta do dashboard que você atualizou (ex.: `cartoes`).
4. Na outra janela, abra a pasta local do dashboard dentro de `dados_para_drive`, **selecione todos os arquivos** (Ctrl + A) e **arraste** para a janela do Drive.
5. Se o Drive perguntar sobre arquivos que já existem, escolha **Substituir** (ou "Enviar como nova versão"). **Não** escolha "manter ambos".
6. Espere o Drive mostrar "Upload concluído".
7. Repita para cada dashboard que você atualizou.

> Dica: só envie as pastas que mudaram. Se você atualizou apenas os cartões, envie só `cartoes`.

### Passo 5 — Confira no portal
1. Abra o link do portal.
2. Escolha o dashboard atualizado.
3. No menu lateral, veja **"Dados de ..."**: deve mostrar a data/hora **mais recente**.
4. Se estava com o dashboard aberto, clique em **"Atualizar dados"** (menu lateral).
5. Confira se os totais batem com o Excel (ex.: total do mês).

---

## 4. Resumo em uma página (cola)

```
1. Atualizar o Excel e FECHAR
2. sincronizador\exportar.bat  → esperar "Pronto"
3. dados_para_drive\<dashboard>\  → selecionar tudo
4. Arrastar para Drive > Dashboards_Portal_dados > <mesma pasta>   (Substituir!)
5. Portal → "Atualizar dados" → conferir a data/hora
```

---

## 5. Situações especiais

### 5.1 Quero forçar a reconversão de tudo
Use quando suspeitar que algum JSON ficou desatualizado ou corrompido.

Abra o **Prompt de Comando** na pasta `sincronizador` e rode:

```
python exportar_para_drive.py --forcar
```

### 5.2 Quero converter só um dashboard
```
python exportar_para_drive.py --so cartoes
```
Troque `cartoes` por `analise`, `fluxo` ou `maquinas`. Pode combinar: `python exportar_para_drive.py --so fluxo --forcar`.

### 5.3 Mudou a pasta onde ficam os Excel
Abra `sincronizador\config.json` (Bloco de Notas) e ajuste o campo `"origem"` do dashboard. Atenção: no JSON, **barras invertidas são duplas** (`\\`).

### 5.4 Quero que o envio ao Drive seja automático
Instale o **Google Drive para computador**, sincronize a pasta `Dashboards_Portal_dados` e, no `config.json`, aponte `"destino"` para essa pasta sincronizada. Assim o Passo 4 deixa de ser manual. (Podemos configurar isso numa próxima parte do manual.)

---

## 6. Problemas comuns e soluções

| O que aparece | Causa provável | O que fazer |
|---|---|---|
| Janela do `.bat` fecha na hora | Python não instalado ou fora do PATH | Instale o Python (marque "Add to PATH") e rode de novo |
| `No module named 'openpyxl'` | Falta a biblioteca | No Prompt de Comando: `pip install openpyxl` |
| `PermissionError` / erro de arquivo | Excel aberto | Feche o Excel e rode de novo |
| "Pasta de origem não existe" | Rede desconectada ou caminho mudou | Confira o acesso à rede e o `config.json` |
| "nada mudou" mas você alterou o Excel | Esqueceu de **salvar** | Salve, feche e rode de novo (ou use `--forcar`) |
| Portal mostra a data **antiga** | Não enviou o `manifest.json`, ou o envio falhou | Reenvie a pasta inteira e clique em "Atualizar dados" |
| Dashboard com erro "Arquivo de dados não encontrado" | Faltou subir algum `.json` | Compare a pasta local com a do Drive e envie o que faltou |
| Dashboard "Não foi possível carregar" | Pasta do Drive com nome errado | As pastas devem se chamar exatamente: `analise_semanal`, `cartoes`, `fluxo_de_caixa`, `maquinas` |
| Números diferentes do Excel | Coluna renomeada ou linha de total no meio dos dados | Corrija a planilha e converta de novo |
| Duas cópias do mesmo arquivo no Drive | Foi escolhido "manter ambos" | Sem problema: o portal usa a cópia **mais recente**. Pode apagar a antiga |
| Máquinas de Cartões demora para abrir | Base grande (~230 mil linhas) | Normal: aguarde alguns segundos |

---

## 7. Cuidados

- **Não compartilhe** a pasta `Dashboards_Portal_dados` do Drive com ninguém. O portal acessa os dados como **dono** da pasta; quem libera o acesso é o próprio portal.
- **Não renomeie** nem **mova** a pasta `Dashboards_Portal_dados` ou suas subpastas.
- **Não edite** os `.json` à mão.
- Antes de uma mudança grande nos Excel, guarde uma cópia da pasta `bd`.

---

## 8. Checklist de cada atualização

- [ ] Excel atualizado, **salvo e fechado**
- [ ] `exportar.bat` executado e terminou em "Pronto"
- [ ] Arquivos da subpasta enviados ao Drive (inclusive `manifest.json`), escolhendo **Substituir**
- [ ] Portal aberto e **"Atualizar dados"** clicado
- [ ] Data/hora em "Dados de ..." está atual
- [ ] Um total conferido contra o Excel

---

*Próximas partes sugeridas: 2) Como usar cada dashboard · 3) Conferências (Pendente / Autorizado / Verificar) · 4) Como publicar uma nova versão no Apps Script · 5) Como dar acesso a outra pessoa · 6) Solução de problemas.*
