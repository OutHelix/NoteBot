CREATE SCHEMA service
CREATE TABLE service.users
(
    id serial PRIMARY KEY NOT NULL,
    full_name varchar NOT NULL,
    login varchar NOT NULL,
    password varchar NOT NULL,
    telegram varchar NOT NULL,
    discord varchar NOT NULL,
    vk varchar NOT NULL
);

CREATE TABLE service.notes
(
    id_user int,
    FOREIGN KEY (id_user) REFERENCES service.users (id),
    note_id int NOT NULL,
    note_time varchar NOT NULL
);