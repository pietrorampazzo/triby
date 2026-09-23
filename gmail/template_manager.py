from pathlib import Path
from config import TEMPLATE_HTML, TEMPLATE_TXT, SENDER_NAME, CNAE_GROUPS


class TemplateManager:
    def __init__(self, fallback_html: Path = TEMPLATE_HTML, fallback_txt: Path = TEMPLATE_TXT):
        self.fallback_html_path = fallback_html
        self.fallback_txt_path = fallback_txt

        # Carrega fallbacks (opcional, já que vamos ignorar se não tiver CNAE)
        self.fallback_html_raw = self._read_file(fallback_html)
        self.fallback_txt_raw = self._read_file(fallback_txt)

        # Carrega grupos
        self.groups_data = {}
        for group_id, group_config in CNAE_GROUPS.items():
            self.groups_data[group_id] = {
                "cnaes": group_config["cnaes"],
                "subject": group_config["subject"],
                "html_raw": self._read_file(group_config["template_html"]),
                "txt_raw": self._read_file(group_config["template_txt"]),
            }

    def _read_file(self, file_path: Path) -> str:
        if not file_path.exists():
            print(f"[Aviso] Template não encontrado em: {file_path}")
            return ""
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    def get_template_for_cnae(self, cnae: str):
        """Retorna (subject, html_raw, txt_raw) baseando-se no CNAE do lead."""
        cnae_clean = str(cnae).strip()
        if not cnae_clean:
            return None, None, None

        for group_id, data in self.groups_data.items():
            # Tenta verificar se o CNAE limpo do lead está em algum grupo
            if cnae_clean in data["cnaes"]:
                return data["subject"], data["html_raw"], data["txt_raw"]
            # Ou faz match parcial (ex: "4530-7" in "4530-7/03")
            for cnae_target in data["cnaes"]:
                if cnae_clean in cnae_target or cnae_target in cnae_clean:
                    return data["subject"], data["html_raw"], data["txt_raw"]
        
        return None, None, None

    def render(self, lead_data: dict, sender_name: str = "") -> tuple[str, str, str]:
        """
        Substitui as variáveis nos templates com dados do lead.
        Retorna (rendered_subject, rendered_html, rendered_text).
        Se CNAE for inválido ou vazio, retorna (None, None, None).
        """
        # Trata CNAE
        cnae = lead_data.get("cnae") or lead_data.get("CNAE") or ""
        subject_raw, html_raw, txt_raw = self.get_template_for_cnae(cnae)

        if subject_raw is None:
            return None, None, None

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
            "cnae": cnae,
        }

        # Adiciona quaisquer outros campos existentes na linha sem sobrescrever os tratados
        for k, v in lead_data.items():
            k_lower = str(k).lower().strip()
            if k_lower not in context:
                context[k_lower] = str(v)

        rendered_subject = subject_raw
        rendered_html = html_raw
        rendered_text = txt_raw

        for key, val in context.items():
            # Suporta variações para Subject
            rendered_subject = rendered_subject.replace(f"{{{key}}}", str(val))
            rendered_subject = rendered_subject.replace(f"{{{key.capitalize()}}}", str(val))
            rendered_subject = rendered_subject.replace(f"{{{key.upper()}}}", str(val))

            # Suporta variações para Body (Chaves)
            rendered_html = rendered_html.replace(f"{{{key}}}", str(val))
            rendered_html = rendered_html.replace(f"{{{key.capitalize()}}}", str(val))
            rendered_html = rendered_html.replace(f"{{{key.upper()}}}", str(val))

            rendered_text = rendered_text.replace(f"{{{key}}}", str(val))
            rendered_text = rendered_text.replace(f"{{{key.capitalize()}}}", str(val))
            rendered_text = rendered_text.replace(f"{{{key.upper()}}}", str(val))

            # Suporta variações para Body (Colchetes)
            rendered_html = rendered_html.replace(f"[{key}]", str(val))
            rendered_html = rendered_html.replace(f"[{key.capitalize()}]", str(val))
            rendered_html = rendered_html.replace(f"[{key.upper()}]", str(val))

            rendered_text = rendered_text.replace(f"[{key}]", str(val))
            rendered_text = rendered_text.replace(f"[{key.capitalize()}]", str(val))
            rendered_text = rendered_text.replace(f"[{key.upper()}]", str(val))

        return rendered_subject, rendered_html, rendered_text
