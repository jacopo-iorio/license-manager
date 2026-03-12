const axios = require('axios');
const fs = require('fs');
const jwt = require('jsonwebtoken');
const path = require('path');

// CONFIGURAZIONE (Da cambiare quando metterai il server online)
const SERVER_URL = "http://localhost:5000/api/verify"; 
const LIC_PATH = path.join(__dirname, 'license.lic');
const PUB_KEY_PATH = path.join(__dirname, 'public.pem');

/**
 * Verifica matematica della licenza locale (Offline)
 * Controlla se il file esiste, se la firma è valida e se non è scaduto.
 */
function checkLocal() {
    try {
        if (!fs.existsSync(LIC_PATH) || !fs.existsSync(PUB_KEY_PATH)) {
            return null;
        }

        const token = fs.readFileSync(LIC_PATH, 'utf8');
        const publicKey = fs.readFileSync(PUB_KEY_PATH, 'utf8');

        // Verifica la firma RSA e la scadenza (exp)
        return jwt.verify(token, publicKey, { algorithms: ['RS256'] });
    } catch (err) {
        // Se il token è manomesso o scaduto, restituisce null
        return null;
    }
}

/**
 * Sincronizza la licenza con il server Python (Online)
 * Se il server risponde 403 (REVOKED), il sito viene bloccato.
 */
async function syncLicense() {
    try {
        if (!fs.existsSync(LIC_PATH)) return;

        const token = fs.readFileSync(LIC_PATH, 'utf8');
        
        // Chiamata al server Python
        const response = await axios.post(SERVER_URL, { token }, { timeout: 5000 });

        if (response.data.status === "success" && response.data.token) {
            // Aggiorna il file locale con il nuovo token (rinnovo automatico)
            fs.writeFileSync(LIC_PATH, response.data.token);
            console.log("[Auth] Licenza sincronizzata con successo.");
        }
    } catch (error) {
        if (error.response && error.response.status === 403) {
            console.error("************************************************");
            console.error("!!! ACCESSO NEGATO: LICENZA REVOCATA DAL SERVER !!!");
            console.error("************************************************");
            
            // AUTO-DISTRUZIONE: Rimuove la licenza locale
            if (fs.existsSync(LIC_PATH)) fs.unlinkSync(LIC_PATH);
            
            // Arrestate il processo
            process.exit(1);
        } else {
            // Se il server è offline, il sito continua a funzionare 
            // grazie alla validità residua del token locale.
            console.log("[Auth] Server non raggiungibile. Modalità offline attiva.");
        }
    }
}

module.exports = { checkLocal, syncLicense };