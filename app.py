from flask import Flask, jsonify, request, session, redirect, url_for
from functools import wraps
import hashlib
import secrets
import requests
import os

app = Flask(__name__)
app.secret_key = 'oyebi_secret_key'

# ==================================================
# CONFIGURATION GROQ API
# ==================================================
GROQ_API_KEY = os.environ.get('GROQ_API_KEY', '')
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

# ==================================================
# FONCTION POUR APPELER GROQ
# ==================================================
def generer_reponse_groq(question):
    if not GROQ_API_KEY:
        return "⚠️ Clé API Groq non configurée. Va sur Render → Environment → ajoute GROQ_API_KEY."
    
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": "Tu es OYEBI, un expert financier et économique congolais. Réponds de manière structurée : chiffre clé, analyse, causes, conséquences, action concrète."},
            {"role": "user", "content": question}
        ],
        "temperature": 0.7,
        "max_tokens": 800
    }
    
    try:
        response = requests.post(GROQ_URL, json=payload, headers=headers, timeout=30)
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            return f"❌ Erreur API Groq: {response.status_code}"
    except Exception as e:
        return f"❌ Erreur: {str(e)}"

# ==================================================
# AUTHENTIFICATION
# ==================================================
users = {}

def hash_password(p):
    return hashlib.sha256(p.encode()).hexdigest()

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    name = data.get('name')
    if email in users:
        return jsonify({"error": "Email déjà utilisé"}), 400
    if '@' not in email:
        return jsonify({"error": "Email invalide"}), 400
    if len(password) < 6:
        return jsonify({"error": "Mot de passe trop court (min 6)"}), 400
    users[email] = {"name": name, "password": hash_password(password), "email": email}
    return jsonify({"message": "Compte créé !"}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    user = users.get(email)
    if not user or user['password'] != hash_password(password):
        return jsonify({"error": "Identifiants incorrects"}), 401
    session['user'] = email
    return jsonify({"token": secrets.token_hex(32), "user": {"name": user['name'], "email": user['email']}}), 200

@app.route('/api/logout', methods=['POST'])
def logout():
    session.pop('user', None)
    return jsonify({"message": "Déconnecté"}), 200

@app.route('/api/me')
def me():
    email = session.get('user')
    if not email:
        return jsonify({"error": "Non authentifié"}), 401
    user = users.get(email)
    return jsonify({"name": user['name'], "email": user['email']}), 200

@app.route('/api/chat', methods=['POST'])
def api_chat():
    data = request.json
    question = data.get('question', '')
    reponse = generer_reponse_groq(question)
    return jsonify({"reponse": reponse})

# ==================================================
# PAGES HTML
# ==================================================
BASE_HTML = '''
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OYEBI · Agent IA Finance</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Arial, sans-serif; background: #0A0F1E; color: #F1F5F9; padding: 20px; }
        .container { max-width: 900px; margin: 0 auto; }
        .header { text-align: center; padding: 30px; background: linear-gradient(135deg, #0085CA, #FACC15); border-radius: 20px; margin-bottom: 20px; }
        h1 { color: white; font-size: 2rem; }
        .nav { text-align: center; margin-bottom: 20px; }
        .nav a { color: #FACC15; margin: 0 15px; text-decoration: none; font-weight: bold; }
        .chat-box { background: rgba(255,255,255,0.05); border-radius: 20px; padding: 20px; height: 450px; overflow-y: auto; margin-bottom: 20px; border: 1px solid rgba(255,255,255,0.1); }
        .message { margin: 10px 0; padding: 12px; border-radius: 12px; line-height: 1.5; white-space: pre-wrap; }
        .user { background: #0085CA; text-align: right; }
        .bot { background: rgba(250,204,21,0.15); border-left: 3px solid #FACC15; }
        input { width: 80%; padding: 12px; border-radius: 25px; border: none; background: rgba(255,255,255,0.1); color: white; }
        button { padding: 12px 25px; background: #FACC15; border: none; border-radius: 25px; cursor: pointer; font-weight: bold; margin-left: 10px; }
        .footer { text-align: center; margin-top: 20px; font-size: 0.8rem; color: #64748B; }
        @media (max-width: 600px) { input { width: 70%; } }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 OYEBI · Agent IA Financier</h1>
            <p>Propulsé par Groq IA (ultra-rapide)</p>
        </div>
        <div class="nav">
            <a href="/">Accueil</a>
            <a href="/chat">Chat</a>
            <a href="/login" id="authLink">Connexion</a>
        </div>
        <div id="content">[CONTENT]</div>
        <div class="footer">OYEBI · Kinshasa, RDC</div>
    </div>
    <script>
        const token = localStorage.getItem('token');
        const authLink = document.getElementById('authLink');
        if (token) {
            fetch('/api/me').then(r => {
                if (r.ok) authLink.innerHTML = '👤 Mon compte';
                else localStorage.removeItem('token');
            });
        }
    </script>
</body>
</html>
'''

def render_page(content):
    return BASE_HTML.replace('[CONTENT]', content)

@app.route('/')
def index():
    content = '''
    <div style="text-align:center; background:rgba(255,255,255,0.05); border-radius:20px; padding:40px;">
        <h2>💡 Votre expert financier surhumain</h2>
        <p>Posez vos questions sur l'économie, l'inflation, les investissements...</p>
        <a href="/chat"><button style="margin-top:20px;">💬 Démarrer une conversation</button></a>
    </div>
    '''
    return render_page(content)

@app.route('/chat')
def chat():
    content = '''
    <div class="chat-box" id="chat">
        <div class="message bot">🤖 <strong>OYEBI IA :</strong><br>Bonjour ! Je suis votre agent financier. Posez-moi des questions sur :<br>• L'économie de la RDC<br>• L'inflation<br>• Le chômage<br>• Les investissements<br><br>💡 L'IA répond en 5-10 secondes.</div>
    </div>
    <div style="display:flex;">
        <input type="text" id="question" placeholder="Ex: Comment va l'économie de la RDC ?">
        <button onclick="sendMessage()">Envoyer</button>
    </div>
    <script>
        async function sendMessage() {
            const input = document.getElementById('question');
            const question = input.value.trim();
            if (!question) return;
            
            const chat = document.getElementById('chat');
            chat.innerHTML += `<div class="message user">👤 <strong>Vous :</strong><br>${question}</div>`;
            input.value = '';
            chat.innerHTML += `<div class="message bot">🤖 <strong>OYEBI IA :</strong><br><i>Analyse en cours...</i></div>`;
            chat.scrollTop = chat.scrollHeight;
            
            try {
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({question: question})
                });
                const data = await response.json();
                const lastMsg = chat.lastElementChild;
                lastMsg.innerHTML = `🤖 <strong>OYEBI IA :</strong><br>${data.reponse.replace(/\\n/g, '<br>')}`;
                chat.scrollTop = chat.scrollHeight;
            } catch (error) {
                const lastMsg = chat.lastElementChild;
                lastMsg.innerHTML = `🤖 <strong>OYEBI IA :</strong><br>❌ Erreur de connexion. Vérifie que la clé API est configurée.`;
            }
        }
    </script>
    '''
    return render_page(content)

# ==================================================
# PAGES AUTH
# ==================================================
LOGIN_PAGE = '''
<div style="max-width:400px; margin:0 auto; background:rgba(255,255,255,0.05); border-radius:20px; padding:30px;">
    <h2 style="text-align:center;">Connexion / Inscription</h2>
    <input type="text" id="name" placeholder="Nom" style="width:100%; padding:10px; margin:10px 0; background:rgba(255,255,255,0.1); border:none; border-radius:10px; color:white;">
    <input type="email" id="email" placeholder="Email" style="width:100%; padding:10px; margin:10px 0; background:rgba(255,255,255,0.1); border:none; border-radius:10px; color:white;">
    <input type="password" id="password" placeholder="Mot de passe" style="width:100%; padding:10px; margin:10px 0; background:rgba(255,255,255,0.1); border:none; border-radius:10px; color:white;">
    <button onclick="register()" style="width:48%; background:#FACC15; padding:10px; margin:5px 1%; border:none; border-radius:10px; font-weight:bold;">S'inscrire</button>
    <button onclick="login()" style="width:48%; background:#0085CA; padding:10px; margin:5px 1%; border:none; border-radius:10px; font-weight:bold;">Se connecter</button>
    <div id="msg" style="color:#FACC15; text-align:center; margin-top:10px;"></div>
</div>
<script>
    async function register() {
        let r = await fetch('/api/register', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                name: document.getElementById('name').value,
                email: document.getElementById('email').value,
                password: document.getElementById('password').value
            })
        });
        let d = await r.json();
        document.getElementById('msg').innerHTML = d.message || d.error;
        if (r.ok) setTimeout(() => window.location.href='/login', 1500);
    }
    async function login() {
        let r = await fetch('/api/login', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                email: document.getElementById('email').value,
                password: document.getElementById('password').value
            })
        });
        let d = await r.json();
        if (r.ok) {
            localStorage.setItem('token', d.token);
            window.location.href = '/';
        } else {
            document.getElementById('msg').innerHTML = d.error;
        }
    }
</script>
'''

MON_COMPTE_PAGE = '''
<div style="text-align:center; background:rgba(255,255,255,0.05); border-radius:20px; padding:40px;">
    <div id="userInfo"></div>
    <button onclick="logout()" style="background:#EF4444; padding:10px 20px; border:none; border-radius:10px; cursor:pointer; margin-top:20px;">Déconnexion</button>
</div>
<script>
    async function loadUser() {
        let r = await fetch('/api/me');
        if (r.ok) {
            let u = await r.json();
            document.getElementById('userInfo').innerHTML = `<h2>👤 ${u.name}</h2><p>📧 ${u.email}</p>`;
        } else {
            window.location.href = '/login';
        }
    }
    async function logout() {
        await fetch('/api/logout', {method: 'POST'});
        localStorage.removeItem('token');
        window.location.href = '/';
    }
    loadUser();
</script>
'''

@app.route('/login')
def login_page():
    return render_page(LOGIN_PAGE)

@app.route('/mon-compte')
def mon_compte():
    return render_page(MON_COMPTE_PAGE)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
