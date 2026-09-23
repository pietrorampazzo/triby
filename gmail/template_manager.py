from pathlib import Path
from config import TEMPLATE_HTML, TEMPLATE_TXT, SENDER_NAME


class TemplateManager:
    def __init__(self, html_path: Path = TEMPLATE_HTML, txt_path: Path = TEMPLATE_TXT):
        self.html_path = html_path
        self.txt_path = txt_path

        if not self.html_path.exists():
            raise FileNotFoundError(f"Template HTML não encontrado em: {self.html_path}")
        if not self.txt_path.exists():
            raise FileNotFoundError(f"Template de texto não encontrado em: {self.txt_path}")

        with open(self.html_path, "r", encoding="utf-8") as f:
            self.html_raw = f.read()

        with open(self.txt_path, "r", encoding="utf-8") as f:
            self.txt_raw = f.read()

    def render(self, lead_data: dict, sender_name: str = "") -> tuple[str, str, str]:
        """
        Substitui as variáveis nos templates com dados do lead.
        Retorna (rendered_subject, rendered_html, rendered_text).
        """
        # Trata nome
        full_name = lead_data.get("Nome") or lead_data.get("nome") or lead_data.get("Contato") or ""
        first_name = full_name.strip().split()[0] if full_name.strip() else "Prezado(a)"

        # Trata empresa
        company = lead_data.get("Empresa") or lead_data.get("empresa") or lead_data.get("Negócio") or "sua empresa"

        # Remetente
        remetente = sender_name or SENDER_NAME or "Equipe de Novos Negócios"

        context = {
            "nome": first_name,
            "nome_completo": full_name or first_name,
            "empresa": company,
            "email": lead_data.get("E-mail") or lead_data.get("email") or "",
            "remetente": remetente,
        }

        # Adiciona quaisquer outros campos existentes na linha sem sobrescrever os tratados
        for k, v in lead_data.items():
            k_lower = str(k).lower().strip()
            if k_lower not in context:
                context[k_lower] = str(v)

        rendered_html = self.html_raw
        rendered_text = self.txt_raw

        for key, val in context.items():
            # Suporta variações com chaves: {nome}, {Nome}, {NOME}
            rendered_html = rendered_html.replace(f"{{{key}}}", str(val))
            rendered_html = rendered_html.replace(f"{{{key.capitalize()}}}", str(val))
            rendered_html = rendered_html.replace(f"{{{key.upper()}}}", str(val))

            rendered_text = rendered_text.replace(f"{{{key}}}", str(val))
            rendered_text = rendered_text.replace(f"{{{key.capitalize()}}}", str(val))
            rendered_text = rendered_text.replace(f"{{{key.upper()}}}", str(val))

            # Suporta variações com colchetes: [nome], [Nome], [NOME]
            rendered_html = rendered_html.replace(f"[{key}]", str(val))
            rendered_html = rendered_html.replace(f"[{key.capitalize()}]", str(val))
            rendered_html = rendered_html.replace(f"[{key.upper()}]", str(val))

            rendered_text = rendered_text.replace(f"[{key}]", str(val))
            rendered_text = rendered_text.replace(f"[{key.capitalize()}]", str(val))
            rendered_text = rendered_text.replace(f"[{key.upper()}]", str(val))

        return rendered_html, rendered_text
