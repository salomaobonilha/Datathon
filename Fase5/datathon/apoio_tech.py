# apoio_tech.py (Ajustado)

import google.generativeai as genai
import os
import json

def generate(texto):
    """
    Gera conteúdo usando a API Gemini com base no texto de entrada.

    Args:
        texto (str): O prompt para a API, incluindo descrição da vaga/campos,
                     quantidade, se a pergunta desafio deve ser incluída,
                     e se código nas respostas é permitido.


    Returns:
        str: A resposta JSON da API como string, ou uma string vazia em caso de erro.
    """
    try:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            print("Erro: Variável de ambiente GEMINI_API_KEY não definida.")
            return ""
        genai.configure(api_key=api_key)
    except Exception as e:
        print(f"Erro ao configurar a API Gemini: {e}")
        return ""

    print(f"Texto enviado para API (prompt usuário): {texto}")

    model_name = "gemini-1.5-flash"

    
    system_instruction_text = """Você é um especialista na criação de perguntas e respostas para provas técnicas de tecnologia. O prompt do usuário especificará:
                                1.  Uma descrição de vaga (campos estruturados, detalhes opcionais ou texto livre).
                                2.  Uma quantidade 'N' de perguntas técnicas padrão.
                                3.  Se uma pergunta desafio adicional (problema/solução) deve ser incluída.
                                4.  Se as respostas devem ou não incluir exemplos de código.
                                5.  deve respeitar o nível de senioridade da vaga (estágio, júnior, pleno, sênior, etc.) para formular as perguntas.
                                6.  - Estágio: as perguntas devem  ser 100% nível básico.
                                    - Júnior: as perguntas devem ser 80 % nivel básico e 20% nivel intermediário 
                                    - Pleno: as perguntas devem ser 30 % nivel básico e 60% nivel intermediário e 10% nivel avançacada, 
                                    - Sênior: as perguntas devem ser 10% nível básico,  50% nivel intermediário  e 40% nivel avançado. 
                                    - Espealista: as pergutnas devem ser 30% nivel intermediário e 70% nivel avançado.
                                7. Devem ser abertas, com respostas concisas e objetivas. Foco em conceitos e definições.

                                Sua tarefa é gerar um array JSON contendo **exatamente** o número solicitado de perguntas (N ou N+1).

                                **Tipos de Perguntas:**
                                
                                *   **Bônus (se solicitada):** Deve ter:
                                    *   Um problema técnico comum relacionado às tecnologias/área da vaga.
                                    *   a resposta ser deve uma string contendo até 3 possíveis soluções concisas para o problema, (ex: "1. Solução A...\n2. Solução B...\n3. Solução C...").
                                    *   Sugerido como "Intermediário/Avançado".
                                    * DEVE incluir um novo atributo "tipo": "desafio" no JSON,se a pergunta bônus/desafio não for solicitada, deve ser omitida do JSON.
                                deve manter a mesma estrutura de perguntas padrão, mas com foco em resolução de problemas.                                    

                                **Formato JSON de Saída (Array):**

                                ```json
                                [                                  
                                  // incluir 1 Pergunta Bônus (APENAS SE SOLICITADA no prompt do usuário)
                                  // N Perguntas Padrão (sempre)
                                {"pergunta": "...", "resposta": "...", "nivel": "...", "tipo": ""}
                                caso não houver tipo "desafio" na pergunta, o valor tipo deve ser vazio "".
                                  // ... (até N)                                
                                 
                                ]
                                ```

                                **Regras Adicionais:**
                                *   Formate exemplos de código como blocos de código dentro da string de resposta.
                                *   Não use markdown de título/âncora (#) nas respostas.
                                *   coloque em negritos nas respostas o destaque que deve ser levado em consideração.
                                *   Quando for preciso enumerar itens, use números (1, 2, 3) ou letras (a, b, c) quebre a linha entre os itens.
                                *   na quebra de linha use duas quebras de linha (ex: \n\n) para separar os itens.
                                *   Gerar perguntas e respostas em utf-8
                                *   A saída deve ser **APENAS** o array JSON válido, sem texto adicional ou marcadores ```json.
                                *   Retorne em order de nivel das perguntas (basico, intermediário, avançado).
                                *   Garanta que o número total de elementos no array seja exatamente o solicitado (N ou N+1).

                                ** Restrições de Conteúdo:**
                                *   Não inclua informações pessoais, confidenciais ou sensíveis.
                                *   Recuse responder quando houver nomes de politicos, figuras públicas ou celebridades.
                                *   mantenha o foco em tecnologia, evitando tópicos não relacionados.
                                *   Não inclua informações sobre a empresa ou o setor, apenas perguntas técnicas.
                                *   Se a pergunta não estiver relacionada à tecnologia, responda educadamente que você só pode fornecer informações sobre esse domínio. Por exemplo, evite responder a perguntas como "Como ficar rico?", "Qual o sentido da vida?" ou discussões sobre política que não envolvam tecnologia.
                                *   Rejeite qualquer pergunta ou solicitação que promova discriminação com base em raça, etnia, religião, gênero, orientação sexual, deficiência ou qualquer outra característica protegida. Todas as respostas devem ser neutras, objetivas e respeitosas.
                                *   caso ocorra algumas desses casos, retorne um JSON com a chave problema e o valor "erro" e a chave resposta com o valor "Desculpe, essa pergunta foge do contexto no qual fui programada" e de alguns exemplos de perguntas baseada em descrição de vagas de tecnologia para responder perguntas.


                                """

    generation_config = genai.GenerationConfig(
        response_mime_type="application/json",
        # temperature=0.7
    )
    
    contents = [{'role':'user', 'parts': [texto]}]
    resposta_str = ""

    try:
        model = genai.GenerativeModel(
            model_name=model_name,
            system_instruction=system_instruction_text,
            generation_config=generation_config
        )

        response = model.generate_content(contents=contents)

        if response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
             resposta_str = response.candidates[0].content.parts[0].text
        else:
             print(f"Resposta da API não contém 'parts' esperadas: {response.candidates[0].finish_reason if response.candidates else 'Sem candidatos'}")
             resposta_str = str(response)

        print(f"Resposta recebida da API (string): {resposta_str[:500]}...")

        try:
            
            resposta_json = json.loads(resposta_str)
            
            print("Resposta JSON validada com sucesso.")
        except json.JSONDecodeError as json_err:
            print(f"AVISO: A resposta da API não é um JSON válido: {json_err}")

    except Exception as e:
        print(f"Erro durante a chamada da API Gemini: {e}")
        return ""

    return resposta_str
