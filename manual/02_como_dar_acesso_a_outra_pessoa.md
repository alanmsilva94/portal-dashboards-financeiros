# Manual do Portal Financeiro — Parte 2
## Como dar acesso a outra pessoa

**Para quem é:** o administrador do portal (dono do projeto no Apps Script).
**Tempo médio:** 5 minutos por pessoa.
**Pré-requisito:** a pessoa precisa ter e-mail **@empresa.exemplo.com** (conta Google da organização).

---

## 1. Entenda como o acesso funciona (1 minuto)

O acesso é controlado em **duas camadas**. A pessoa só entra se passar pelas duas.

```
 Pessoa abre o link
        │
        ▼
 ┌───────────────────────────────┐
 │ CAMADA 1 — Google             │   Configurada na IMPLANTAÇÃO do Apps Script
 │ "Quem pode abrir o link?"     │   (Somente eu  /  Qualquer pessoa da organização)
 └───────────────┬───────────────┘
                 ▼
 ┌───────────────────────────────┐
 │ CAMADA 2 — Portal Financeiro        │   Configurada no arquivo Acessos.gs
 │ "Este e-mail está na lista?   │   (lista de e-mails e dashboards liberados)
 │  Para quais dashboards?"      │
 └───────────────┬───────────────┘
                 ▼
        Dashboard liberado
```

- **Camada 1** decide se o Google deixa a pessoa chegar ao portal. Hoje está em **"Somente eu"**: só você abre o link.
- **Camada 2** decide **o que** a pessoa vê. Mesmo que o Google deixe a pessoa entrar, se o e-mail dela **não estiver** em `Acessos.gs`, ela vê a tela **"Acesso não liberado"**.
- A pessoa **não precisa** de acesso à pasta de dados no seu Drive. O portal lê os dados com a **sua** conta ("Executar como Eu").
- Seu computador **não precisa estar ligado**: o portal roda nos servidores do Google.

---

## 2. Antes de começar — decida

| Pergunta | Opções |
|---|---|
| Quem vai receber acesso? | O e-mail @empresa.exemplo.com da pessoa |
| Quais dashboards ela verá? | **Todos** ou só alguns: `analise`, `cartoes`, `fluxo`, `maquinas` |

**Nomes (chaves) dos dashboards**

| Dashboard | Chave |
|---|---|
| Análise Semanal | `analise` |
| Cartões Corporativos | `cartoes` |
| Fluxo de Caixa | `fluxo` |
| Máquinas de Cartões | `maquinas` |

---

## 3. Passo a passo

### Passo 1 — Abrir o projeto
1. Acesse **script.google.com** com a conta `voce@empresa.exemplo.com`.
2. Abra o projeto **Portal Financeiro**.
3. Na lista de arquivos (lado esquerdo), clique em **`Acessos.gs`**.

### Passo 2 — Incluir a pessoa na lista
O arquivo tem este bloco:

```javascript
const ACESSOS = {
  'voce@empresa.exemplo.com': ['*']
  // 'fulano@empresa.exemplo.com': ['analise', 'fluxo'],
};
```

Adicione **uma linha por pessoa**, seguindo o modelo.

**Exemplo A — liberar só alguns dashboards**
```javascript
const ACESSOS = {
  'voce@empresa.exemplo.com': ['*'],
  'maria.silva@empresa.exemplo.com': ['analise', 'fluxo']
};
```

**Exemplo B — liberar todos os dashboards**
```javascript
const ACESSOS = {
  'voce@empresa.exemplo.com': ['*'],
  'joao.souza@empresa.exemplo.com': ['*']
};
```

**Exemplo C — várias pessoas**
```javascript
const ACESSOS = {
  'voce@empresa.exemplo.com': ['*'],
  'maria.silva@empresa.exemplo.com': ['analise', 'fluxo'],
  'joao.souza@empresa.exemplo.com': ['cartoes'],
  'ana.lima@empresa.exemplo.com': ['*']
};
```

**Regras de escrita (onde mais se erra)**
1. **E-mail todo em letras minúsculas**, entre aspas simples `' '`.
2. **Vírgula no fim de cada linha**, **exceto na última** (a última fica sem vírgula).
3. Dashboards entre colchetes `[ ]`, cada um entre aspas, separados por vírgula.
4. `['*']` significa **todos** os dashboards.
5. Não apague as chaves `{ }` nem o ponto e vírgula `;` do final.

### Passo 3 — Salvar
Clique no ícone de **disquete** (Salvar) na barra de cima, ou use **Ctrl + S**. Espere a mensagem "Projeto salvo".

### Passo 4 — Publicar uma nova versão
Salvar **não basta**: o link principal só passa a valer depois de publicar.

1. Clique em **Implantar → Gerenciar implantações**.
2. Na implantação ativa, clique no **lápis** (Editar).
3. No campo **Versão**, escolha **Nova versão**.
4. No campo **Descrição**, escreva um nome claro, por exemplo: `Portal Financeiro v8 - acesso Maria Silva`.
5. Clique em **Implantar** e depois em **Concluído**.

> O **link não muda**: continua o mesmo de antes.

### Passo 5 — Liberar a Camada 1 (apenas na primeira vez que der acesso a alguém)
Se o portal estiver em **"Somente eu"**, a pessoa **não consegue nem abrir o link**. Para permitir:

1. **Implantar → Gerenciar implantações → lápis (Editar)**.
2. Em **Configuração**, localize **"Quem pode acessar"**.
3. Troque de **"Somente eu"** para **"Qualquer pessoa da organização empresa.exemplo.com"**.
4. Mantenha **"Executar como": Eu**. **Não mude isso.**
5. Clique em **Implantar**.

> Mesmo com o link aberto para a organização, só entra quem estiver em `Acessos.gs`. Os demais veem "Acesso não liberado".
>
> Esse passo só é necessário **uma vez**. Para as próximas pessoas, basta repetir os Passos 1 a 4.

### Passo 6 — Avisar a pessoa e testar
1. Envie o **link do portal** (o que termina em `/exec`).
2. Peça para ela abrir **logada na conta @empresa.exemplo.com**.
3. Na **primeira vez**, o Google pode pedir uma confirmação de acesso. É normal.
4. Peça para conferir se aparecem **apenas** os dashboards que você liberou no menu lateral.

---

## 4. Resumo em uma página (cola)

```
1. script.google.com → Portal Financeiro → Acessos.gs
2. Incluir:  'email@empresa.exemplo.com': ['analise','fluxo'],     (ou ['*'] para todos)
3. Salvar (Ctrl+S)
4. Implantar → Gerenciar implantações → lápis → Nova versão → Descrição → Implantar
5. (1ª vez) "Quem pode acessar" → Qualquer pessoa da organização empresa.exemplo.com
6. Enviar o link /exec e confirmar com a pessoa
```

---

## 5. Outras tarefas comuns

### 5.1 Mudar os dashboards de uma pessoa
Edite a linha dela em `Acessos.gs`, ajuste os dashboards, salve e publique uma **Nova versão** (Passo 4).

### 5.2 Tirar o acesso de uma pessoa
Apague a **linha inteira** dela em `Acessos.gs` (cuidado com a vírgula da linha anterior), salve e publique uma **Nova versão**. A partir daí ela vê "Acesso não liberado".

### 5.3 Liberar todo mundo da organização (opção avançada)
No mesmo arquivo há duas configurações:

```javascript
const LIBERAR_DOMINIO = '';          // ex.: '@empresa.exemplo.com'
const DASHBOARDS_PADRAO = [];        // ex.: ['analise']
```

Se você preencher `LIBERAR_DOMINIO = '@empresa.exemplo.com'` e `DASHBOARDS_PADRAO = ['analise']`, **qualquer pessoa** com e-mail @empresa.exemplo.com que **não esteja na lista** entrará vendo só o Análise Semanal. Quem está na lista continua com o que foi definido para ela.

> **Cuidado:** use só se quiser mesmo abrir para toda a organização. Por segurança, o padrão é deixar vazio.

### 5.4 Ver quem tem acesso hoje
Abra `Acessos.gs`: a lista de e-mails dentro de `ACESSOS` é a lista completa.

---

## 6. Problemas comuns e soluções

| O que aparece | Causa provável | O que fazer |
|---|---|---|
| Google mostra "Você precisa de acesso" / "Sem permissão" | Camada 1 em "Somente eu" | Faça o **Passo 5** |
| Portal mostra **"Acesso não liberado"** com o e-mail da pessoa | E-mail não está em `Acessos.gs`, ou foi digitado diferente | Confira o e-mail (minúsculas, sem espaço) e publique **Nova versão** |
| "Acesso não liberado" para **um** dashboard | Dashboard não está na lista dela | Inclua a chave certa (`analise`, `cartoes`, `fluxo`, `maquinas`) |
| Mensagem "Não foi possível identificar sua conta" | Pessoa não está logada em conta @empresa.exemplo.com | Entrar com o e-mail da organização e abrir o link de novo |
| Salvei, mas nada mudou para a pessoa | Faltou publicar **Nova versão** | Refaça o **Passo 4** |
| Erro de sintaxe ao salvar o `Acessos.gs` | Vírgula faltando ou sobrando, aspa aberta | Confira as regras de escrita do Passo 2 |
| Pessoa vê o dashboard mas **sem dados** | Pasta de dados do Drive com problema | Veja o manual da Parte 1 (conferir pastas e envio ao Drive) |
| Pessoa de **fora** da organização não entra | O portal é só para @empresa.exemplo.com | Não é possível liberar e-mails de outros domínios com a configuração atual |

---

## 7. Cuidados de segurança

- **Dê acesso só a quem precisa**, e só aos dashboards necessários. Prefira listas específicas em vez de `['*']`.
- **Nunca** compartilhe a pasta `Dashboards_Portal_dados` nem a planilha `Conferencias_Dashboards_Portal` do seu Drive. O portal já lê os dados por você.
- **Mantenha "Executar como: Eu"**. Se mudar para "Usuário que acessa", cada pessoa precisaria de acesso direto à pasta de dados e o portal deixaria de funcionar para ela.
- Ao **desligar** alguém da empresa, remova o e-mail de `Acessos.gs` e publique **Nova versão**.
- Quem tem acesso ao dashboard **pode alterar as conferências** (Pendente / Autorizado / Verificar com o departamento) da Análise Semanal. Considere isso ao liberar.
- Guarde um **backup** (pasta `backups`) antes de mudar `Acessos.gs` em lote.

---

## 8. Checklist de cada liberação

- [ ] E-mail @empresa.exemplo.com da pessoa confirmado (minúsculas)
- [ ] Dashboards definidos (`'*'` ou lista)
- [ ] Linha incluída em `Acessos.gs` (sem erro de vírgula)
- [ ] Salvo (Ctrl + S)
- [ ] **Nova versão** publicada, com Descrição
- [ ] (1ª vez) "Quem pode acessar" ajustado para a organização
- [ ] Link `/exec` enviado e pessoa testou
- [ ] Menu lateral dela mostra só o que deveria

---

*Próximas partes sugeridas: 3) Como usar cada dashboard · 4) Conferências (Pendente / Autorizado / Verificar) · 5) Como publicar uma nova versão no Apps Script · 6) Solução de problemas.*
