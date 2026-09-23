import re
from typing import Optional, Dict, Any, List
from config import (
    SPREADSHEET_ID,
    SHEET_GID,
    FORM_RESPONSES_GID,
    FORM_RESPONSES_TAB,
    COL_EMAIL,
    COL_NAME,
    COL_COMPANY,
    COL_CNAE,
    COL_CNPJ,
    COL_SEND_TIME,
    COL_STATUS,
    STATUS_NOVO,
    STATUS_EM_CONTATO,
    STATUS_DIAGNOSTICO_ACEITO,
    STATUS_SEM_INTERESSE,
)


def col_index_to_letter(col_idx: int) -> str:
    """Converte índice numérico de coluna (0 = A, 1 = B, 26 = AA) para letra A1."""
    result = ""
    col_idx += 1
    while col_idx > 0:
        col_idx, remainder = divmod(col_idx - 1, 26)
        result = chr(65 + remainder) + result
    return result


def normalize_digits(value: Any) -> str:
    """Extrai somente os dígitos numéricos de uma string ou número."""
    return re.sub(r"\D", "", str(value or ""))


class SheetsClient:
    def __init__(
        self,
        service,
        spreadsheet_id: str = SPREADSHEET_ID,
        gid: str = SHEET_GID,
        form_gid: str = FORM_RESPONSES_GID,
    ):
        self.service = service
        self.spreadsheet_id = spreadsheet_id
        self.gid = str(gid)
        self.form_gid = str(form_gid)

        # Resolução dos nomes reais das abas
        self.sheet_title = self._resolve_sheet_title(self.gid, default_title="LEADS")
        self.form_title = self._resolve_sheet_title(self.form_gid, default_title=FORM_RESPONSES_TAB)
        self.columns_map = {}

    def _resolve_sheet_title(self, target_gid: str, default_title: str) -> str:
        """Descobre o nome real da aba a partir do GID numérico com fallback seguro."""
        try:
            metadata = (
                self.service.spreadsheets()
                .get(
                    spreadsheetId=self.spreadsheet_id,
                    fields="sheets(properties(sheetId,title))",
                )
                .execute()
            )
            sheets = metadata.get("sheets", [])
            for s in sheets:
                props = s.get("properties", {})
                if str(props.get("sheetId")) == str(target_gid):
                    title = props.get("title")
                    return title

            for s in sheets:
                props = s.get("properties", {})
                if props.get("title", "").strip().lower() == default_title.strip().lower():
                    return props.get("title")

            if sheets:
                return sheets[0].get("properties", {}).get("title", default_title)
        except Exception as e:
            print(f"[!] Erro ao resolver nome da aba (GID {target_gid}): {e}")

        return default_title

    def read_all_rows(self) -> List[List[str]]:
        """Lê todas as linhas da aba principal de LEADS."""
        range_name = f"'{self.sheet_title}'!A1:ZZ"
        result = (
            self.service.spreadsheets()
            .values()
            .get(spreadsheetId=self.spreadsheet_id, range=range_name)
            .execute()
        )
        return result.get("values", [])

    def map_columns(self, header_row: List[str]) -> Dict[str, int]:
        """
        Mapeia os cabeçalhos de coluna de forma flexível e inteligente.
        Retorna dicionário com os índices das colunas.
        """
        mapping = {}
        for idx, col in enumerate(header_row):
            col_clean = str(col).strip().lower()

            # E-mail
            if any(term in col_clean for term in ["e-mail", "email", "mail", "correio"]):
                mapping["email"] = idx

            # Hora de Envio
            if ("hora" in col_clean and "envio" in col_clean) or col_clean == COL_SEND_TIME.lower():
                mapping["hora_envio"] = idx

            # Status do Contato
            if "status" in col_clean or col_clean == COL_STATUS.lower():
                mapping["status"] = idx

            # Nome do Contato / Responsável
            if any(term in col_clean for term in ["nome", "contato", "cliente", "lead"]) and "empresa" not in col_clean and "status" not in col_clean:
                mapping["nome"] = idx

            # Empresa / Razão Social
            if any(term in col_clean for term in ["empresa", "negócio", "negocio", "loja", "organização", "razão social", "razao social"]):
                mapping["empresa"] = idx

            # CNPJ
            if "cnpj" in col_clean or col_clean == COL_CNPJ.lower():
                mapping["cnpj"] = idx

            # Nicho / Segmento
            if any(term in col_clean for term in ["nicho", "segmento", "ramo", "setor"]):
                mapping["nicho"] = idx

            # CNAE Principal
            if "cnae" in col_clean or col_clean == COL_CNAE.lower():
                mapping["cnae"] = idx

            # Cidade / Município
            if "cidade" in col_clean or "município" in col_clean or "municipio" in col_clean:
                mapping["cidade"] = idx

            # Gancho de Abordagem
            if "gancho" in col_clean or "abordagem" in col_clean:
                mapping["gancho"] = idx

            # Telefone / Celular
            if any(term in col_clean for term in ["telefone", "celular", "whatsapp", "fone", "tel"]):
                mapping["telefone"] = idx

        self.columns_map = mapping
        return mapping

    def get_column_letters(self) -> Dict[str, str]:
        """Retorna as letras das colunas mapeadas (ex: {'hora_envio': 'I', 'status': 'J'})."""
        return {k: col_index_to_letter(v) for k, v in self.columns_map.items()}

    def get_next_pending_lead(self) -> Optional[Dict[str, Any]]:
        """
        Encontra o próximo lead pendente de envio.
        Condições:
        - E-mail preenchido e válido
        - 'Hora de Envio' vazia
        - 'Status do Contato' vazio ou igual a 'Novo'
        """
        rows = self.read_all_rows()
        if not rows:
            print("[!] A planilha está vazia.")
            return None

        headers = rows[0]
        self.map_columns(headers)

        if "email" not in self.columns_map:
            raise ValueError("Coluna de E-mail não foi encontrada no cabeçalho da planilha!")
        if "hora_envio" not in self.columns_map:
            raise ValueError(f"Coluna '{COL_SEND_TIME}' não encontrada no cabeçalho da planilha!")
        if "status" not in self.columns_map:
            raise ValueError(f"Coluna '{COL_STATUS}' não encontrada no cabeçalho da planilha!")

        email_idx = self.columns_map["email"]
        hora_idx = self.columns_map["hora_envio"]
        status_idx = self.columns_map["status"]
        nome_idx = self.columns_map.get("nome")
        empresa_idx = self.columns_map.get("empresa")
        cnae_idx = self.columns_map.get("cnae")
        cnpj_idx = self.columns_map.get("cnpj")

        email_regex = re.compile(r"^[\w\.-]+@[\w\.-]+\.\w+$")

        for row_idx, row in enumerate(rows[1:], start=2):
            email = row[email_idx].strip() if email_idx < len(row) else ""
            hora_envio = row[hora_idx].strip() if hora_idx < len(row) else ""
            status = row[status_idx].strip() if status_idx < len(row) else ""

            is_hora_empty = not hora_envio
            is_status_pending = status == "" or status.lower() == STATUS_NOVO.lower()

            if email and email_regex.match(email) and is_hora_empty and is_status_pending:
                nome = row[nome_idx].strip() if (nome_idx is not None and nome_idx < len(row)) else ""
                empresa = row[empresa_idx].strip() if (empresa_idx is not None and empresa_idx < len(row)) else ""
                cnae = row[cnae_idx].strip() if (cnae_idx is not None and cnae_idx < len(row)) else ""
                cnpj = row[cnpj_idx].strip() if (cnpj_idx is not None and cnpj_idx < len(row)) else ""

                lead_data = {
                    "row_number": row_idx,
                    "email": email,
                    "nome": nome,
                    "empresa": empresa,
                    "cnae": cnae,
                    "cnpj": cnpj,
                    "status_atual": status,
                    "raw_row": {headers[i]: row[i] for i in range(min(len(headers), len(row)))},
                }
                return lead_data

        return None

    def update_lead_sent(self, row_number: int, send_time_str: str, new_status: str = STATUS_EM_CONTATO):
        """
        Atualiza a planilha após o envio com sucesso:
        - Coluna 'Hora de Envio' -> 'xx/xx/xxxx às yy:yy'
        - Coluna 'Status do Contato' -> 'Em Contato'
        """
        if not self.columns_map:
            rows = self.read_all_rows()
            if rows:
                self.map_columns(rows[0])

        hora_col_letter = col_index_to_letter(self.columns_map["hora_envio"])
        status_col_letter = col_index_to_letter(self.columns_map["status"])

        data = [
            {
                "range": f"'{self.sheet_title}'!{hora_col_letter}{row_number}",
                "values": [[send_time_str]],
            },
            {
                "range": f"'{self.sheet_title}'!{status_col_letter}{row_number}",
                "values": [[new_status]],
            },
        ]

        body = {
            "valueInputOption": "USER_ENTERED",
            "data": data,
        }

        self.service.spreadsheets().values().batchUpdate(
            spreadsheetId=self.spreadsheet_id,
            body=body,
        ).execute()

        print(f"[OK] Planilha atualizada (Linha {row_number}): {COL_SEND_TIME}='{send_time_str}', {COL_STATUS}='{new_status}'")

    def update_lead_status(self, row_number: int, new_status: str):
        """Atualiza somente o 'Status do Contato' de uma linha específica na aba LEADS."""
        if not self.columns_map:
            rows = self.read_all_rows()
            if rows:
                self.map_columns(rows[0])

        status_col_letter = col_index_to_letter(self.columns_map["status"])
        range_str = f"'{self.sheet_title}'!{status_col_letter}{row_number}"

        self.service.spreadsheets().values().update(
            spreadsheetId=self.spreadsheet_id,
            range=range_str,
            valueInputOption="USER_ENTERED",
            body={"values": [[new_status]]},
        ).execute()

        print(f"[OK] Status da linha {row_number} atualizado para: '{new_status}'")

    def get_contacted_leads(self) -> List[Dict[str, Any]]:
        """Retorna lista de leads que estão atualmente em contato para monitorar respostas no Gmail."""
        rows = self.read_all_rows()
        if not rows:
            return []

        headers = rows[0]
        self.map_columns(headers)

        if "email" not in self.columns_map or "status" not in self.columns_map:
            return []

        email_idx = self.columns_map["email"]
        status_idx = self.columns_map["status"]
        hora_idx = self.columns_map.get("hora_envio")
        nome_idx = self.columns_map.get("nome")
        empresa_idx = self.columns_map.get("empresa")

        contacted = []
        for row_idx, row in enumerate(rows[1:], start=2):
            email = row[email_idx].strip() if email_idx < len(row) else ""
            status = row[status_idx].strip() if status_idx < len(row) else ""
            hora = row[hora_idx].strip() if (hora_idx is not None and hora_idx < len(row)) else ""

            if email and (status.lower() == STATUS_EM_CONTATO.lower() or (hora and status.lower() != STATUS_SEM_INTERESSE.lower())):
                nome = row[nome_idx].strip() if (nome_idx is not None and nome_idx < len(row)) else ""
                empresa = row[empresa_idx].strip() if (empresa_idx is not None and empresa_idx < len(row)) else ""
                contacted.append({
                    "row_number": row_idx,
                    "email": email,
                    "nome": nome,
                    "empresa": empresa,
                    "hora_envio": hora,
                    "status": status,
                })

        return contacted

    def check_form_responses(self) -> List[Dict[str, Any]]:
        """
        Lê a aba 'Respostas ao formulário 1' e faz cruzamento automático com a aba 'LEADS':
        - Busca respostas com CNPJ preenchido.
        - Se o CNPJ constar na aba 'LEADS' e o status ainda não for 'Diagnóstico Aceito':
          Atualiza automaticamente o Status do Contato para 'Diagnóstico Aceito'.
        Retorna a lista de leads recém-convertidos.
        """
        try:
            form_range = f"'{self.form_title}'!A1:Z"
            form_res = (
                self.service.spreadsheets()
                .values()
                .get(spreadsheetId=self.spreadsheet_id, range=form_range)
                .execute()
            )
            form_rows = form_res.get("values", [])
            if len(form_rows) <= 1:
                return []

            form_headers = [str(h).strip().lower() for h in form_rows[0]]

            # Localiza colunas de CNPJ, Contratante e Data na aba do formulário
            form_cnpj_idx = None
            form_name_idx = None
            form_date_idx = None

            for i, h in enumerate(form_headers):
                if "cnpj" in h:
                    form_cnpj_idx = i
                elif any(t in h for t in ["contratante", "nome"]):
                    form_name_idx = i
                elif any(t in h for t in ["carimbo", "data"]):
                    form_date_idx = i

            if form_cnpj_idx is None:
                return []

            # Lê todas as linhas da aba LEADS para cruzar por CNPJ
            leads_rows = self.read_all_rows()
            if not leads_rows:
                return []

            self.map_columns(leads_rows[0])
            leads_cnpj_idx = self.columns_map.get("cnpj")
            leads_status_idx = self.columns_map.get("status")
            leads_empresa_idx = self.columns_map.get("empresa")

            if leads_cnpj_idx is None or leads_status_idx is None:
                return []

            # Cria índice de CNPJs na aba LEADS: cnpj_digits -> (row_number, empresa, status)
            leads_by_cnpj: Dict[str, Dict[str, Any]] = {}
            for r_idx, r in enumerate(leads_rows[1:], start=2):
                r_cnpj = r[leads_cnpj_idx] if leads_cnpj_idx < len(r) else ""
                r_status = r[leads_status_idx] if leads_status_idx < len(r) else ""
                r_empresa = r[leads_empresa_idx] if (leads_empresa_idx is not None and leads_empresa_idx < len(r)) else ""
                
                cnpj_digits = normalize_digits(r_cnpj)
                if cnpj_digits:
                    leads_by_cnpj[cnpj_digits] = {
                        "row_number": r_idx,
                        "empresa": r_empresa,
                        "status": r_status,
                    }

            newly_diagnosed = []

            # Itera sobre as respostas do formulário
            for f_row in form_rows[1:]:
                resp_cnpj = f_row[form_cnpj_idx] if form_cnpj_idx < len(f_row) else ""
                resp_digits = normalize_digits(resp_cnpj)
                if not resp_digits:
                    continue

                resp_name = f_row[form_name_idx] if (form_name_idx is not None and form_name_idx < len(f_row)) else ""
                resp_date = f_row[form_date_idx] if (form_date_idx is not None and form_date_idx < len(f_row)) else ""

                if resp_digits in leads_by_cnpj:
                    lead_info = leads_by_cnpj[resp_digits]
                    current_status = lead_info["status"]

                    if current_status != STATUS_DIAGNOSTICO_ACEITO:
                        row_to_update = lead_info["row_number"]
                        self.update_lead_status(row_to_update, STATUS_DIAGNOSTICO_ACEITO)
                        lead_info["status"] = STATUS_DIAGNOSTICO_ACEITO

                        conversion = {
                            "row_number": row_to_update,
                            "empresa": lead_info["empresa"],
                            "cnpj": resp_cnpj,
                            "contratante": resp_name,
                            "data": resp_date,
                        }
                        newly_diagnosed.append(conversion)

            return newly_diagnosed

        except Exception as e:
            print(f"[!] Erro ao verificar respostas do formulário: {e}")
            return []
