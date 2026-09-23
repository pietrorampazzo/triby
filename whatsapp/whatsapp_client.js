const {
    default: makeWASocket,
    useMultiFileAuthState,
    DisconnectReason,
    delay,
    Browsers,
    fetchLatestBaileysVersion
} = require('@whiskeysockets/baileys');
const { Boom } = require('@hapi/boom');
const pino = require('pino');
const path = require('path');
const fs = require('fs');

class WhatsAppClient {
    constructor(options = {}) {
        this.phoneNumber = (options.phoneNumber || process.env.PHONE_NUMBER || '5511994103374').replace(/\D/g, '');
        this.authDir = options.authDir || process.env.AUTH_DIR || path.join(__dirname, 'auth_info_baileys');
        this.sock = null;
        this.isConnected = false;
        this.isConnecting = false;
        this.pairingCodeRequested = false;
    }

    async connect() {
        if (this.isConnecting) return;
        this.isConnecting = true;

        try {
            console.log('[*] Carregando estado de autenticação...');
            const { state, saveCreds } = await useMultiFileAuthState(this.authDir);

            let version;
            try {
                const vInfo = await fetchLatestBaileysVersion();
                version = vInfo.version;
                console.log(`[*] Baileys versão: ${version.join('.')}`);
            } catch (e) {
                version = [2, 3000, 1015901307];
            }

            // Remove listeners antigos se houver
            if (this.sock && this.sock.ev) {
                try {
                    this.sock.ev.removeAllListeners();
                } catch (e) {}
            }

            const sock = makeWASocket({
                version,
                logger: pino({ level: 'silent' }),
                printQRInTerminal: false,
                auth: state,
                browser: Browsers.ubuntu('Chrome'),
                markOnlineOnConnect: true,
                generateHighQualityLinkPreview: true,
                syncFullHistory: false,
                connectTimeoutMs: 60000,
                defaultQueryTimeoutMs: 60000,
                keepAliveIntervalMs: 25000,
            });

            this.sock = sock;

            // Salva credenciais sempre que atualizadas
            sock.ev.on('creds.update', saveCreds);

            // Se ainda não estiver registrado, solicita o código de pareamento
            const isRegistered = sock.authState?.creds?.registered;
            if (!isRegistered && !this.pairingCodeRequested) {
                this.pairingCodeRequested = true;
                setTimeout(async () => {
                    try {
                        console.log(`[*] Solicitando Código de Pareamento para o número +${this.phoneNumber}...`);
                        const code = await sock.requestPairingCode(this.phoneNumber);
                        const formatted = code?.match(/.{1,4}/g)?.join('-') || code;

                        console.log('\n' + '='.repeat(60));
                        console.log('📲 CÓDIGO DE PAREAMENTO DO WHATSAPP GERADO COM SUCESSO:');
                        console.log('\n            👉   ' + formatted + '   👈\n');
                        console.log('Instruções para parear no seu celular:');
                        console.log(`1. Abra o WhatsApp no aparelho (+${this.phoneNumber})`);
                        console.log('2. Acesse: Configurações > Aparelhos Conectados');
                        console.log('3. Toque em: "Conectar um aparelho"');
                        console.log('4. Na parte inferior, toque em: "Conectar com número de telefone"');
                        console.log(`5. Digite o código de 8 dígitos acima: ${formatted}`);
                        console.log('='.repeat(60) + '\n');
                    } catch (err) {
                        console.error('[ERRO] Falha ao solicitar código de pareamento:', err.message || err);
                        this.pairingCodeRequested = false;
                    }
                }, 3000);
            }

            // Monitora o status da conexão
            sock.ev.on('connection.update', async (update) => {
                const { connection, lastDisconnect } = update;

                if (connection === 'connecting') {
                    console.log('[*] Conectando aos servidores do WhatsApp...');
                } else if (connection === 'open') {
                    this.isConnected = true;
                    this.isConnecting = false;
                    const user = sock.user;
                    console.log('\n' + '='.repeat(60));
                    console.log('✅ WHATSAPP CONECTADO COM SUCESSO!');
                    console.log(`Conta: ${user?.name || 'WhatsApp'} (${user?.id?.split(':')[0] || this.phoneNumber})`);
                    console.log('Status: Pronto para enviar e receber mensagens.');
                    console.log('='.repeat(60) + '\n');
                } else if (connection === 'close') {
                    this.isConnected = false;
                    this.isConnecting = false;

                    const statusCode = (lastDisconnect?.error instanceof Boom)
                        ? lastDisconnect.error.output?.statusCode
                        : lastDisconnect?.error?.statusCode;

                    const shouldReconnect = statusCode !== DisconnectReason.loggedOut;

                    console.log(`[!] Conexão fechada. Motivo / Código: ${statusCode}. Reconectar: ${shouldReconnect}`);

                    if (statusCode === DisconnectReason.loggedOut) {
                        console.log('[!] Aparelho desconectado (Logout). Limpando sessão antiga...');
                        try {
                            fs.rmSync(this.authDir, { recursive: true, force: true });
                        } catch (e) {}
                        this.pairingCodeRequested = false;
                        console.log('[*] Reiniciando para novo pareamento em 3s...');
                        setTimeout(() => this.connect(), 3000);
                    } else if (statusCode === DisconnectReason.connectionReplaced || statusCode === 440) {
                        console.log('[!] Conexão substituída por outra sessão ativa (ex: WhatsApp Web aberto no navegador).');
                        console.log('[*] Aguardando 30 segundos antes de tentar restabelecer conexão com o Baileys...');
                        setTimeout(() => this.connect(), 30000);
                    } else if (shouldReconnect) {
                        console.log('[*] Reconectando em 5 segundos...');
                        setTimeout(() => this.connect(), 5000);
                    }
                }
            });

            // Escuta novas mensagens recebidas
            sock.ev.on('messages.upsert', async ({ messages, type }) => {
                if (type !== 'notify') return;

                for (const msg of messages) {
                    if (!msg.message) continue;
                    const from = msg.key.remoteJid;
                    const isFromMe = msg.key.fromMe;
                    const pushName = msg.pushName || 'Desconhecido';

                    const text =
                        msg.message.conversation ||
                        msg.message.extendedTextMessage?.text ||
                        msg.message.imageMessage?.caption ||
                        '';

                    if (text && !isFromMe) {
                        console.log(`\n📩 Nova Mensagem de ${pushName} (${from}):`);
                        console.log(`   "${text}"`);
                    }
                }
            });

            return sock;
        } catch (err) {
            this.isConnecting = false;
            console.error('[ERRO] Falha ao iniciar conexão:', err.message || err);
            console.log('[*] Tentando reconectar em 5 segundos...');
            setTimeout(() => this.connect(), 5000);
        }
    }

    async sendMessage(to, content) {
        if (!this.isConnected || !this.sock) {
            throw new Error('WhatsApp não está conectado no momento.');
        }

        let targetJid = String(to).trim();
        if (!targetJid.includes('@')) {
            const cleanNumber = targetJid.replace(/\D/g, '');
            targetJid = `${cleanNumber}@s.whatsapp.net`;
        }

        let payload;
        if (typeof content === 'string') {
            payload = { text: content };
        } else if (content && content.image) {
            let imageBuffer;
            if (typeof content.image === 'string') {
                imageBuffer = fs.readFileSync(content.image);
            } else {
                imageBuffer = content.image;
            }
            payload = {
                image: imageBuffer,
                caption: content.caption || content.text || ''
            };
        } else if (content && content.text) {
            payload = { text: content.text };
        } else {
            payload = content;
        }

        console.log(`[*] Enviando mensagem para ${targetJid}...`);
        const result = await this.sock.sendMessage(targetJid, payload);
        console.log(`[OK] Mensagem enviada para ${targetJid} com sucesso!`);
        return result;
    }
}

module.exports = WhatsAppClient;
