const { checkLocal, syncLicense } = require('./licenseManager');

// 1. Blocco immediato se la licenza locale non è valida
const auth = checkLocal();
if (!auth) {
    console.error("Licenza non trovata o corrotta. Il server non può avviarsi.");
    process.exit(1);
}

// 2. Controllo remoto periodico (ogni 12 ore)
setInterval(syncLicense, 1000 * 60 * 60 * 12);

// 3. Primo controllo remoto all'avvio (senza bloccare l'avvio se il server è offline)
syncLicense();

console.log(`Sito avviato per: ${auth.email}`);
// ... resto del tuo codice express o node ...