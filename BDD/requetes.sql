CREATE DATABASE lapetitemeteo;
GRANT ALL PRIVILEGES ON *.* to 'www-data'@'localhost' IDENTIFIED BY 'www-data';

ALTER TABLE sonde ADD MAC_address text NOT NULL;

