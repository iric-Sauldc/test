CREATE TABLE IF NOT EXISTS usuario (
    id INTEGER NOT NULL AUTO_INCREMENT,
    usuario VARCHAR(20) NOT NULL,
    nombre VARCHAR(50) NOT NULL,
    apellido VARCHAR(50) NOT NULL,
    correo VARCHAR(100) NOT NULL,
    `contraseña` VARCHAR(200) NOT NULL,
    puntuacion INTEGER DEFAULT 0,
    PRIMARY KEY (id),
    UNIQUE (usuario),
    UNIQUE (correo)
);

CREATE TABLE IF NOT EXISTS categoria (
    id INTEGER NOT NULL AUTO_INCREMENT,
    nombre VARCHAR(100) NOT NULL,
    descripcion TEXT,
    PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS subcategoria (
    id INTEGER NOT NULL AUTO_INCREMENT,
    nombre VARCHAR(100) NOT NULL,
    descripcion TEXT,
    categoria_id INTEGER NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY (categoria_id) REFERENCES categoria (id)
);

CREATE TABLE IF NOT EXISTS desafio (
    id INTEGER NOT NULL AUTO_INCREMENT,
    nombre VARCHAR(100) NOT NULL,
    descripcion VARCHAR(200) NOT NULL,
    puntuacion INTEGER NOT NULL,
    dificultad VARCHAR(50) NOT NULL,
    archivo LONGBLOB,
    flag VARCHAR(255) NOT NULL,
    subcategoria_id INTEGER NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY (subcategoria_id) REFERENCES subcategoria (id)
);

CREATE TABLE IF NOT EXISTS desafio_completado (
    id INTEGER NOT NULL AUTO_INCREMENT,
    usuario_id INTEGER NOT NULL,
    desafio_id INTEGER NOT NULL,
    puntuacion INTEGER NOT NULL,
    flag_ingresada VARCHAR(200) NOT NULL,
    fecha_completado TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    tiempo_record FLOAT,
    es_correcta BOOLEAN DEFAULT FALSE,
    PRIMARY KEY (id),
    FOREIGN KEY (usuario_id) REFERENCES usuario (id),
    FOREIGN KEY (desafio_id) REFERENCES desafio (id)
);

CREATE TABLE IF NOT EXISTS desafio_en_progreso (
    id INTEGER NOT NULL AUTO_INCREMENT,
    user_id INTEGER NOT NULL,
    desafio_id INTEGER NOT NULL,
    tiempo_inicio DATETIME NOT NULL,
    tiempo_limite INTEGER DEFAULT 0,
    estado VARCHAR(20) DEFAULT 'en_progreso',
    reintentos INTEGER DEFAULT 0,
    PRIMARY KEY (id),
    FOREIGN KEY (user_id) REFERENCES usuario (id),
    FOREIGN KEY (desafio_id) REFERENCES desafio (id)
);

CREATE TABLE IF NOT EXISTS progreso_desafio (
    id INTEGER NOT NULL AUTO_INCREMENT,
    user_id INTEGER NOT NULL,
    desafio_id INTEGER NOT NULL,
    progreso JSON,
    actualizado_en DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    FOREIGN KEY (user_id) REFERENCES usuario (id),
    FOREIGN KEY (desafio_id) REFERENCES desafio (id)
);
