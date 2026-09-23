import os
from pathlib import Path
from dotenv import load_dotenv

# Carrega variáveis do arquivo .env
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

# Google APIs Configuration
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID", "1MCalRZ5CTg_VVSdlRGpGzPwFc96nfZHvLNaq_A7nLEA")
SHEET_GID = os.getenv("SHEET_GID", "343702656")  # Aba LEADS
FORM_RESPONSES_GID = os.getenv("FORM_RESPONSES_GID", "1712742275")  # Aba Respostas ao formulário 1
FORM_RESPONSES_TAB = os.getenv("FORM_RESPONSES_TAB", "Respostas ao formulário 1")

# Files
CREDENTIALS_FILE = BASE_DIR / "credentials.json"
TOKEN_FILE = BASE_DIR / "token.json"
TEMPLATES_DIR = BASE_DIR / "templates"
TEMPLATE_HTML = TEMPLATES_DIR / "email_template.html"
TEMPLATE_TXT = TEMPLATES_DIR / "email_template.txt"

# Configurações de CNAEs e Templates Segmentados
CNAE_GROUPS = {
    "grupo1": {
        "nome": "Autopeças e Oficinas",
        "cnaes": ["4530-7/03", "4530-7/04", "4530-7/05", "4520-0/01", "4541-2/06"],
        "subject": "dúvida sobre a apuração do das - {empresa}",
        "template_txt": TEMPLATES_DIR / "grupo1_autopecas.txt",
        "template_html": TEMPLATES_DIR / "grupo1_autopecas.html",
    },
    "grupo2": {
        "nome": "Farmácias, Cosméticos e Perfumaria",
        "cnaes": ["4771-7/01", "4771-7/02", "4771-7/03", "4772-5/00"],
        "subject": "tributação de perfumaria e medicamentos / {empresa}",
        "template_txt": TEMPLATES_DIR / "grupo2_farmacias.txt",
        "template_html": TEMPLATES_DIR / "grupo2_farmacias.html",
    },
    "grupo3": {
        "nome": "Tabacarias, Conveniências e Alimentos",
        "cnaes": ["4729-6/01", "4721-1/04", "4729-6/99"],
        "subject": "impostos em duplicidade - {empresa}",
        "template_txt": TEMPLATES_DIR / "grupo3_tabacarias.txt",
        "template_html": TEMPLATES_DIR / "grupo3_tabacarias.html",
    },
    "grupo4": {
        "nome": "Bares, Restaurantes e Distribuidoras de Bebidas",
        "cnaes": ["5611-2/01", "5611-2/02", "5611-2/03", "5611-2/04", "4723-7/00", "4712-1/00"],
        "subject": "tributação de bebidas na {empresa}",
        "template_txt": TEMPLATES_DIR / "grupo4_bares.txt",
        "template_html": TEMPLATES_DIR / "grupo4_bares.html",
    }
}

# Google OAuth Scopes
SCOPES = [
    # Acesso completo para ler e atualizar valores na planilha
    "https://www.googleapis.com/auth/spreadsheets",
    # Acesso ao Google Drive
    "https://www.googleapis.com/auth/drive",
    # Envio de e-mails em nome do usuário
    "https://www.googleapis.com/auth/gmail.send",
    # Leitura e busca de mensagens na caixa de entrada para checar respostas dos leads
    "https://www.googleapis.com/auth/gmail.readonly",
]

# Configurações de Envio e Cadência
INTERVAL_SECONDS = int(os.getenv("INTERVAL_SECONDS", "60"))
TIMEZONE_NAME = os.getenv("TIMEZONE", "America/Sao_Paulo")
EMAIL_SUBJECT = os.getenv("EMAIL_SUBJECT", "💡Ei, sua empresa recuperou imposto ?")
SENDER_NAME = os.getenv("SENDER_NAME", "Pietro")

# Nomes esperados de Colunas
COL_EMAIL = os.getenv("COL_EMAIL", "E-mail")
COL_NAME = os.getenv("COL_NAME", "Nome")
COL_COMPANY = os.getenv("COL_COMPANY", "Empresa")
COL_CNAE = os.getenv("COL_CNAE", "CNAE Principal")
COL_CNPJ = os.getenv("COL_CNPJ", "CNPJ")
COL_NICHO = os.getenv("COL_NICHO", "Nicho / Segmento")
COL_GANCHO = os.getenv("COL_GANCHO", "Gancho de Abordagem")
COL_CIDADE = os.getenv("COL_CIDADE", "Cidade")
COL_TELEFONE = os.getenv("COL_TELEFONE", "Telefone")
COL_SEND_TIME = os.getenv("COL_SEND_TIME", "Hora de Envio")
COL_STATUS = os.getenv("COL_STATUS", "Status do Contato")

# Status do Contato (conforme menu da planilha)
STATUS_NOVO = "Novo"
STATUS_EM_CONTATO = "Em Contato"
STATUS_DIAGNOSTICO_ACEITO = "Diagnóstico Aceito"
STATUS_SEM_INTERESSE = "Sem Interesse"
