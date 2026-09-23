# Triby - Automação Multicanal (Gmail + WhatsApp)

Projeto integrado de prospecção e comunicação para captação e diagnóstico estratégico:

---

## 📁 Estrutura do Projeto

### 1. 📧 [Pasta `gmail/`](file:///c:/Users/Pietro/triby/gmail)
Automação de e-mails conectada ao **Google Workspace** e **Google Sheets**:
- Conectado à planilha unificada de Leads e Respostas de Formulário.
- Disparo de 1 e-mail por minuto (cadência anti-spam) com templates segmentados por CNAE.
- Preenchimento automático na planilha da coluna **"Hora de Envio"** (`xx/xx/xxxx às yy:yy`).
- Atualização do **"Status do Contato"** para **`Em Contato`** no envio e **`Diagnóstico Aceito`** quando o lead responde ao formulário.
- Monitoramento contínuo de respostas dos leads na caixa de entrada do Gmail.
- Templates formatados em HTML e texto puro para a **Valor Fiscal**.
- Scripts prontos: `run_mvp_10.bat`, `run_loop.bat`, `run_once.bat`, `test_connection.bat`.

### 2. 💬 [Pasta `whatsapp/`](file:///c:/Users/Pietro/triby/whatsapp)
Conexão direta com o **WhatsApp** via biblioteca **Baileys**:
- Pareamento sem QR Code através de **Código de Pareamento de 8 dígitos** para o celular `+55 11 99410-3374`.
- Reconexão automática em caso de oscilação de rede.
- Sessão persistida em `auth_info_baileys/`.
- Módulo para envio de mensagens e escuta de novas mensagens recebidas.
- Servidor API HTTP interno na porta `3001` para envio desacoplado.
- Scripts prontos: `start.bat`, `disparar_barsi.bat`.

### 3. 🎯 Skill: Disparo para Grupos WhatsApp - Barsi
Skill Antigravity configurada em [`.agent/skills/disparo-grupos-barsi/`](file:///c:/Users/Pietro/triby/.agent/skills/disparo-grupos-barsi):
- Envio automatizado nos **13 grupos de WhatsApp** (JP Networking Black, Construindo uma Startup #2, ACE NET, etc.).
- Controle de cadência inteligente anti-spam (padrão 10s configurável).
- Suporte a modo `--dry-run` para testes e relatórios de auditoria em `whatsapp/disparo_logs/`.

