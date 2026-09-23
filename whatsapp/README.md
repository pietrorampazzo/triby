# Módulo WhatsApp (API Baileys)

Conexão direta e leve com o WhatsApp utilizando a biblioteca **Baileys** (`@whiskeysockets/baileys`) sem necessidade de navegador Chromium ou Selenium, com autenticação via **Código de Pareamento (Pairing Code)** digitado diretamente no aplicativo do celular.

---

## 📱 Número Configurado
- **Telefone:** `+55 11 99410-3374`
- **Configuração:** Editável no arquivo `.env` (`PHONE_NUMBER=5511994103374`).

---

## 🚀 Como Iniciar e Parear

1. Dê dois cliques em **`start.bat`** (ou rode `node index.js` no terminal dentro desta pasta).
2. O script exibirá o código de 8 dígitos formatado (ex: `ABCD-1234`).
3. No WhatsApp do seu celular (+55 11 99410-3374):
   - Abra **Configurações** (ou três pontinhos no Android).
   - Toque em **Aparelhos Conectados**.
   - Toque em **Conectar um aparelho**.
   - Na parte inferior da tela, toque em **Conectar com número de telefone**.
   - Digite o código de 8 dígitos exibido no terminal.
4. Após digitar o código, a sessão será autenticada e os dados salvos em `auth_info_baileys/`. **As próximas inicializações serão automáticas!**

---

- **`index.js`**: Ponto de entrada que inicia o cliente e mantém o serviço ativo com API HTTP interna na porta 3001.
- **`whatsapp_client.js`**: Classe cliente com métodos de conexão, reconexão automática, escuta de mensagens e envio de mensagens para contatos e grupos (`sendMessage(to, text)`).
- **`auth_info_baileys/`**: Pasta contendo as chaves de sessão autenticadas.
- **`start.bat`**: Atalho para execução com um clique no Windows.
- **`grupos_barsi.json`**: Cadastro oficial dos 13 grupos de networking da campanha Barsi.
- **`disparo_barsi.js`**: Script de envio em lote para os grupos com intervalo anti-spam e relatório de entrega.
- **`disparar_barsi.bat`**: Atalho com menu interativo (Disparo real, simulação dry-run, listagem de grupos).
- **`templates/barsi_mensagem.txt`**: Template de texto padrão das mensagens enviadas aos grupos.
- **`disparo_logs/`**: Histórico detalhado de cada disparo com data, hora e status por grupo.
