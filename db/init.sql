CREATE TABLE IF NOT EXISTS emails(
    ID SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL
);
CREATE TABLE IF NOT EXISTS phone_numbers(
    ID SERIAL PRIMARY KEY,
    phone_number VARCHAR(20) NOT NULL
);

INSERT INTO emails (email) VALUES ('test@test.com'), ('test2@test2.ru');
INSERT INTO phone_numbers (phone_number) VALUES ('88005553535'), ('+7 987 654 32 10');

CREATE USER repl_user WITH REPLICATION ENCRYPTED PASSWORD 'qwerty123';
SELECT pg_create_physical_replication_slot('replication_slot');