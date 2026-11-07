import re
from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass
class Inconsistencia:
    linha: int
    campo: str
    valor: str
    tipo: str        # "erro" | "aviso"
    descricao: str
    sugestao: str


# Quantidade máxima permitida por paciente/competência para cada procedimento
LIMITES_QTD: dict[str, int] = {
    "0101010010": 1,   # Consulta médica em atenção básica
    "0202010295": 2,   # Hemograma completo
    "0205020097": 1,   # TC de crânio
    "0301010110": 4,   # Psicoterapia individual
}

# Faixa etária permitida (idade_min, idade_max) por procedimento
RESTRICOES_IDADE: dict[str, tuple[int, int]] = {
    "0101060120": (0, 11),    # Consulta pediátrica
    "0301010110": (18, 120),  # Psicoterapia individual — apenas adultos
    "0211060100": (60, 120),  # Procedimentos exclusivos para idosos
}

# CIDs com restrição de sexo: "F" = feminino, "M" = masculino
CID_SEXO: dict[str, str] = {
    "N70": "F", "N71": "F", "N72": "F", "N73": "F", "N74": "F",
    "N80": "F", "N81": "F", "N82": "F", "N83": "F",
    "Z34": "F", "Z35": "F",
    "N40": "M", "N41": "M", "N42": "M", "N43": "M", "N44": "M",
    "O": "F",   # prefixo único: capítulo Obstetrícia
}


def _validar_cns(cns: str) -> bool:
    """Validação simplificada do CNS: 15 dígitos, início válido, não repetido."""
    cns = cns.strip()
    return (
        len(cns) == 15
        and cns.isdigit()
        and cns[0] in "12789"
        and len(set(cns)) > 1
    )


def _validar_cid(cid: str) -> bool:
    return bool(re.match(r"^[A-Z][0-9]{2}(\.[0-9]{1,2})?$", cid.upper()))


def _calcular_idade(nasc: str, comp: str) -> Optional[int]:
    try:
        d = date(int(nasc[:4]), int(nasc[4:6]), int(nasc[6:8]))
        ref = date(int(comp[:4]), int(comp[4:6]), 1)
        return ref.year - d.year - ((ref.month, 1) < (d.month, d.day))
    except Exception:
        return None


def auditar_registros(
    registros: list[dict],
) -> tuple[list[dict], list[Inconsistencia]]:
    inconsistencias: list[Inconsistencia] = []
    vistos: dict[str, int] = {}

    for i, r in enumerate(registros):
        ln = i + 2  # linha 1 é o cabeçalho

        cns = r.get("cns_paciente", "")
        cid = r.get("cid", "").upper()
        proc = r.get("procedimento", "")
        comp = r.get("competencia", "")
        nasc = r.get("data_nascimento", "")
        sexo = r.get("sexo", "").upper()

        # 1. CNS
        if not _validar_cns(cns):
            inconsistencias.append(Inconsistencia(
                linha=ln, campo="cns_paciente", valor=cns, tipo="erro",
                descricao=f"CNS '{cns}' inválido. Deve ter 15 dígitos e iniciar com 1, 2, 7, 8 ou 9.",
                sugestao="Verificar o CNS correto no CADWEB ou solicitar nova emissão ao CADSUS.",
            ))

        # 2. CID-10
        if not _validar_cid(cid):
            inconsistencias.append(Inconsistencia(
                linha=ln, campo="cid", valor=cid, tipo="erro",
                descricao=f"CID-10 '{cid}' fora do padrão (ex: J06.9, I10, Z00.0).",
                sugestao="Consultar tabela CID-10 no DATASUS e corrigir o código.",
            ))

        # 3. Código SIGTAP
        if not proc.isdigit() or len(proc) != 10:
            inconsistencias.append(Inconsistencia(
                linha=ln, campo="procedimento", valor=proc, tipo="erro",
                descricao=f"Código SIGTAP '{proc}' inválido. Deve ter exatamente 10 dígitos.",
                sugestao="Consultar o procedimento na tabela SIGTAP vigente para a competência.",
            ))

        # 4. Quantidade
        try:
            qtd = int(r.get("quantidade", 0))
            if qtd <= 0:
                raise ValueError
            # 4b. Limite por procedimento
            if proc in LIMITES_QTD and qtd > LIMITES_QTD[proc]:
                lim = LIMITES_QTD[proc]
                inconsistencias.append(Inconsistencia(
                    linha=ln, campo="quantidade", valor=str(qtd), tipo="erro",
                    descricao=f"Quantidade {qtd} excede o limite de {lim}/mês para o procedimento {proc}.",
                    sugestao=f"Reduzir para máximo {lim} ou anexar laudo de excepcionalidade.",
                ))
        except (ValueError, TypeError):
            inconsistencias.append(Inconsistencia(
                linha=ln, campo="quantidade", valor=str(r.get("quantidade", "")), tipo="erro",
                descricao="Quantidade deve ser um número inteiro positivo.",
                sugestao="Corrigir com o valor real de procedimentos realizados.",
            ))

        # 5. Restrição de idade por procedimento
        if proc in RESTRICOES_IDADE and nasc and comp:
            idade = _calcular_idade(nasc, comp)
            if idade is not None:
                mn, mx = RESTRICOES_IDADE[proc]
                if not (mn <= idade <= mx):
                    inconsistencias.append(Inconsistencia(
                        linha=ln, campo="procedimento", valor=proc, tipo="erro",
                        descricao=(
                            f"Procedimento {proc} não permitido para paciente com {idade} anos "
                            f"(faixa autorizada: {mn}–{mx} anos)."
                        ),
                        sugestao="Revisar procedimento no prontuário ou atualizar cadastro do paciente.",
                    ))

        # 6. Restrição de sexo por CID
        cid3, cid1 = cid[:3], cid[:1]
        restricao = CID_SEXO.get(cid3) or CID_SEXO.get(cid1)
        if restricao and sexo and sexo != restricao:
            esperado = "Feminino" if restricao == "F" else "Masculino"
            inconsistencias.append(Inconsistencia(
                linha=ln, campo="cid", valor=cid, tipo="erro",
                descricao=f"CID '{cid}' é restrito ao sexo {esperado}. Registro indica sexo '{sexo}'.",
                sugestao="Verificar CID e dados do paciente no prontuário físico.",
            ))

        # 7. Duplicata
        chave = f"{r.get('cnes')}-{cns}-{proc}-{comp}"
        if chave in vistos:
            inconsistencias.append(Inconsistencia(
                linha=ln, campo="registro", valor=chave[:35], tipo="aviso",
                descricao=(
                    f"Registro duplicado: mesma combinação CNES+CNS+procedimento+competência "
                    f"já aparece na linha {vistos[chave]}."
                ),
                sugestao="Verificar duplo lançamento e excluir o registro redundante.",
            ))
        else:
            vistos[chave] = ln

        # 8. Competência (Portaria GM/MS nº 10.297/2026)
        if comp:
            try:
                ano, mes = int(comp[:4]), int(comp[4:6])
                if not (1 <= mes <= 12) or ano < 2020 or ano > 2030:
                    raise ValueError
            except Exception:
                inconsistencias.append(Inconsistencia(
                    linha=ln, campo="competencia", valor=comp, tipo="erro",
                    descricao=f"Competência '{comp}' inválida. Formato esperado: AAAAMM (ex: 202604).",
                    sugestao="Corrigir para o mês/ano de referência conforme Portaria GM/MS nº 10.297/2026.",
                ))

    return registros, inconsistencias
