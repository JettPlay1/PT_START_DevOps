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

CREATE USER ${DB_REPL_USER} WITH REPLICATION ENCRYPTED PASSWORD ${DB_REPL_PASSWORD};
SELECT pg_create_physical_replication_slot('replication_slot');

CREATE USER tg_bot_user WITH PASSWORD 'qwerty123';
GRANT SELECT, INSERT ON emails, phone_numbers TO tg_bot_user;
GRANT ALL ON SEQUENCE phone_numbers_id_seq, emails_id_seq TO tg_bot_user;