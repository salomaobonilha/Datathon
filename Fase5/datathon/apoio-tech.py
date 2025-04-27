# To run this code you need to install the following dependencies:
# pip install google-genai

import base64
from google import genai
import os
from google.genai import types


def generate():
    client = genai.Client(
        api_key=os.environ["GEMINI_API_KEY"]
    )

    model = "gemini-2.0-flash-lite"
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text="""Vaga para desenvolvimento de software Python Pleno"""),
            ],
        ),
    ]
    generate_content_config = types.GenerateContentConfig(
        response_mime_type="text/plain",
        system_instruction=[
            types.Part.from_text(text="""Você é especialista em criar perguntas e resposta de prova técnica de tecnologia, baseado na vaga informada e a senioridade da vaga gere 10 as perguntas e respostas, considere o nivel das perguntas baseado na senioridade da vaga, se a vaga for junior é importante ter perguntas devem ser de nivel básico e pouco intermediario, se a vaga for pleno as perguntas devem ser de nivel básico e intermediário e se a vaga for senior as perguntas devem ser de nivel básico (em quantidade menor), intermediario e avançado. As perguntas devem ser sobre o assunto relacionado a vaga, por exemplo: se a vaga for para desenvolvedor java, as perguntas devem ser sobre java, spring, hibernate, etc. Se a vaga for para desenvolvedor python, as perguntas devem ser sobre python, django, flask, etc. As perguntas devem ser abertas e as respostas devem ser curtas e objetivas. 

Qualquer outra pergunta diferente disso não deve ser respondida, gere a saida em json com perguntas e respostas e o nivel de conhecimento   (básico, intermediário e avançado) tudo em portugues, mas nomes técnicos devem ser mantidos"""),
        ],
    )

    for chunk in client.models.generate_content_stream(
        model=model,
        contents=contents,
        config=generate_content_config,
    ):
        print(chunk.text, end="")

if __name__ == "__main__":
    generate()
