from flask import Flask

app = Flask(__name__)

@app.route('/')
def index():
    return "<h1>OYEBI - Déploiement réussi !</h1><p>L'application tourne sur Render 🎉</p>"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
