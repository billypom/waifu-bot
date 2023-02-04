DROP TABLE IF EXISTS waifu;
DROP TABLE IF EXISTS user;

CREATE TABLE user (
    id bigint unsigned,
    CONSTRAINT userPK PRIMARY KEY (id)
);

CREATE TABLE waifu (
    id int unsigned auto_increment,
    name varchar(128),
    series varchar(256),
    user_id bigint unsigned,
    claim_time_limit bigint unsigned,
    CONSTRAINT waifuPK PRIMARY KEY (id),
    CONSTRAINT waifuFK FOREIGN KEY (user_id) REFERENCES user(id)
);

CREATE TABLE config (
    id int unsigned auto_increment,
    server_id bigint unsigned,
)