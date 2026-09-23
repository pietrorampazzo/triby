import re
from pathlib import Path
from config import TEMPLATE_HTML, TEMPLATE_TXT, SENDER_NAME, CNAE_GROUPS, EMAIL_SUBJECT


class TemplateManager:
    def __init__(self, fallback_html: Path = TEMPLATE_HTML, fallback_txt: Path = TEMPLATE_TXT):
        self.fallback_html_path = fallback_html
        self.fallback_txt_path = fallback_txt

        # Carrega templates de fallback padrão
        self.fallback_html_raw = self._read_file(fallback_html)
        self.fallback_txt_raw = self._read_file(fallback_txt)

        # Carrega grupos de CNAE segmentados
        self.groups_data = {}
        for group_id, group_config in CNAE_GROUPS.items():
            self.groups_data[group_id] = {
                "nome": group_config.get("nome", group_id),
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

    def get_template_for_cnae(self, cnae: str) -> tuple[str, str, str]:
        """
        Retorna (subject, html_raw, txt_raw) baseando-se no CNAE do lead.
        Se o CNAE pertencer a um grupo segmentado, retorna o template específico do grupo.
        Caso contrário, utiliza o template institucional padrão como fallback.
        """
        cnae_str = str(cnae).strip()
        cnae_digits = re.sub(r"\D", "", cnae_str)

        if cnae_digits:
            for group_id, data in self.groups_data.items():
                for cnae_target in data["cnaes"]:
                    target_digits = re.sub(r"\D", "", str(cnae_target))
                    # Match exato de 7 dígitos ou match de prefixo (ex: 45307 em 4530703)
                    if target_digits and (
                        target_digits == cnae_digits
                        or (len(target_digits) >= 5 and cnae_digits.startswith(target_digits))
                        or (len(cnae_digits) >= 5 and target_digits.startswith(cnae_digits))
                    ):
                        return data["subject"], data["html_raw"], data["txt_raw"]
                    # Match textual
                    if str(cnae_target).lower() in cnae_str.lower():
                        return data["subject"], data["html_raw"], data["txt_raw"]

        # Se não casou com nenhum grupo segmentado, retorna o template padrão institucional
        return EMAIL_SUBJECT, self.fallback_html_raw, self.fallback_txt_raw

    def render(self, lead_data: dict, sender_name: str = "") -> tuple[str, str, str]:
        """
        Substitui as variáveis nos templates com dados do lead.
        Retorna (rendered_subject, rendered_html, rendered_text).
        Garante que sempre haverá um template válido para envio.
        """
        # Extrai CNAE de chaves prováveis
        cnae = ""
        for key in ["CNAE Principal", "cnae_principal", "cnae", "CNAE", "cnae principal"]:
            val = lead_data.get(key)
            if val:
                cnae = str(val).strip()
                break

        subject_raw, html_raw, txt_raw = self.get_template_for_cnae(cnae)

        # Trata empresa
        company = ""
        for key in ["Empresa", "empresa", "Razão Social", "razao social", "Negócio", "negocio"]:
            val = lead_data.get(key)
            if val:
                company = str(val).strip()
                break
        if not company:
            company = "sua empresa"

        # Trata nome da pessoa (se houver) ou usa primeiro termo da empresa
        full_name = ""
        for key in ["Nome", "nome", "Contato", "contato", "Cliente", "cliente"]:
            val = lead_data.get(key)
            if val:
                full_name = str(val).strip()
                break

        if full_name:
            first_name = full_name.split()[0]
        else:
            first_name = company if company != "sua empresa" else "Equipe"

        # Remetente
        remetente = sender_name or SENDER_NAME or "Pietro"

        context = {
            "nome": first_name,
            "nome_completo": full_name or first_name,
            "empresa": company,
            "email": str(lead_data.get("E-mail") or lead_data.get("email") or "").strip(),
            "cidade": str(lead_data.get("Cidade") or lead_data.get("cidade") or "").strip(),
            "nicho": str(lead_data.get("Nicho / Segmento") or lead_data.get("nicho") or "").strip(),
            "cnae": cnae,
            "cnae_principal": cnae,
            "gancho": str(lead_data.get("Gancho de Abordagem") or lead_data.get("gancho") or "").strip(),
            "cnpj": str(lead_data.get("CNPJ") or lead_data.get("cnpj") or "").strip(),
            "remetente": remetente,
        }

        # Adiciona quaisquer outros campos existentes na linha sem sobrescrever
        for k, v in lead_data.items():
            k_clean = str(k).lower().strip()
            if k_clean not in context:
                context[k_clean] = str(v).strip()

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
