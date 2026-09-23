#!/usr/bin/env node
require('dotenv').config();
const fs = require('fs');
const path = require('path');
const http = require('http');

const GROUPS_FILE = path.join(__dirname, 'grupos_barsi.json');
const DEFAULT_TEMPLATE = path.join(__dirname, 'templates', 'barsi_convite_legenda.txt');
const DEFAULT_IMAGE = path.join(__dirname, 'assets', 'barsi_dividendos_inteligentes.png');
const LOGS_DIR = path.join(__dirname, 'disparo_logs');

// Parse argumentos de linha de comando
const args = process.argv.slice(2);
const isDryRun = args.includes('--dry-run');
const isListOnly = args.includes('--list');
const noImage = args.includes('--no-image');

function getArgValue(flag, defaultValue = null) {
    const idx = args.indexOf(flag);
    if (idx !== -1 && args[idx + 1]) {
        return args[idx + 1];
    }
    return defaultValue;
}

const customMsg = getArgValue('--msg');
const customFile = getArgValue('--file');
const customImage = getArgValue('--img');
const delaySeconds = parseInt(getArgValue('--delay', '15'), 10);
const targetGroupId = getArgValue('--group');

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// Carrega os grupos
function loadGroups() {
    if (!fs.existsSync(GROUPS_FILE)) {
        throw new Error(`Arquivo de grupos não encontrado: ${GROUPS_FILE}`);
    }
    return JSON.parse(fs.readFileSync(GROUPS_FILE, 'utf-8'));
}

// Carrega o conteúdo da legenda/mensagem
function loadMessage() {
    if (customMsg) return customMsg.trim();
    const filePath = customFile ? path.resolve(customFile) : DEFAULT_TEMPLATE;
    if (!fs.existsSync(filePath)) {
        throw new Error(`Arquivo de mensagem não encontrado: ${filePath}`);
    }
    return fs.readFileSync(filePath, 'utf-8').trim();
}

// Obtém o caminho da imagem se existir
function getImageAttachment() {
    if (noImage) return null;
    const imgPath = customImage ? path.resolve(customImage) : DEFAULT_IMAGE;
    if (fs.existsSync(imgPath)) {
        return imgPath;
    }
    return null;
}

// Verifica se o servidor local HTTP está ativo na porta 3001
function checkLocalServer(port = 3001) {
    return new Promise((resolve) => {
        const req = http.get(`http://127.0.0.1:${port}/status`, { timeout: 2000 }, (res) => {
            let data = '';
            res.on('data', chunk => { data += chunk; });
            res.on('end', () => {
                try {
                    const parsed = JSON.parse(data);
                    resolve({ online: true, connected: !!parsed.connected });
                } catch {
                    resolve({ online: false, connected: false });
                }
            });
        });
        req.on('error', () => resolve({ online: false, connected: false }));
        req.on('timeout', () => { req.destroy(); resolve({ online: false, connected: false }); });
    });
}

// Envia mensagem (texto ou imagem + legenda) via API HTTP local
function sendViaHttp(jid, payloadContent, port = 3001) {
    return new Promise((resolve, reject) => {
        const payloadData = typeof payloadContent === 'string'
            ? { to: jid, text: payloadContent }
            : { to: jid, ...payloadContent };

        const payloadStr = JSON.stringify(payloadData);
        const req = http.request({
            hostname: '127.0.0.1',
            port,
            path: '/send',
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Content-Length': Buffer.byteLength(payloadStr)
            },
            timeout: 30000
        }, (res) => {
            let data = '';
            res.on('data', chunk => { data += chunk; });
            res.on('end', () => {
                try {
                    const parsed = JSON.parse(data);
                    if (res.statusCode >= 200 && res.statusCode < 300 && parsed.success) {
                        resolve(parsed);
                    } else {
                        reject(new Error(parsed.error || `HTTP ${res.statusCode}: ${data}`));
                    }
                } catch (e) {
                    reject(new Error(`Resposta inválida: ${data}`));
                }
            });
        });

        req.on('error', reject);
        req.on('timeout', () => {
            req.destroy();
            reject(new Error('Timeout ao enviar via API local'));
        });
        req.write(payloadStr);
        req.end();
    });
}

async function run() {
    const allGroups = loadGroups();

    if (isListOnly) {
        console.log('\n📋 GRUPOS CONFIGURADOS PARA DISPARO BARSI:');
        console.table(allGroups.map(g => ({
            '#': g.id,
            'Nome do Grupo': g.name,
            'WhatsApp JID': g.jid,
            'Status': g.status
        })));
        return;
    }

    const message = loadMessage();
    const imagePath = getImageAttachment();
    const groups = targetGroupId
        ? allGroups.filter(g => String(g.id) === String(targetGroupId))
        : allGroups;

    if (groups.length === 0) {
        console.error(`[ERRO] Nenhum grupo encontrado para o filtro informado.`);
        process.exit(1);
    }

    console.log('='.repeat(70));
    console.log('🚀 DISPARO PARA GRUPOS WHATSAPP - CONVITE BARSI');
    console.log('='.repeat(70));
    console.log(`Grupos selecionados: ${groups.length} de ${allGroups.length}`);
    console.log(`Intervalo anti-spam: ${delaySeconds} segundos entre envios`);
    console.log(`Modo de execução:    ${isDryRun ? 'SIMULAÇÃO (DRY-RUN - sem envio real)' : 'REAL (ENVIO ATIVO)'}`);
    console.log(`Imagem anexada:      ${imagePath ? imagePath : '(Apenas texto)'}`);
    console.log('\n--- PRÉVIA DA LEGENDA ---');
    console.log(message);
    console.log('---------------------------\n');

    let sendFn = null;
    let ephemeralClient = null;

    if (!isDryRun) {
        // Verifica se o serviço contínuo está rodando
        const serverStatus = await checkLocalServer();
        if (serverStatus.online && serverStatus.connected) {
            console.log('[*] Conexão ativa identificada na API local (porta 3001).');
            sendFn = (jid, content) => sendViaHttp(jid, content);
        } else {
            console.log('[*] API local não encontrada ou desconectada. Iniciando cliente WhatsApp direto...');
            const WhatsAppClient = require('./whatsapp_client');
            ephemeralClient = new WhatsAppClient();
            await ephemeralClient.connect();

            // Aguarda autenticar
            console.log('[*] Aguardando conexão abrir...');
            let attempts = 0;
            while (!ephemeralClient.isConnected && attempts < 35) {
                await sleep(1000);
                attempts++;
            }

            if (!ephemeralClient.isConnected) {
                console.error('[ERRO] Não foi possível conectar ao WhatsApp a tempo. Certifique-se de que a sessão está pareada.');
                process.exit(1);
            }
            sendFn = (jid, content) => ephemeralClient.sendMessage(jid, content);
        }
    }

    const report = {
        timestamp: new Date().toISOString(),
        dryRun: isDryRun,
        imageAttached: imagePath || null,
        total: groups.length,
        delaySeconds,
        successCount: 0,
        failCount: 0,
        results: []
    };

    const messagePayload = imagePath
        ? { image: imagePath, caption: message }
        : { text: message };

    console.log(`\nIniciando disparos às ${new Date().toLocaleTimeString()}...\n`);

    for (let i = 0; i < groups.length; i++) {
        const group = groups[i];
        const step = `[${i + 1}/${groups.length}]`;

        console.log(`${step} Preparando: "${group.name}" (${group.jid})...`);

        try {
            if (isDryRun) {
                console.log(`   👉 [DRY-RUN] Simulado envio com foto e legenda com sucesso!`);
                report.results.push({
                    id: group.id,
                    name: group.name,
                    jid: group.jid,
                    status: 'SIMULADO',
                    sentAt: new Date().toISOString()
                });
                report.successCount++;
            } else {
                const sendResult = await sendFn(group.jid, messagePayload);
                console.log(`   ✅ [OK] Convite com foto e legenda entregue ao grupo!`);
                report.results.push({
                    id: group.id,
                    name: group.name,
                    jid: group.jid,
                    messageId: sendResult?.messageId || sendResult?.key?.id || null,
                    status: 'SUCESSO',
                    sentAt: new Date().toISOString()
                });
                report.successCount++;
            }
        } catch (err) {
            console.error(`   ❌ [FALHA] Erro ao enviar: ${err.message}`);
            report.results.push({
                id: group.id,
                name: group.name,
                jid: group.jid,
                status: 'FALHA',
                error: err.message,
                sentAt: new Date().toISOString()
            });
            report.failCount++;
        }

        // Aguarda intervalo anti-spam se não for o último grupo
        if (i < groups.length - 1) {
            const waitTime = isDryRun ? 1000 : delaySeconds * 1000;
            console.log(`   ⏳ Aguardando ${waitTime / 1000}s de intervalo de segurança anti-spam...\n`);
            await sleep(waitTime);
        }
    }

    // Salva relatório de auditoria
    if (!fs.existsSync(LOGS_DIR)) {
        fs.mkdirSync(LOGS_DIR, { recursive: true });
    }
    const logFileName = `disparo_${new Date().toISOString().replace(/[:.]/g, '-')}.json`;
    fs.writeFileSync(path.join(LOGS_DIR, logFileName), JSON.stringify(report, null, 2), 'utf-8');

    console.log('\n' + '='.repeat(70));
    console.log('📊 RESUMO DO DISPARO BARSI:');
    console.log(`Total de Grupos:     ${report.total}`);
    console.log(`Enviados com Sucesso: ${report.successCount}`);
    console.log(`Falhas:              ${report.failCount}`);
    console.log(`Foto Anexada:        ${report.imageAttached ? 'Sim (barsi_dividendos_inteligentes.png)' : 'Não'}`);
    console.log(`Relatório salvo em:  whatsapp/disparo_logs/${logFileName}`);
    console.log('='.repeat(70) + '\n');

    if (ephemeralClient) {
        console.log('[*] Finalizando processo...');
        setTimeout(() => process.exit(0), 1000);
    }
}

run().catch((err) => {
    console.error('[ERRO FATAL NO DISPARO]', err);
    process.exit(1);
});
