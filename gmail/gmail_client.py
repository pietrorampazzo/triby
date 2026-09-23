import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List, Dict, Any, Optional
from config import SENDER_NAME


class GmailClient:
    def __init__(self, service, user_email: str = "me"):
        self.service = service
        self.user_email = user_email

    def send_email(
        self,
        to_email: str,
        subject: str,
        body_html: str,
        body_text: str,
        sender_name: str = "",
    ) -> Dict[str, Any]:
        """
        Envia um e-mail multipart (HTML + Texto Puro) usando a Gmail API.
        """
        message = MIMEMultipart("alternative")
        message["to"] = to_email
        message["subject"] = subject

        name_to_use = sender_name or SENDER_NAME
        if name_to_use and self.user_email != "me":
            message["from"] = f"{name_to_use} <{self.user_email}>"

        # Anexa versão texto puro e HTML
        part_text = MIMEText(body_text, "plain", "utf-8")
        part_html = MIMEText(body_html, "html", "utf-8")

        message.attach(part_text)
        message.attach(part_html)

        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
        send_body = {"raw": raw_message}

        sent = (
            self.service.users()
            .messages()
            .send(userId="me", body=send_body)
            .execute()
        )
        return sent

    def check_replies_for_leads(self, contacted_leads: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Verifica a caixa de entrada por respostas dos leads contatados.
        Pesquisa mensagens onde o remetente é o e-mail do lead.
        """
        detected_replies = []
        if not contacted_leads:
            return detected_replies

        # Obter o endereço de e-mail da própria conta para não contar e-mails enviados por nós mesmos
        my_email = self.user_email.lower()

        for lead in contacted_leads:
            lead_email = lead.get("email", "").strip()
            if not lead_email:
                continue

            query = f"from:{lead_email} in:inbox"
            try:
                response = (
                    self.service.users()
                    .messages()
                    .list(userId="me", q=query, maxResults=5)
                    .execute()
                )
                messages = response.get("messages", [])
                if messages:
                    # Lead tem e-mails na caixa de entrada
                    for msg_item in messages:
                        msg_id = msg_item.get("id")
                        msg_data = (
                            self.service.users()
                            .messages()
                            .get(
                                userId="me",
                                id=msg_id,
                                format="metadata",
                                metadataHeaders=["From", "Subject", "Date"],
                            )
                            .execute()
                        )

                        headers = {
                            h.get("name", "").lower(): h.get("value", "")
                            for h in msg_data.get("payload", {}).get("headers", [])
                        }

                        sender = headers.get("from", "")
                        # Se o remetente não formos nós mesmos, é uma resposta válida do lead!
                        if my_email and my_email in sender.lower():
                            continue

                        detected_replies.append({
                            "lead": lead,
                            "email": lead_email,
                            "subject": headers.get("subject", "(Sem Assunto)"),
                            "from": sender,
                            "date": headers.get("date", ""),
                            "snippet": msg_data.get("snippet", ""),
                            "thread_id": msg_data.get("threadId"),
                            "message_id": msg_id,
                        })
                        # Processa apenas a mensagem mais recente desse lead
                        break
            except Exception as e:
                print(f"[!] Erro ao checar respostas para {lead_email}: {e}")

        return detected_replies
