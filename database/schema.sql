CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario TEXT NOT NULL UNIQUE,
    senha_hash TEXT NOT NULL,
    salt TEXT NOT NULL,
    papel TEXT NOT NULL DEFAULT 'ADMIN'
);

CREATE TABLE IF NOT EXISTS eleitores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    cpf TEXT NOT NULL UNIQUE,
    titulo TEXT NOT NULL UNIQUE,
    ja_votou INTEGER NOT NULL DEFAULT 0,
    foto TEXT,
    biometria INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS candidatos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    numero INTEGER NOT NULL,
    partido TEXT NOT NULL,
    cargo TEXT NOT NULL,
    votos INTEGER NOT NULL DEFAULT 0,
    foto TEXT,
    UNIQUE (numero, cargo)
);

CREATE TABLE IF NOT EXISTS eleicoes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'ABERTA'
);

CREATE TABLE IF NOT EXISTS eleicao_cargos (
    eleicao_id INTEGER NOT NULL,
    cargo TEXT NOT NULL,
    PRIMARY KEY (eleicao_id, cargo),
    FOREIGN KEY (eleicao_id) REFERENCES eleicoes(id)
);

CREATE TABLE IF NOT EXISTS eleicao_candidatos (
    eleicao_id INTEGER NOT NULL,
    candidato_id INTEGER NOT NULL,
    PRIMARY KEY (eleicao_id, candidato_id),
    FOREIGN KEY (eleicao_id) REFERENCES eleicoes(id),
    FOREIGN KEY (candidato_id) REFERENCES candidatos(id)
);

CREATE TABLE IF NOT EXISTS votos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    eleicao_id INTEGER NOT NULL,
    cargo TEXT NOT NULL,
    eleitor_id INTEGER NOT NULL,
    candidato_id INTEGER,
    tipo TEXT NOT NULL DEFAULT 'VALIDO',
    data_hora TEXT NOT NULL,
    FOREIGN KEY (eleicao_id) REFERENCES eleicoes(id),
    FOREIGN KEY (eleitor_id) REFERENCES eleitores(id),
    FOREIGN KEY (candidato_id) REFERENCES candidatos(id),
    UNIQUE (eleicao_id, cargo, eleitor_id)
);

CREATE TABLE IF NOT EXISTS auditoria (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    data_hora TEXT NOT NULL,
    usuario TEXT NOT NULL,
    acao TEXT NOT NULL,
    detalhes TEXT
);