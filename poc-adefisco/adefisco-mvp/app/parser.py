import csv
from typing import TextIO

CAMPOS_ESPERADOS = [
    "cnes", "competencia", "cns_paciente", "data_nascimento",
    "sexo", "cbo", "cid", "procedimento", "quantidade", "valor_unitario",
]


def parse_bpa_csv(stream: TextIO) -> list[dict]:
    reader = csv.DictReader(stream)
    registros = []
    for row in reader:
        normalizado = {
            k.strip().lower().replace(" ", "_"): str(v).strip() if v is not None else ""
            for k, v in row.items()
        }
        if any(normalizado.get(c) for c in CAMPOS_ESPERADOS):
            registros.append(normalizado)
    return registros
