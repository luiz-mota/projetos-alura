from datetime import datetime


def gerar_relatorio_html(
    registros: list[dict],
    inconsistencias: list,
    analise_ia: str | None,
    audit_id: str,
    filename: str,
) -> str:
    data = datetime.now().strftime("%d/%m/%Y %H:%M")
    erros = [i for i in inconsistencias if i.tipo == "erro"]
    avisos = [i for i in inconsistencias if i.tipo == "aviso"]
    total = len(registros)
    pct = round((1 - len(erros) / max(total, 1)) * 100, 1)
    cor_pct = "#00c48c" if pct >= 90 else "#febc2e" if pct >= 70 else "#ff5f57"

    def badge(tipo: str) -> str:
        cor = "#ff5f57" if tipo == "erro" else "#febc2e"
        return (
            f'<span style="background:{cor}22;color:{cor};padding:2px 8px;'
            f'border-radius:4px;font-size:.72rem;font-weight:700">{tipo.upper()}</span>'
        )

    linhas_inc = "".join(
        f"<tr>"
        f"<td>{i.linha}</td>"
        f"<td>{i.campo}</td>"
        f"<td><code>{str(i.valor)[:30]}</code></td>"
        f"<td>{badge(i.tipo)}</td>"
        f"<td>{i.descricao}</td>"
        f"<td style='color:#6b85a3;font-size:.8rem'>{i.sugestao}</td>"
        f"</tr>"
        for i in inconsistencias
    )

    linhas_reg = "".join(
        f"<tr>"
        f"<td>{r.get('cnes','')}</td>"
        f"<td>{r.get('competencia','')}</td>"
        f"<td>{r.get('cns_paciente','')}</td>"
        f"<td>{r.get('sexo','')}</td>"
        f"<td>{r.get('cid','')}</td>"
        f"<td>{r.get('procedimento','')}</td>"
        f"<td>{r.get('quantidade','')}</td>"
        f"<td>R$ {r.get('valor_unitario','')}</td>"
        f"</tr>"
        for r in registros
    )

    ia_bloco = ""
    if analise_ia:
        ia_bloco = f"""
        <div style="background:#0a1628;border:1px solid rgba(0,196,140,.25);border-radius:12px;padding:1.5rem;margin:2rem 0">
          <h3 style="color:#00c48c;font-size:.95rem;margin-bottom:.8rem">🤖 Análise da IA ADEFISCO</h3>
          <pre style="color:#b0c4d8;font-size:.875rem;line-height:1.75;white-space:pre-wrap;font-family:'Segoe UI',system-ui,sans-serif">{analise_ia}</pre>
        </div>"""

    tabela_inc = (
        f"""<table>
          <thead><tr>
            <th>Linha</th><th>Campo</th><th>Valor</th><th>Tipo</th>
            <th>Descrição</th><th>Sugestão de Correção</th>
          </tr></thead>
          <tbody>{linhas_inc}</tbody>
        </table>"""
        if inconsistencias
        else '<p style="color:#00c48c;padding:1rem 0">✅ Nenhuma inconsistência encontrada. Arquivo em conformidade.</p>'
    )

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8"/>
<title>ADEFISCO — Relatório #{audit_id}</title>
<style>
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{background:#050c18;color:#e4edf8;font-family:'Segoe UI',system-ui,sans-serif;padding:2.5rem 5%}}
  h1{{font-size:1.5rem;font-weight:900;letter-spacing:2px;color:#00c48c}}
  h2{{font-size:1rem;font-weight:700;margin:2.5rem 0 1rem;color:#e4edf8;border-bottom:1px solid #132238;padding-bottom:.5rem}}
  .meta{{color:#6b85a3;font-size:.82rem;margin:.4rem 0 2rem}}
  .cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:1rem;margin-bottom:2rem}}
  .card{{background:#0a1628;border:1px solid #132238;border-radius:12px;padding:1.2rem;text-align:center}}
  .card .num{{font-size:2rem;font-weight:900;margin-bottom:.2rem}}
  .card .lbl{{color:#6b85a3;font-size:.75rem}}
  table{{width:100%;border-collapse:collapse;font-size:.8rem;margin-bottom:2rem}}
  th{{background:#0a1628;color:#6b85a3;padding:.65rem 1rem;text-align:left;font-size:.68rem;text-transform:uppercase;letter-spacing:1px;border-bottom:1px solid #132238}}
  td{{padding:.7rem 1rem;border-bottom:1px solid rgba(255,255,255,.04);vertical-align:top}}
  code{{background:#0a1628;padding:2px 6px;border-radius:3px;font-size:.78rem;color:#5aadff}}
  footer{{margin-top:3rem;padding-top:1.5rem;border-top:1px solid #132238;color:#6b85a3;font-size:.78rem;text-align:center}}
  @media print{{body{{background:#fff;color:#111}}table{{font-size:.7rem}}}}
</style>
</head>
<body>
<h1>ADEFISCO</h1>
<div class="meta">
  Relatório de Auditoria SUS • ID: <strong>{audit_id}</strong> •
  Gerado em: {data} • Arquivo: {filename}
</div>

<div class="cards">
  <div class="card"><div class="num">{total}</div><div class="lbl">Registros analisados</div></div>
  <div class="card"><div class="num" style="color:#ff5f57">{len(erros)}</div><div class="lbl">Erros críticos</div></div>
  <div class="card"><div class="num" style="color:#febc2e">{len(avisos)}</div><div class="lbl">Avisos</div></div>
  <div class="card"><div class="num" style="color:{cor_pct}">{pct}%</div><div class="lbl">Taxa de conformidade</div></div>
</div>

{ia_bloco}

<h2>Inconsistências Encontradas</h2>
{tabela_inc}

<h2>Registros Processados</h2>
<table>
  <thead><tr>
    <th>CNES</th><th>Competência</th><th>CNS Paciente</th><th>Sexo</th>
    <th>CID</th><th>Procedimento</th><th>Qtd</th><th>Valor Unit.</th>
  </tr></thead>
  <tbody>{linhas_reg}</tbody>
</table>

<footer>ADEFISCO — Inteligência Artificial para Faturamento SUS • © 2026 • Relatório gerado automaticamente</footer>
</body>
</html>"""
