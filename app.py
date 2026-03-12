from flask import Flask, render_template, request, redirect, jsonify, send_file, session
import mysql.connector
import jwt
import datetime
import io
import os
from functools import wraps

app = Flask(__name__)
app.secret_key = "una_chiave_molto_segreta_per_le_sessioni" # Cambiala!

# CONFIGURAZIONE
DASHBOARD_PASSWORD = "admin" # La tua password per entrare nel gestore
DB_CONFIG = {
    'host': 'localhost',
    'user': 'jacopo',
    'password': 'jacopo29',
    'database': 'license_manager'
}

# Caricamento Chiavi RSA
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(BASE_DIR, "private.pem"), "rb") as f:
    PRIVATE_KEY = f.read()

def get_db():
    return mysql.connector.connect(**DB_CONFIG)

# Middleware per proteggere la dashboard
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function

# --- ROTTE DI AUTENTICAZIONE ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['password'] == DASHBOARD_PASSWORD:
            session['logged_in'] = True
            return redirect('/')
        return "Password errata!"
    return '''<form method="post" style="text-align:center; margin-top:100px;">
                <h2>Accedi al Gestore</h2>
                <input type="password" name="password" placeholder="Password">
                <button type="submit">Entra</button>
              </form>'''

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect('/login')

# --- ROTTE GESTIONE LICENZE ---
@app.route('/')
@login_required
def index():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM clients ORDER BY created_at DESC")
    clients = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('index.html', clients=clients)

@app.route('/add', methods=['POST'])
@login_required
def add_client():
    email = request.form['email']
    domain = request.form['domain']
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO clients (email, domain, status) VALUES (%s, %s, 'ACTIVE')", (email, domain))
        conn.commit()
    except Exception as e:
        print(f"Errore: {e}")
    finally:
        cursor.close()
        conn.close()
    return redirect('/')

@app.route('/toggle/<int:id>')
@login_required
def toggle_status(id):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT status FROM clients WHERE id = %s", (id,))
    client = cursor.fetchone()
    if client:
        new_status = 'REVOKED' if client['status'] == 'ACTIVE' else 'ACTIVE'
        cursor.execute("UPDATE clients SET status = %s WHERE id = %s", (new_status, id))
        conn.commit()
    cursor.close()
    conn.close()
    return redirect('/')

@app.route('/download/<int:id>')
@login_required
def download_license(id):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM clients WHERE id = %s", (id,))
    client = cursor.fetchone()
    cursor.close()
    conn.close()

    if not client: return "Non trovato", 404
    
    # Generazione Token Iniziale (valido 30 giorni)
    token = jwt.encode({
        "email": client['email'],
        "domain": client['domain'],
        "exp": datetime.datetime.utcnow() + datetime.timedelta(days=30),
        "iat": datetime.datetime.utcnow()
    }, PRIVATE_KEY, algorithm="RS256")
    
    return send_file(
        io.BytesIO(token.encode()),
        mimetype='application/octet-stream',
        as_attachment=True,
        download_name=f"license_{client['domain']}.lic"
    )

# --- API PER I SITI (Senza login_required) ---
@app.route('/api/verify', methods=['POST'])
def verify():
    data = request.json
    token = data.get('token')
    try:
        decoded = jwt.decode(token, options={"verify_signature": False})
        email = decoded.get('email')
        
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT status FROM clients WHERE email = %s", (email,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if not user or user['status'] == 'REVOKED':
            return jsonify({"status": "error", "message": "Revocata"}), 403
        
        # Rinnovo automatico per altri 7 giorni
        new_token = jwt.encode({
            "email": email,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(days=7)
        }, PRIVATE_KEY, algorithm="RS256")
        
        return jsonify({"status": "success", "token": new_token})
    except:
        return jsonify({"status": "error"}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)