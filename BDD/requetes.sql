CREATE DATABASE lapetitemeteo;
GRANT ALL PRIVILEGES ON *.* to 'www-data'@'localhost' IDENTIFIED BY 'www-data';

ALTER TABLE sonde ADD COLUMN MAC_address text NOT NULL;

/* Récupérer le derniers relevé pour chaque sonde */
SELECT date, temperature, humidite, ID_sonde FROM releve
WHERE (ID_sonde, date) IN
    (
        SELECT ID_sonde, MAX(date)
        AS max_date FROM releve
        GROUP BY ID_sonde
    )
;

/* Récupérer les derniers relevés des dernières 48 heures par sondes*/
SELECT date, temperature, humidite 
FROM releve 
WHERE date BETWEEN DATE_SUB(NOW(), INTERVAL 48 HOUR) AND NOW() 
AND ID_sonde = {sonde[0]}
ORDER BY date DESC;

/* Récupérer la liste des relevés avec le nom de la sonde plutôt que son ID*/
SELECT r.date, r.temperature, r.humidite, s.nom AS nom_sonde FROM releve r JOIN sonde s ON r.ID_sonde = s.ID_sonde;