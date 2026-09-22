"""Aplicação Flask didática: Explicador de Conceitos com IA."""

import os
import requests
from flask import Flask, render_template, request

app = Flask(__name__)

# A chave fica nos Secrets do Codespaces, nunca escrita no código.
# GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_KEY = "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"

def pedir_explicacao(tema, nivel):
    """Envia o tema e o nível para a API e devolve o texto da IA."""
    prompt = f"""
Explique o tema \"{tema}\" para uma pessoa no nível \"{nivel}\".
Use português do Brasil, linguagem adequada ao nível e uma explicação curta.
Ao final, dê exatamente um exemplo prático.
"""

    resposta = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": "openai/gpt-oss-120b",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.4,
        },
        timeout=30,
    )

    # Se a API responder com erro, esta linha interrompe a execução.
    resposta.raise_for_status()
    dados = resposta.json()

    # Este é o caminho definido pelo formato de resposta da API.
    return dados["choices"][0]["message"]["content"]


@app.route("/", methods=["GET", "POST"])
def index():
    explicacao = None
    erro = None
    tema = ""
    nivel = "adolescente"

    # A página abre com GET. O formulário envia os dados com POST.
    if request.method == "POST":
        tema = request.form.get("tema", "").strip()
        nivel = request.form.get("nivel", "adolescente")

        if not tema:
            erro = "Digite um tema para receber a explicação."
        elif nivel not in ("criança", "adolescente", "adulto"):
            erro = "Escolha um nível válido."
        elif not GROQ_API_KEY:
            erro = "A chave GROQ_API_KEY não foi configurada no Codespaces."
        else:
            try:
                explicacao = pedir_explicacao(tema, nivel)
            except requests.RequestException:
                erro = "Não foi possível conversar com a IA agora. Tente novamente."

    return render_template(
        "index.html",
        explicacao=explicacao,
        erro=erro,
        tema=tema,
        nivel=nivel,
    )


if __name__ == "__main__":
    # host=0.0.0.0 permite que o Codespaces encaminhe a porta 5000.
    app.run(host="0.0.0.0", port=5000, debug=True)
