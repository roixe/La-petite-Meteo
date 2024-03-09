-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Hôte : 127.0.0.1:3306
-- Généré le : jeu. 15 fév. 2024 à 12:34
-- Version du serveur : 8.2.0
-- Version de PHP : 8.2.13

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Base de données : `la-petite-meteo_2`
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
  KEY `ID_sonde` (`ID_sonde`),
  CONSTRAINT `fk_releve_sonde` FOREIGN KEY (`ID_sonde`) REFERENCES `sonde` (`ID_sonde`)
) ENGINE=MyISAM AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Déchargement des données de la table `releve`
--

INSERT INTO `releve` (`ID_releve`, `Temperature`, `Humidite`, `date`, `ID_sonde`) VALUES
(1, 23, 88, '2024-01-15 13:19:30', 0);

-- --------------------------------------------------------

--
-- Structure de la table `sonde`
--

DROP TABLE IF EXISTS `sonde`;
CREATE TABLE IF NOT EXISTS `sonde` (
  `ID_sonde` int NOT NULL AUTO_INCREMENT,
  `Nom` text NOT NULL,
  `Zone` text NOT NULL,
  PRIMARY KEY (`ID_sonde`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;