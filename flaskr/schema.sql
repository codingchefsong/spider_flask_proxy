DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS proxy;
DROP TABLE IF EXISTS post;
DROP TABLE IF EXISTS upload;
DROP TABLE IF EXISTS deleted;

CREATE TABLE user (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT    UNIQUE
                     NOT NULL,
    password TEXT    NOT NULL
);

CREATE TABLE proxy (
    id        INTEGER   PRIMARY KEY AUTOINCREMENT,
    author_id INTEGER   NOT NULL,
    created   TIMESTAMP,
    updated   TIMESTAMP,
    delay     TEXT,
    ip        TEXT      NOT NULL
                        UNIQUE,
    port      TEXT      NOT NULL,
    FOREIGN KEY (author_id) REFERENCES user (id)
    );

CREATE TABLE post (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  author_id INTEGER NOT NULL,
  created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  title TEXT NOT NULL,
  body TEXT NOT NULL,
  FOREIGN KEY (author_id) REFERENCES user (id)
  );

CREATE TABLE upload (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  author_id INTEGER NOT NULL,
  created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  title TEXT NOT NULL,
  body TEXT NOT NULL,
  file_url TEXT NOT NULL,
  FOREIGN KEY (author_id) REFERENCES user (id)
  );

  CREATE TABLE deleted (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  author_id INTEGER NOT NULL,
  created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  title TEXT NOT NULL,
  body TEXT NOT NULL,
  file_url TEXT NOT NULL,
  FOREIGN KEY (author_id) REFERENCES user (id)
  );


