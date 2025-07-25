# ai_service.py
import os
import aiohttp
import json

# Pega a chave de API das "Secrets" do Replit de forma segura
API_KEY = os.getenv('GEMINI_API_KEY')
API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"

async def generate_embed_content(user_prompt: str) -> dict or None:
    """
    Envia um prompt para a API do Gemini e formata a resposta para um embed.
    Retorna um dicionário {'title': ..., 'description': ...} ou None em caso de erro.
    """
    if not API_KEY:
        print("ERRO: A chave de API do Gemini não foi encontrada nas Secrets.")
        return None

    headers = {
        'Content-Type': 'application/json',
        'x-goog-api-key': API_KEY
    }

    # Instruímos a IA a nos dar um título e uma descrição, o que facilita o nosso trabalho.
    structured_prompt = (
        f"Com base no tópico a seguir, gere um conteúdo para um embed do Discord. "
        f"Sua resposta DEVE ser em português e seguir EXATAMENTE este formato, sem nenhuma palavra extra:\n"
        f"TÍTULO: [título gerado aqui]\n"
        f"DESCRIÇÃO: [descrição gerada aqui com parágrafos]\n\n"
        f"Tópico: \"{user_prompt}\""
    )

    data = {
        "contents": [{
            "parts": [{
                "text": structured_prompt
            }]
        }]
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(API_URL, headers=headers, json=data) as response:
                if response.status == 200:
                    response_json = await response.json()
                    # Extrai o texto da resposta da IA
                    text_content = response_json['candidates'][0]['content']['parts'][0]['text']

                    # Processa o texto para separar Título e Descrição
                    title = "Título Gerado pela IA"
                    description = text_content # Fallback

                    lines = text_content.strip().split('\n')
                    for line in lines:
                        if line.upper().startswith("TÍTULO:"):
                            title = line[len("TÍTULO:"):].strip()
                        elif line.upper().startswith("DESCRIÇÃO:"):
                            # Junta o resto como descrição
                            description = text_content[text_content.upper().find("DESCRIÇÃO:") + len("DESCRIÇÃO:"):].strip()
                            break # Para de procurar após achar a descrição

                    return {"title": title, "description": description}
                else:
                    print(f"Erro na API do Gemini: {response.status} - {await response.text()}")
                    return None
    except Exception as e:
        print(f"Ocorreu um erro na requisição para a IA: {e}")
        return None