import os
from dotenv import load_dotenv

load_dotenv()


async def gerar_analise_ia(inconsistencias: list, total_registros: int) -> str | None:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return None

    try:
        import anthropic

        client = anthropic.AsyncAnthropic(api_key=api_key)

        linhas = "\n".join(
            f"- Linha {inc.linha} | {inc.campo} | {inc.tipo.upper()}: {inc.descricao}"
            for inc in inconsistencias[:25]
        )

        msg = await client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=900,
            system=(
                "Você é especialista em faturamento SUS, auditoria de produção ambulatorial/hospitalar "
                "e conformidade com as Portarias GM/MS nº 6.904/2025 e nº 10.297/2026. "
                "Analise as inconsistências de um arquivo BPA e responda SEMPRE em três blocos:\n"
                "1. DIAGNÓSTICO GERAL (2 frases)\n"
                "2. PRINCIPAIS RISCOS DE GLOSA (liste os 3 mais críticos)\n"
                "3. PRÓXIMOS PASSOS (ações prioritárias para o município)\n"
                "Seja direto, técnico e prático. Responda em português."
            ),
            messages=[{
                "role": "user",
                "content": (
                    f"Arquivo analisado: {total_registros} registros de produção SUS.\n"
                    f"Total de inconsistências: {len(inconsistencias)}\n\n"
                    f"Detalhamento:\n{linhas}\n\n"
                    "Forneça a análise especializada."
                ),
            }],
        )

        return msg.content[0].text

    except Exception as exc:
        return f"Análise de IA indisponível: {exc}"
