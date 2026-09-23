import sys
from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from config import CREDENTIALS_FILE, TOKEN_FILE, SCOPES


def get_credentials() -> Credentials:
    """
    Obtém e valida as credenciais OAuth 2.0 do Google.
    Se o arquivo token.json não existir ou estiver expirado, inicia o fluxo de autorização
    no navegador usando o credentials.json e salva o token resultante.
    """
    creds = None

    # Verifica se já temos um token salvo previamente
    if TOKEN_FILE.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
        except Exception as e:
            print(f"[!] Erro ao carregar token existente: {e}")
            creds = None

    # Se não houver credenciais válidas disponíveis, solicita autorização ao usuário
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                print("[*] Renovando token de acesso do Google...")
                creds.refresh(Request())
            except Exception as e:
                print(f"[!] Não foi possível renovar o token: {e}. Solicitando nova autorização...")
                creds = None

        if not creds:
            if not CREDENTIALS_FILE.exists():
                print("\n" + "=" * 70)
                print("[ERRO] Arquivo 'credentials.json' não encontrado na pasta do projeto!")
                print(f"Caminho esperado: {CREDENTIALS_FILE}")
                print("\nPara resolver:")
                print("1. Acesse o Google Cloud Console: https://console.cloud.google.com/")
                print("2. Crie ou selecione seu projeto Google Workspace.")
                print("3. Ative a 'Gmail API' e a 'Google Sheets API'.")
                print("4. Em 'Credenciais', crie um 'ID do cliente OAuth' para 'Aplicativo para Computador' (Desktop).")
                print("5. Baixe o arquivo JSON e renomeie para 'credentials.json' nesta pasta.")
                print("=" * 70 + "\n")
                sys.exit(1)

            print("[*] Iniciando fluxo de autorização OAuth 2.0 no navegador...")
            flow = InstalledAppFlow.from_client_secrets_file(
                str(CREDENTIALS_FILE), SCOPES
            )
            # Abre o navegador automaticamente na porta local disponível
            creds = flow.run_local_server(port=0, prompt="consent")

            # Salva o token para as próximas execuções
            with open(TOKEN_FILE, "w", encoding="utf-8") as token_out:
                token_out.write(creds.to_json())
            print(f"[OK] Token salvo com sucesso em: {TOKEN_FILE.name}")

    return creds


def get_sheets_service(creds: Credentials = None):
    """Retorna o serviço da Google Sheets API v4."""
    if not creds:
        creds = get_credentials()
    return build("sheets", "v4", credentials=creds)


def get_gmail_service(creds: Credentials = None):
    """Retorna o serviço da Gmail API v1."""
    if not creds:
        creds = get_credentials()
    return build("gmail", "v1", credentials=creds)


def get_google_services():
    """Retorna ambos os serviços (sheets, gmail) com uma única verificação de credenciais."""
    creds = get_credentials()
    sheets = build("sheets", "v4", credentials=creds)
    gmail = build("gmail", "v1", credentials=creds)
    return sheets, gmail


def get_authenticated_user_email(gmail_service) -> str:
    """Retorna o endereço de e-mail da conta Google Workspace conectada."""
    try:
        profile = gmail_service.users().getProfile(userId="me").execute()
        return profile.get("emailAddress", "desconhecido")
    except Exception as e:
        print(f"[!] Não foi possível obter o e-mail autenticado: {e}")
        return "desconhecido"
