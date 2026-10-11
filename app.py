"""Aplicação Flask didática: Explicador de Conceitos com IA."""

import os
import requests
from flask import Flask, render_template, request

app = Flask(__name__)

# A chave fica nos Secrets do Codespaces, nunca escrita no código.
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

def cabecalhos_supabase():
    """Monta os cabeçalhos usados pela API REST do Supabase."""
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
    }


def salvar_consulta(tema, nivel, explicacao):
    """Grava uma consulta na tabela consultas do Supabase."""
    # TEMPORÁRIO: imprimir no console do terminal para depuração.
    print("Entrou em salvar_consulta.", flush=True)
    url = f"{SUPABASE_URL.rstrip('/')}/rest/v1/consultas"
    resposta = requests.post(
        url,
        headers=cabecalhos_supabase(),
        json={"tema": tema, "nivel": nivel, "explicacao": explicacao},
        timeout=10,
    )
    # Mudar abaixo para imprimir no console do terminal:
    print(f"Resposta do Supabase: {resposta.status_code} - {resposta.text} - \nSUPABASE_URL: {SUPABASE_URL} - \nURL: {url}", flush=True)
    resposta.raise_for_status()


def buscar_historico():
    """Devolve as consultas mais recentes cadastradas no Supabase."""
    url = f"{SUPABASE_URL.rstrip('/')}/rest/v1/consultas"
    resposta = requests.get(
        url,
        headers=cabecalhos_supabase(),
        params={
            "select": "id,tema,nivel,explicacao,created_at",
            "order": "created_at.desc",
        },
        timeout=10,
    )
    # TEMPORÁRIO: imprimir no console do terminal para depuração.
    print(f"Resposta do Supabase: {resposta.status_code} - {resposta.text} - \n{SUPABASE_URL} - \n{url}", flush=True)
    resposta.raise_for_status()
    return resposta.json()


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

@app.route('/oi')
def oi():
    return '<h1>Oi, pessoal!</h1>'

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
        elif not SUPABASE_URL or not SUPABASE_KEY:
            erro = "Configure as variáveis SUPABASE_URL e SUPABASE_KEY."
        else:
            try:
                explicacao = pedir_explicacao(tema, nivel)
            except requests.RequestException:
                erro = "Não foi possível conversar com a IA agora. Tente novamente." + SUPABASE_URL
            else:
                print("Resposta da IA recebida; iniciando gravação.", flush=True)
                try:
                    salvar_consulta(tema, nivel, explicacao)
                except requests.RequestException:
                    erro = "A explicação foi gerada, mas não foi possível salvar no histórico." 

    return render_template(
        "index.html",
        explicacao=explicacao,
        erro=erro,
        tema=tema,
        nivel=nivel,
    )


@app.route("/historico")
def historico():
    consultas = []
    erro = None

    if not SUPABASE_URL or not SUPABASE_KEY:
        erro = "Configure as variáveis SUPABASE_URL e SUPABASE_KEY."
    else:
        try:
            consultas = buscar_historico()
        except requests.RequestException:
            erro = "Não foi possível carregar o histórico agora. Tente novamente."

    return render_template("historico.html", consultas=consultas, erro=erro)

