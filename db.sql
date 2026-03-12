-- 1. Crea il database se non esiste
CREATE DATABASE IF NOT EXISTS license_manager;

-- 2. Seleziona il database per le operazioni successive
USE license_manager;

-- 3. Crea la tabella per i clienti e le licenze
CREATE TABLE IF NOT EXISTS clients (
    id INT AUTO_INCREMENT PRIMARY KEY,          -- ID univoco
    email VARCHAR(255) NOT NULL UNIQUE,         -- Email del cliente (univoca)
    domain VARCHAR(255) NOT NULL,                -- Dominio del sito (es. sito.com)
    status ENUM('ACTIVE', 'REVOKED') DEFAULT 'ACTIVE', -- Lo "switch" per lo stop
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP -- Data di registrazione
);