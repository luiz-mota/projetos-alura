import io
import uuid
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .ai_audit import gerar_analise_ia
from .parser import parse_bpa_csv
from .report import gerar_relatorio_html
from .rules import auditar_registros

BASE = Path(__file__).parent.parent

app = FastAPI(title="ADEFISCO — Auditoria SUS")
app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")
app.mount("/sample_data", StaticFiles(directory=BASE / "sample_data"), name="sample_data")

_store: dict[str, str] = {}


@app.get("/", response_class=HTMLResponse)
async def index():
    return (BASE / "static" / "index.html").read_text(encoding="utf-8")


@app.post("/api/auditar")
async def auditar(arquivo: UploadFile = File(...)):
    if not arquivo.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Envie um arquivo .csv")

    conteudo = await arquivo.read()
    try:
        texto = conteudo.decode("utf-8-sig")
        registros = parse_bpa_csv(io.StringIO(texto))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Erro ao processar arquivo: {exc}")

    if not registros:
        raise HTTPException(status_code=400, detail="Nenhum registro encontrado no arquivo.")

    _, inconsistencias = auditar_registros(registros)

    analise_ia = None
    if inconsistencias:
        analise_ia = await gerar_analise_ia(inconsistencias, len(registros))

    aid = str(uuid.uuid4())[:8].upper()
    html = gerar_relatorio_html(registros, inconsistencias, analise_ia, aid, arquivo.filename)
    _store[aid] = html

    return JSONResponse({
        "id": aid,
        "total_registros": len(registros),
        "total_inconsistencias": len(inconsistencias),
        "erros": sum(1 for i in inconsistencias if i.tipo == "erro"),
        "avisos": sum(1 for i in inconsistencias if i.tipo == "aviso"),
        "inconsistencias": [vars(i) for i in inconsistencias],
        "analise_ia": analise_ia,
    })


@app.get("/api/relatorio/{aid}", response_class=HTMLResponse)
async def relatorio(aid: str):
    chave = aid.upper()
    if chave not in _store:
        raise HTTPException(status_code=404, detail="Relatório não encontrado.")
    return _store[chave]
