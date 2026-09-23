import re
from typing import Optional, Dict, Any, List
from config import (
    SPREADSHEET_ID,
    SHEET_GID,
    COL_EMAIL,
    COL_NAME,
    COL_COMPANY,
    COL_SEND_TIME,
    COL_STATUS,
    STATUS_NOVO,
    STATUS_EM_CONTATO,
)


def col_index_to_letter(col_idx: int) -> str:
    """Converte índice numérico de coluna (0 = A, 1 = B, 26 = AA) para letra A1."""
    result = ""
    col_idx += 1
    while col_idx > 0:
        col_idx, remainder = divmod(col_idx - 1, 26)
        result = chr(65 + remainder) + result
    return result


class SheetsClient:
    def __init__(self, service, spreadsheet_id: str = SPREADSHEET_ID, gid: str = SHEET_GID):
        self.service = service
        self.spreadsheet_id = spreadsheet_id
        self.gid = str(gid)
        self.sheet_title = self._resolve_sheet_title()
        self.columns_map = {}

    def _resolve_sheet_title(self) -> str:
        """Descobre o nome real da aba (ex: 'Página1' ou 'Leads') a partir do GID numérico."""
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
                if str(props.get("sheetId")) == self.gid:
                    title = props.get("title")
                    print(f"[*] Aba identificada pelo GID {self.gid}: '{title}'")
                    return title

            # Se não encontrar pelo GID, usa a primeira aba
            if sheets:
                fallback_title = sheets[0].get("properties", {}).get("title", "Página1")
                print(f"[!] GID {self.gid} não encontrado. Usando a primeira aba: '{fallback_title}'")
                return fallback_title
        except Exception as e:
            print(f"[!] Erro ao resolver nome da aba: {e}")

        return "Página1"

    def read_all_rows(self) -> List[List[str]]:
        """Lê todas as linhas da aba configurada."""
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

            # Mapeamento do E-mail
            if any(term in col_clean for term in ["e-mail", "email", "mail", "correio"]):
                mapping["email"] = idx

            # Mapeamento da Hora de Envio
            if ("hora" in col_clean and "envio" in col_clean) or col_clean == COL_SEND_TIME.lower():
                mapping["hora_envio"] = idx

            # Mapeamento do Status do Contato
            if "status" in col_clean or col_clean == COL_STATUS.lower():
                mapping["status"] = idx

            # Mapeamento do Nome (garante que não confunda com 'Status do Contato')
            if any(term in col_clean for term in ["nome", "contato", "cliente", "lead"]) and "empresa" not in col_clean and "status" not in col_clean:
                mapping["nome"] = idx

            # Mapeamento da Empresa
            if any(term in col_clean for term in ["empresa", "negócio", "negocio", "loja", "organização", "razão social", "razao social"]):
                mapping["empresa"] = idx

            # Mapeamento de Nicho / Segmento
            if any(term in col_clean for term in ["nicho", "segmento", "ramo", "setor"]):
                mapping["nicho"] = idx

            # Mapeamento de CNAE
            if "cnae" in col_clean:
                mapping["cnae"] = idx

            # Mapeamento de Cidade
            if "cidade" in col_clean or "município" in col_clean or "municipio" in col_clean:
                mapping["cidade"] = idx

            # Mapeamento de Gancho de Abordagem
            if "gancho" in col_clean or "abordagem" in col_clean:
                mapping["gancho"] = idx

        self.columns_map = mapping
        return mapping

    def get_column_letters(self) -> Dict[str, str]:
        """Retorna as letras das colunas mapeadas (ex: {'hora_envio': 'G', 'status': 'H'})."""
        return {k: col_index_to_letter(v) for k, v in self.columns_map.items()}

    def get_next_pending_lead(self) -> Optional[Dict[str, Any]]:
        """
        Encontra o próximo lead pendente de envio.
        Condições:
        - E-mail válido preenchido
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

        email_regex = re.compile(r"^[\w\.-]+@[\w\.-]+\.\w+$")

        for row_idx, row in enumerate(rows[1:], start=2):  # Linha 1 é cabeçalho; dados começam na linha 2
            email = row[email_idx].strip() if email_idx < len(row) else ""
            hora_envio = row[hora_idx].strip() if hora_idx < len(row) else ""
            status = row[status_idx].strip() if status_idx < len(row) else ""

            # Verifica se é um lead pendente
            is_hora_empty = not hora_envio
            is_status_pending = status == "" or status.lower() == STATUS_NOVO.lower()

            if email and email_regex.match(email) and is_hora_empty and is_status_pending:
                nome = row[nome_idx].strip() if (nome_idx is not None and nome_idx < len(row)) else ""
                empresa = row[empresa_idx].strip() if (empresa_idx is not None and empresa_idx < len(row)) else ""

                lead_data = {
                    "row_number": row_idx,
                    "email": email,
                    "nome": nome,
                    "empresa": empresa,
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

    def get_contacted_leads(self) -> List[Dict[str, Any]]:
        """
        Retorna a lista de leads que estão atualmente em contato para monitorar respostas no Gmail.
        """
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

            # Lead está em contato se o status for "Em Contato" ou se tiver hora de envio registrada
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
