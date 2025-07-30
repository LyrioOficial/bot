# ai_service.py
import os
import aiohttp
import json

# Pega a chave de API das suas variáveis de ambiente
API_KEY = os.getenv('GEMINI_API_KEY')
API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"

async def generate_embed_content(user_prompt: str) -> dict or None:
    """
    Envia um prompt para a API do Gemini e formata a resposta para um embed.
    Retorna um dicionário {'title': ..., 'description': ...} ou None em caso de erro.
    """
    if not API_KEY:
        print("ERRO: A chave de API do Gemini (GEMINI_API_KEY) não foi encontrada nas variáveis de ambiente.")
        return None

    headers = {
        'Content-Type': 'application/json',
        'x-goog-api-key': API_KEY
    }
    
    # Instruímos a IA a nos dar um título e uma descrição de forma estruturada
    structured_prompt = (
        f"Com base no tópico a seguir, gere um conteúdo para um embed do Discord. "
        f"Sua resposta DEVE ser em português e seguir EXATAMENTE este formato, sem nenhuma palavra extra:\n"
        f"TÍTULO: [título conciso e atrativo aqui]\n"
        f"DESCRIÇÃO: [descrição bem elaborada aqui, usando parágrafos e markdown do Discord se necessário]\n\n"
        f"Tópico: \"{user_prompt}\""
    )

    data = {
        "contents": [{
            "parts": [{"text": structured_prompt}]
        }]
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(API_URL, headers=headers, json=data) as response:
                if response.status == 200:
                    response_json = await response.json()
                    
                    if not response_json.get('candidates'):
                        print(f"Erro na API do Gemini: Resposta sem 'candidates'. Provavelmente bloqueado por segurança. Resposta: {response_json}")
                        return {"title": "Erro de Conteúdo", "description": "A IA não pôde gerar o conteúdo, possivelmente por restrições de segurança do modelo."}

                    text_content = response_json['candidates'][0]['content']['parts'][0]['text']
                    
                    title = "Título Gerado pela IA"
                    description = text_content
                    
                    lines = text_content.strip().split('\n')
                    for line in lines:
                        if line.upper().startswith("TÍTULO:"):
                            title = line[len("TÍTULO:"):].strip()
                        elif line.upper().startswith("DESCRIÇÃO:"):
                            description = text_content[text_content.upper().find("DESCRIÇÃO:") + len("DESCRIÇÃO:"):].strip()
                            break
                            
                    return {"title": title, "description": description}
                else:
                    error_text = await response.text()
                    print(f"Erro na API do Gemini: {response.status} - {error_text}")
                    return {"title": "Erro de API", "description": f"A API retornou um erro {response.status}. Verifique o console para mais detalhes."}
    except Exception as e:
        print(f"Ocorreu um erro na requisição para a IA: {e}")
        return None