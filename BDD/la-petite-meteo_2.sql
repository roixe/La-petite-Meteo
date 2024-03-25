--
-- Base de données : `la-petite-meteo`
--

-- --------------------------------------------------------

--
-- Structure de la table `releve`
--

DROP TABLE IF EXISTS `releve`;
CREATE TABLE IF NOT EXISTS `releve` (
  `ID_releve` int NOT NULL AUTO_INCREMENT,
  `Temperature` int NOT NULL,
  `Humidite` int NOT NULL,
  `date` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `ID_sonde` int NOT NULL,
  PRIMARY KEY (`ID_releve`),
  KEY `ID_sonde` (`ID_sonde`)
) ENGINE=MyISAM AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


-- --------------------------------------------------------

--
-- Structure de la table `sonde`
--

DROP TABLE IF EXISTS `sonde`;
CREATE TABLE IF NOT EXISTS `sonde` (
  `ID_sonde` int NOT NULL AUTO_INCREMENT,
  `Nom` text NOT NULL,
  `Zone` text NOT NULL,
  `MAC_address` text  NOT NULL,
  PRIMARY KEY (`ID_sonde`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
