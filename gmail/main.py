import os
import sys
import time
import argparse
from datetime import datetime
import zoneinfo

# Garante compatibilidade UTF-8 no terminal Windows
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from config import (
    SPREADSHEET_ID,
    SHEET_GID,
    INTERVAL_SECONDS,
    TIMEZONE_NAME,
    EMAIL_SUBJECT,
    SENDER_NAME,
    STATUS_EM_CONTATO,
    STATUS_NOVO,
)
from auth import get_google_services, get_authenticated_user_email
from sheets_client import SheetsClient
from gmail_client import GmailClient
from template_manager import TemplateManager


def get_current_time_str() -> str:
    """Gera a string de data/hora no padrão solicitado: 'xx/xx/xxxx às yy:yy'."""
    try:
        tz = zoneinfo.ZoneInfo(TIMEZONE_NAME)
        now = datetime.now(tz)
    except Exception:
        now = datetime.now()
    return now.strftime("%d/%m/%Y às %H:%M")


def run_cycle(sheets_client: SheetsClient, gmail_client: GmailClient, template_manager: TemplateManager, check_only: bool = False) -> bool:
    """
    Executa um ciclo do processo:
    1. Verifica respostas na caixa de entrada para leads já contactados.
    2. Envia 1 e-mail para o próximo lead pendente (se não estiver em check_only).
    Retorna True se um e-mail foi enviado, False caso contrário.
    """
    timestamp_log = datetime.now().strftime("%H:%M:%S")
    print(f"\n[{timestamp_log}] === Iniciando ciclo de processamento ===")

    # 1. VERIFICAÇÃO DE RESPOSTAS NA CAIXA DE ENTRADA
    print("[*] Conferindo caixa de entrada do Gmail por respostas de leads...")
    contacted_leads = sheets_client.get_contacted_leads()
    if contacted_leads:
        print(f"[*] Monitorando {len(contacted_leads)} lead(s) com status 'Em Contato'...")
        replies = gmail_client.check_replies_for_leads(contacted_leads)
        if replies:
            print("\n" + "=" * 65)
            print(f"[!!!] ATENÇÃO: {len(replies)} NOVA(S) RESPOSTA(S) IDENTIFICADA(S)!")
            print("=" * 65)
            for r in replies:
                lead = r["lead"]
                print(f"  • Lead: {lead.get('nome', '')} ({r['email']}) - Linha {lead.get('row_number')}")
                print(f"    Assunto: {r['subject']}")
                print(f"    Data: {r['date']}")
                print(f"    Trecho: \"{r['snippet']}\"")
                print(f"    Link/ID: {r['thread_id']}")
                print("-" * 65)
        else:
            print("[*] Nenhuma nova resposta identificada nesta checagem.")
    else:
        print("[*] Nenhum lead em contato para monitorar respostas.")

    if check_only:
        print("[*] Modo 'apenas checagem' ativado. Nenhum e-mail será enviado.")
        return False

    # 2. SELEÇÃO E ENVIO DE E-MAIL PARA O PRÓXIMO LEAD PENDENTE
    print("[*] Buscando próximo lead pendente na planilha...")
    try:
        pending_lead = sheets_client.get_next_pending_lead()
    except Exception as e:
        print(f"[!] Erro ao buscar lead pendente: {e}")
        return False

    if not pending_lead:
        print("[i] Nenhum lead pendente encontrado na planilha (todos já foram contatados ou estão preenchidos).")
        return False

    row_num = pending_lead["row_number"]
    email_to = pending_lead["email"]
    nome_lead = pending_lead.get("nome") or "Prezado(a)"
    empresa_lead = pending_lead.get("empresa") or "sua empresa"

    print(f"\n[>>>] Lead Selecionado: {nome_lead} | Empresa: {empresa_lead} | E-mail: {email_to} (Linha {row_num})")

    # Renderiza templates
    body_html, body_text = template_manager.render(pending_lead["raw_row"], sender_name=SENDER_NAME)

    # Assunto personalizado com suporte a várias tags
    subject = EMAIL_SUBJECT
    for key, val in [
        ("empresa", empresa_lead),
        ("nome", nome_lead),
        ("cidade", pending_lead["raw_row"].get("Cidade", "")),
        ("nicho", pending_lead["raw_row"].get("Nicho / Segmento", "")),
    ]:
        subject = subject.replace(f"{{{key}}}", str(val)).replace(f"{{{key.capitalize()}}}", str(val))
        subject = subject.replace(f"[{key}]", str(val)).replace(f"[{key.capitalize()}]", str(val))

    # Dispara e-mail via Gmail API
    print(f"[*] Enviando e-mail via Gmail para: {email_to}...")
    try:
        sent_info = gmail_client.send_email(
            to_email=email_to,
            subject=subject,
            body_html=body_html,
            body_text=body_text,
            sender_name=SENDER_NAME,
        )
        msg_id = sent_info.get("id", "desconhecido")
        print(f"[OK] E-mail enviado com sucesso! Message ID: {msg_id}")
    except Exception as e:
        print(f"[ERRO] Falha ao enviar e-mail para {email_to}: {e}")
        return False

    # Registra data/hora no padrão solicitado: "xx/xx/xxxx às yy:yy"
    send_time_formatted = get_current_time_str()
    print(f"[*] Registrando na planilha: Hora='{send_time_formatted}', Status='{STATUS_EM_CONTATO}'...")

    try:
        sheets_client.update_lead_sent(
            row_number=row_num,
            send_time_str=send_time_formatted,
            new_status=STATUS_EM_CONTATO,
        )
        print(f"[SUCESSO] Lead linha {row_num} atualizado com êxito!")
        return True
    except Exception as e:
        print(f"[ERRO] Falha ao atualizar planilha para a linha {row_num}: {e}")
        return False


def test_environment(sheets_client: SheetsClient, gmail_client: GmailClient, user_email: str):
    """Executa testes de validação das conexões sem enviar e-mails ou alterar a planilha."""
    print("\n" + "=" * 65)
    print("[TESTE] VALIDAÇÃO DE CONECTIVIDADE E AMBIENTE")
    print("=" * 65)
    print(f"Conta Google Workspace Conectada: {user_email}")
    print(f"ID da Planilha: {SPREADSHEET_ID}")
    print(f"Aba da Planilha: '{sheets_client.sheet_title}' (GID {sheets_client.gid})")

    # Lê cabeçalhos
    rows = sheets_client.read_all_rows()
    if not rows:
        print("[!] A planilha retornou 0 linhas.")
        return

    headers = rows[0]
    print(f"\nCabeçalhos encontrados ({len(headers)} colunas):")
    for i, h in enumerate(headers):
        print(f"  [{i}] {h}")

    col_map = sheets_client.map_columns(headers)
    letters = sheets_client.get_column_letters()

    print("\nMapeamento de Colunas Detectado:")
    for k, idx in col_map.items():
        print(f"  - {k.upper()}: Coluna '{headers[idx]}' (Índice {idx} -> Letra {letters.get(k)})")

    # Contagem de leads
    total_dados = len(rows) - 1
    pending = sheets_client.get_next_pending_lead()
    contacted = sheets_client.get_contacted_leads()

    print(f"\nResumo de Linhas:")
    print(f"  • Total de linhas de dados: {total_dados}")
    print(f"  • Leads já 'Em Contato': {len(contacted)}")
    if pending:
        print(f"  • Próximo lead da fila: Linha {pending['row_number']} - {pending['email']} ({pending.get('nome')})")
    else:
        print("  • Próximo lead da fila: Nenhum lead pendente")

    # Testa busca de caixa de entrada
    print("\nTestando busca no Gmail...")
    try:
        test_search = gmail_client.service.users().messages().list(userId="me", maxResults=1).execute()
        print(f"[OK] Acesso ao Gmail verificado. Total estimado de mensagens: {test_search.get('resultSizeEstimate', 0)}")
    except Exception as e:
        print(f"[!] Erro ao testar Gmail: {e}")

    print("\n[OK] Teste de ambiente concluído com sucesso!")
    print("=" * 65 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Automação de Envio de E-mails via Gmail e Google Sheets")
    parser.add_argument(
        "--mode",
        choices=["loop", "once"],
        default="loop",
        help="Modo de execução: 'loop' roda continuamente a cada intervalo (padrão); 'once' roda 1 único ciclo e encerra (ideal para cron/agendador).",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=INTERVAL_SECONDS,
        help=f"Intervalo em segundos entre envios no modo loop (padrão: {INTERVAL_SECONDS} segundos = 1 minuto).",
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Apenas verifica respostas na caixa de entrada sem enviar novos e-mails.",
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Testa credenciais, conexões com Gmail e Google Sheets e exibe mapeamento de colunas.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Número máximo de e-mails enviados antes de encerrar (0 = sem limite/infinito).",
    )

    args = parser.parse_args()

    print("=================================================================")
    print("[*] DISPARADOR DE LEADS & MONITOR DE RESPOSTAS (GOOGLE WORKSPACE)")
    print("=================================================================")

    # 1. Autenticação e conexão com Google APIs
    try:
        sheets_service, gmail_service = get_google_services()
        user_email = get_authenticated_user_email(gmail_service)
        print(f"[*] Autenticado com sucesso como: {user_email}")
    except Exception as e:
        print(f"[ERRO CRÍTICO] Falha na autenticação do Google: {e}")
        sys.exit(1)

    # 2. Inicialização dos clientes
    sheets_client = SheetsClient(sheets_service)
    gmail_client = GmailClient(gmail_service, user_email=user_email)
    template_manager = TemplateManager()

    # Se for modo de teste
    if args.test:
        test_environment(sheets_client, gmail_client, user_email)
        return

    # Se for execução única (estilo cron)
    if args.mode == "once":
        print("[*] Executando em MODO ÚNICO (cron/once)...")
        run_cycle(sheets_client, gmail_client, template_manager, check_only=args.check_only)
        print("[*] Execução concluída.")
        return

    # Modo LOOP contínuo (envio a cada 1 minuto)
    interval = args.interval
    limit_info = f" (Limite: {args.limit} e-mails)" if args.limit > 0 else " (Sem limite de quantidade)"
    print(f"[*] Executando em MODO LOOP contínuo (intervalo de {interval}s / 1 minuto entre disparos){limit_info}.")
    print("[*] Pressione Ctrl+C a qualquer momento para encerrar com segurança.\n")

    cycle_count = 0
    sent_count = 0
    try:
        while True:
            cycle_count += 1
            print(f"\n--- [Ciclo #{cycle_count}] ---")
            start_time = time.time()

            sent = run_cycle(sheets_client, gmail_client, template_manager, check_only=args.check_only)

            if sent:
                sent_count += 1
                if args.limit > 0:
                    print(f"[*] Progresso do MVP: {sent_count}/{args.limit} e-mail(s) enviado(s).")
                    if sent_count >= args.limit:
                        print("\n" + "=" * 65)
                        print(f"[SUCESSO] META ATINGIDA: {args.limit} e-mails do MVP enviados e registrados!")
                        print("=" * 65 + "\n")
                        break

            elapsed = time.time() - start_time
            sleep_time = max(0.0, interval - elapsed)

            if not args.check_only and not sent:
                print(f"[*] Sem novos envios neste momento. Próxima checagem em {int(sleep_time)}s...")
            else:
                print(f"[*] Aguardando {int(sleep_time)}s para o próximo disparo (cadência de 1 e-mail por minuto)...")

            # Aguarda com pequenos intervalos para responder prontamente a interrupções
            end_sleep = time.time() + sleep_time
            while time.time() < end_sleep:
                time.sleep(1)

    except KeyboardInterrupt:
        print("\n\n[!] Interrupção recebida do usuário (Ctrl+C). Encerrando serviço com segurança.")
        sys.exit(0)


if __name__ == "__main__":
    main()
