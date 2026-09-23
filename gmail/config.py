import os
from pathlib import Path
from dotenv import load_dotenv

# Carrega variáveis do arquivo .env
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

# Google APIs Configuration
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID", "1V3W0KME53VqjGlhaFudJ2IkcmI0MlzPAoaJ4ZszSu9s")
SHEET_GID = os.getenv("SHEET_GID", "421539945")

# Files
CREDENTIALS_FILE = BASE_DIR / "credentials.json"
TOKEN_FILE = BASE_DIR / "token.json"
TEMPLATES_DIR = BASE_DIR / "templates"
TEMPLATE_HTML = TEMPLATES_DIR / "email_template.html"
TEMPLATE_TXT = TEMPLATES_DIR / "email_template.txt"

# Configurações de CNAEs e Templates
CNAE_GROUPS = {
    "grupo1": {
        "cnaes": ["4530-7/03", "4530-7/04", "4530-7/05"],
        "subject": "dúvida sobre a apuração do das - {empresa}",
        "template_txt": TEMPLATES_DIR / "grupo1_autopecas.txt",
        "template_html": TEMPLATES_DIR / "grupo1_autopecas.html",
    },
    "grupo2": {
        "cnaes": ["4771-7/01", "4771-7/02", "4771-7/03"],
        "subject": "tributação de perfumaria e medicamentos / {empresa}",
        "template_txt": TEMPLATES_DIR / "grupo2_farmacias.txt",
        "template_html": TEMPLATES_DIR / "grupo2_farmacias.html",
    },
    "grupo3": {
        "cnaes": ["4729-6/01", "4721-1/04"],
        "subject": "impostos em duplicidade - {empresa}",
        "template_txt": TEMPLATES_DIR / "grupo3_tabacarias.txt",
        "template_html": TEMPLATES_DIR / "grupo3_tabacarias.html",
    },
    "grupo4": {
        "cnaes": ["5611-2/01", "5611-2/02", "4712-1/00"],
        "subject": "tributação de bebidas na {empresa}",
        "template_txt": TEMPLATES_DIR / "grupo4_bares.txt",
        "template_html": TEMPLATES_DIR / "grupo4_bares.html",
    }
}

# Google OAuth Scopes
SCOPES = [
    # Acesso completo para ler e atualizar valores na planilha
    "https://www.googleapis.com/auth/spreadsheets",
    # Envio de e-mails em nome do usuário
    "https://www.googleapis.com/auth/gmail.send",
    # Leitura e busca de mensagens na caixa de entrada para checar respostas dos leads
    "https://www.googleapis.com/auth/gmail.readonly",
]

# Configurações de Envio e Cadência
INTERVAL_SECONDS = int(os.getenv("INTERVAL_SECONDS", "60"))
TIMEZONE_NAME = os.getenv("TIMEZONE", "America/Sao_Paulo")
EMAIL_SUBJECT = os.getenv("EMAIL_SUBJECT", "Diagnóstico Estratégico - {empresa}")
SENDER_NAME = os.getenv("SENDER_NAME", "")

# Nomes esperados de Colunas
COL_EMAIL = os.getenv("COL_EMAIL", "E-mail")
COL_NAME = os.getenv("COL_NAME", "Nome")
COL_COMPANY = os.getenv("COL_COMPANY", "Empresa")
COL_CNAE = os.getenv("COL_CNAE", "CNAE")
COL_SEND_TIME = os.getenv("COL_SEND_TIME", "Hora de Envio")
COL_STATUS = os.getenv("COL_STATUS", "Status do Contato")

# Status do Contato (conforme menu da foto)
STATUS_NOVO = "Novo"
STATUS_EM_CONTATO = "Em Contato"
STATUS_DIAGNOSTICO_ACEITO = "Diagnóstico Aceito"
STATUS_SEM_INTERESSE = "Sem Interesse"
