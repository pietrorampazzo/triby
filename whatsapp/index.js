require('dotenv').config();
const WhatsAppClient = require('./whatsapp_client');

const phoneNumber = process.env.PHONE_NUMBER || '5511994103374';

console.log('='.repeat(65));
console.log('🚀 INICIANDO CONEXÃO WHATSAPP BAILEYS (TRIBY)');
console.log(`Número de Telefone Alvo: +${phoneNumber}`);
console.log('='.repeat(65));

// Tratamento de exceções e rejeições assíncronas do socket para manter o serviço 100% online
process.on('unhandledRejection', (reason) => {
    // Evita crash por fechamento de socket durante requisições pendentes
    console.log('[*] Aviso de conexão assíncrona:', reason?.message || reason);
});

process.on('uncaughtException', (err) => {
    console.log('[*] Exceção tratada internamente:', err?.message || err);
});

const client = new WhatsAppClient({ phoneNumber });

client.connect().catch((err) => {
    console.error('[ERRO FATAL] Erro ao iniciar cliente WhatsApp:', err);
});

const http = require('http');
const PORT = process.env.API_PORT || 3001;

const server = http.createServer((req, res) => {
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

    if (req.method === 'OPTIONS') {
        res.writeHead(204);
        res.end();
        return;
    }

    if (req.method === 'GET' && (req.url === '/status' || req.url === '/health')) {
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({
            connected: client.isConnected,
            user: client.sock?.user || null
        }));
        return;
    }

    if (req.method === 'POST' && req.url === '/send') {
        let body = '';
        req.on('data', chunk => { body += chunk; });
        req.on('end', async () => {
            try {
                const data = JSON.parse(body || '{}');
                if (!data.to || (!data.text && !data.image && !data.caption)) {
                    res.writeHead(400, { 'Content-Type': 'application/json' });
                    res.end(JSON.stringify({ error: 'Campos "to" e conteúdo ("text" ou "image" + "caption") são obrigatórios.' }));
                    return;
                }
                const result = await client.sendMessage(data.to, data);
                res.writeHead(200, { 'Content-Type': 'application/json' });
                res.end(JSON.stringify({ success: true, messageId: result?.key?.id }));
            } catch (err) {
                res.writeHead(500, { 'Content-Type': 'application/json' });
                res.end(JSON.stringify({ error: err.message }));
            }
        });
        return;
    }

    res.writeHead(404, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ error: 'Endpoint não encontrado.' }));
});

server.listen(PORT, '127.0.0.1', () => {
    console.log(`[*] API interna do WhatsApp ativa em http://127.0.0.1:${PORT}`);
});

// Encerramento gracioso via Ctrl+C
process.on('SIGINT', () => {
    console.log('\n[!] Encerrando conexão WhatsApp e servidor API...');
    server.close();
    process.exit(0);
});
