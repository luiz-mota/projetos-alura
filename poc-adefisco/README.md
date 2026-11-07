# ADEFISCO — Auditoria de faturamento SUS com IA (POC)

Prova de conceito de uma ferramenta que audita arquivos de faturamento
ambulatorial do SUS (BPA) **antes do envio**, apontando registros que seriam
glosados e gerando um resumo executivo com IA.

## Problema
Erros de preenchimento no BPA (cartão SUS inválido, CID fora do padrão,
quantidade acima do permitido, procedimento incompatível com idade ou sexo)
geram glosa e perda de receita. A conferência costuma ser manual e tardia.

## O que a POC faz
1. Recebe um CSV de BPA pela interface web
2. Valida cada linha contra regras de faturamento
3. Gera um relatório HTML com as inconsistências por linha (erro ou aviso)
4. Opcionalmente, pede ao Claude um resumo executivo com prioridades de correção

### Regras implementadas
| Regra | Tipo |
|-------|------|
| CNS (Cartão Nacional de Saúde) com 15 dígitos e prefixo válido | erro |
| CID-10 no formato padrão | erro |
| Código de procedimento SIGTAP com 10 dígitos | erro |
| Quantidade acima do limite mensal do procedimento | erro |
| Procedimento fora da faixa etária permitida | erro |
| CID incompatível com o sexo do paciente | erro |
| Registro duplicado no arquivo | aviso |
| Competência fora do formato AAAAMM | erro |

## Estrutura
```
adefisco-mvp/
├── app/
│   ├── main.py       API FastAPI (upload, auditoria, relatório)
│   ├── parser.py     leitura do CSV de BPA
│   ├── rules.py      regras de validação
│   ├── report.py     relatório HTML
│   └── ai_audit.py   resumo executivo via API do Claude
├── static/index.html interface de upload
├── sample_data/      BPA de exemplo com dados fictícios
└── run.py
landing/index.html    página de apresentação do produto
```

## Como rodar
```bash
cd adefisco-mvp
pip install -r requirements.txt
cp .env.example .env          # opcional: ANTHROPIC_API_KEY para o resumo com IA
python run.py                 # http://localhost:8000
```
Use `sample_data/bpa_amostra.csv` para testar. Sem chave de API, a auditoria
por regras funciona normalmente e só o resumo com IA fica desativado.

## Stack
Python · FastAPI · Uvicorn · API do Claude (Anthropic) · HTML/JS

## Status
POC funcional. Próximos passos: persistência das auditorias, regras carregadas
da tabela SIGTAP oficial e testes automatizados.
