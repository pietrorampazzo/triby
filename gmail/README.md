# Disparador de Leads & Monitor de Respostas (Google Workspace)

Sistema completo em Python integrado ao **Gmail** e **Google Sheets** para envio cadenciado de e-mails para leads, atualização automática da planilha e monitoramento de respostas na caixa de entrada.

---

## 📋 Funcionalidades

1. **Leitura Inteligente da Planilha:**
   - Conecta-se à planilha: `https://docs.google.com/spreadsheets/d/1V3W0KME53VqjGlhaFudJ2IkcmI0MlzPAoaJ4ZszSu9s/`
   - Seleciona automaticamente a aba correta através do GID `421539945`.
   - Identifica dinamicamente as colunas necessárias (`E-mail`, `Nome`, `Empresa`, `Hora de Envio`, `Status do Contato`).

2. **Envio Cadenciado (Anti-Spam):**
   - Envia **1 e-mail por vez a cada 1 minuto** (60 segundos).
   - Suporte a templates modernos em **HTML** e **Texto Puro (fallback)**.
   - Variáveis dinâmicas: `{nome}`, `{empresa}`, `{email}`, etc.

3. **Atualização Automática na Planilha:**
   - **Hora de Envio:** Preenche rigorosamente no padrão `"xx/xx/xxxx às yy:yy"` (ex: `22/09/2026 às 17:35`).
   - **Status do Contato:** Atualiza para **`Em Contato`** (respeitando a lista suspensa da planilha).

4. **Monitoramento Ativo da Caixa de Entrada:**
   - A cada ciclo, consulta a caixa de entrada do Gmail para detectar se leads que já foram contatados responderam.
   - Exibe alertas com trecho da mensagem, data, assunto e remetente.

5. **Modos de Execução:**
   - **Modo Loop (`--mode loop`):** Roda continuamente no terminal com pausas de 1 minuto entre disparos.
   - **Modo Único (`--mode once`):** Executa 1 disparo e checagem e encerra (ideal para Agendador de Tarefas do Windows ou Cron do Linux a cada 1 minuto).
   - **Modo Teste (`--test`):** Valida conexões, colunas e permissões sem disparar e-mails.

---

## 🛠️ Passo a Passo para Configuração Inicial

### 1. Obter o arquivo `credentials.json` no Google Cloud

Para que o script acesse sua conta Google Workspace com segurança:

1. Acesse o [Google Cloud Console](https://console.cloud.google.com/).
2. Crie um novo projeto (ou selecione um existente).
3. Vá em **APIs e Serviços** > **Biblioteca**:
   - Pesquise por **Google Sheets API** e clique em **Ativar**.
   - Pesquise por **Gmail API** e clique em **Ativar**.
4. Vá em **APIs e Serviços** > **Tela de permissão OAuth**:
   - Escolha **Externo** (ou Interno se tiver Google Workspace Corporativo).
   - Preencha o nome do app (ex: `Disparador Triby`) e seu e-mail.
   - Na aba **Usuários de teste**, adicione o seu e-mail do Gmail / Workspace.
5. Vá em **APIs e Serviços** > **Credenciais**:
   - Clique em **+ Criar Credenciais** > **ID do cliente OAuth**.
   - Tipo de aplicativo: selecione **Aplicativo para Computador (Desktop App)**.
   - Nome: `Triby Desktop Client`.
   - Clique em **Criar** e depois em **Baixar JSON**.
6. Renomeie o arquivo baixado para **`credentials.json`** e coloque-o nesta pasta:
   ```
   c:\Users\Pietro\triby\credentials.json
   ```

---

### 2. Primeira Execução e Autorização

Execute o arquivo de teste:
- Dê dois cliques em **`test_connection.bat`**, ou no terminal:
  ```powershell
  .venv\Scripts\python.exe main.py --test
  ```
- O navegador abrirá automaticamente para você fazer login na sua conta Google e conceder permissão de envio de e-mails e leitura de planilhas.
- Após autorizar, o arquivo **`token.json`** será salvo na pasta. **Você só precisará fazer isso uma única vez!** A partir de então, tudo funciona de forma 100% autônoma.

---

## 🚀 Como Executar

### Opção A: Execução Contínua em Segundo Plano / Terminal (Recomendado)
Para deixar rodando enviando 1 e-mail por minuto e checando respostas:
- Dê dois cliques em **`run_loop.bat`**, ou no terminal:
  ```powershell
  .venv\Scripts\python.exe main.py --mode loop
  ```
- O script exibirá o progresso a cada ciclo e aguardará 60 segundos antes de enviar o próximo lead.
- Para parar a qualquer momento: pressione **`Ctrl + C`**.

---

### Opção B: Agendador de Tarefas do Windows (Cron a cada 1 minuto)
Se preferir que o próprio Windows dispare o script a cada 1 minuto:
1. Abra o **Agendador de Tarefas** do Windows (`taskschd.msc`).
2. Clique em **Criar Tarefa Básica**.
3. Nome: `Disparador de Leads Triby`.
4. Disparador: **Diariamente** (em opções avançadas, configure para "Repetir a cada 1 minuto" durante 1 dia).
5. Ação: **Iniciar um programa**:
   - Programa/script: `c:\Users\Pietro\triby\.venv\Scripts\python.exe`
   - Adicionar argumentos: `main.py --mode once`
   - Iniciar em: `c:\Users\Pietro\triby`
6. Salvar.

---

### Opção C: Apenas Monitorar Respostas (Sem Enviar E-mails)
Para rodar uma checagem pontual apenas para ver se algum lead respondeu:
```powershell
.venv\Scripts\python.exe main.py --check-only
```

---

## ✉️ Personalização dos Templates de E-mail

Os modelos de mensagens ficam na pasta `templates/`:
- **`templates/email_template.html`**: Layout HTML com fontes e design profissional.
- **`templates/email_template.txt`**: Versão texto puro (enviada em conjunto para clientes de e-mail que preferem texto puro).

### Variáveis Disponíveis:
- `{nome}`: Primeiro nome do lead (ex: `Pietro`).
- `{nome_completo}`: Nome completo preenchido na planilha.
- `{empresa}`: Nome da empresa do lead.
- `{email}`: E-mail de destino.
- `{remetente}`: Seu nome configurado no `.env`.
- Qualquer outra coluna presente na planilha pode ser usada colocando `{nome_da_coluna}`.

---

## ⚙️ Configurações (`.env`)

Você pode editar o arquivo `.env` para ajustar parâmetros a qualquer momento:

```env
SPREADSHEET_ID=1V3W0KME53VqjGlhaFudJ2IkcmI0MlzPAoaJ4ZszSu9s
SHEET_GID=421539945
INTERVAL_SECONDS=60
TIMEZONE=America/Sao_Paulo
EMAIL_SUBJECT=Oportunidade e Diagnóstico Estratégico para {empresa}
SENDER_NAME=Pietro
COL_SEND_TIME=Hora de Envio
COL_STATUS=Status do Contato
```
