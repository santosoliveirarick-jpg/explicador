from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def index():
    usuario = 'Sérgio'
    tecnologia = 'Flask (Python)'
    return render_template('index.html', nome=usuario, tec = tecnologia)
