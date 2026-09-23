---
name: disparo-grupos-barsi
description: >-
  Disparo automatizado e seguro de mensagens nos 13 grupos de WhatsApp da estratégia e campanha Barsi, incluindo JP Networking, ACE NET, Construindo uma Startup e outros, com controle de intervalo anti-spam e relatórios de auditoria.
---

# Disparo para Grupos WhatsApp - Barsi

Skill para envio da campanha oficial de convite do **Método Barsi - Dividendos Inteligentes** (imagem + legenda) para os 13 grupos de networking e negócios configurados no WhatsApp da Triby.

---

## 🖼️ Imagem e Mensagem Oficial

- **Imagem Anexa:** [`whatsapp/assets/barsi_dividendos_inteligentes.jpg`](file:///c:/Users/Pietro/triby/whatsapp/assets/barsi_dividendos_inteligentes.jpg) *(Barsi Investimentos \| XP - Relatório Dividendos Inteligentes)*
- **Template da Legenda:** [`whatsapp/templates/barsi_convite_legenda.txt`](file:///c:/Users/Pietro/triby/whatsapp/templates/barsi_convite_legenda.txt)

```text
📊 MÉTODO BARSI - DIVIDENDOS INTELIGENTES 📊

Olá, pessoal! Quer aprender a investir seguindo o método do maior investidor pessoa física da nossa Bolsa? 🇧🇷💼

Gostaria de convidar todos a participarem do nosso grupo exclusivo de investimentos, onde aplicamos na prática a filosofia do *Luiz Barsi* :

✅ Foco em empresas sólidas e perenes
✅ Compra de ações a preços atrativos (Margem de Segurança)
✅ Foco total em dividendos recorrentes e geração de renda futura 📈
✅ Assessoria gratuita para clientes XP Investimentos. Mude sua assessoria hoje mesmo!

No grupo compartilhamos análises de mercado, carteiras recomendadas de dividendos e oportunidades em primeira mão. Convide um amigo, e ganhe uma sessão de *Planejamento Financeiro*!

Para fazer parte gratuitamente, basta entrar pelo link abaixo:
👉 https://chat.whatsapp.com/I24xxVtUroc0QM5uHxXpvA

Bons investimentos! 📈✨
```

---

## 📋 13 Grupos Alvo

| # | Nome do Grupo | WhatsApp JID | Status |
|---|---|---|---|
| 1 | JP Networking Black ♟️ | `120363328129100867@g.us` | Mantido |
| 2 | Construindo uma Startup #2 | `120363419625067096@g.us` | Mantido |
| 3 | ACE NET BUSINESS | `5511975922582-1592239710@g.us` | Mantido |
| 4 | ILUMINANDO CONEXÕES | `120363423341501332@g.us` | Mantido |
| 5 | Lojistas de Direita 🇧🇷 | `5512981128451-1583502334@g.us` | Mantido |
| 6 | The Society Creator Comun. | `120363422261662575@g.us` | Mantido |
| 7 | Ais Livres Vl | `5511992226744-1611263507@g.us` | Mantido |
| 8 | NJE - Núcleo Jovem GRU | `120363025686868832@g.us` | Mantido |
| 9 | Comunidade Agentes Apex | `120363043969599077@g.us` | Mantido |
| 10 | MBr - Hub SP São Paulo | `5511996099012-1525906925@g.us` | Mantido |
| 11 | ASSEAG ACADEMY | `120363171953633718@g.us` | Mantido |
| 12 | ® Registro de MARCAS & PATENTES 🔐 🇧🇷🌎 | `5511964502842-1569532703@g.us` | Mantido |
| 13 | JP Memeworking | `5521971413564-1599916186@g.us` | Novo ✨ |

---

## 🚀 Comandos de Execução

### Pelo Terminal:

```bash
cd c:\Users\Pietro\triby\whatsapp

# 1. Simulação sem envio real (teste e verificação de grupos):
node disparo_barsi.js --dry-run

# 2. Disparo real com imagem + texto nos 13 grupos:
node disparo_barsi.js

# 3. Disparo com intervalo anti-spam customizado (ex: 20 segundos):
node disparo_barsi.js --delay 20

# 4. Disparo sem imagem (somente texto):
node disparo_barsi.js --no-image

# 5. Disparar apenas para um grupo específico pelo ID (ex: Grupo 1):
node disparo_barsi.js --group 1

# 6. Listar grupos cadastrados:
node disparo_barsi.js --list
```

### Pelo Atalho Windows (1 Clique):
Execute o arquivo:
👉 [`whatsapp/disparar_barsi.bat`](file:///c:/Users/Pietro/triby/whatsapp/disparar_barsi.bat)

---

## 🛡️ Políticas e Segurança

- **Intervalo Anti-Spam:** Padrão de 15 segundos entre envios.
- **Relatório de Auditoria:** Salvo em `whatsapp/disparo_logs/` com carimbo de data/hora e status individual por grupo.
- **Conexão Baileys:** Utiliza a sessão persistente em `auth_info_baileys/`.
