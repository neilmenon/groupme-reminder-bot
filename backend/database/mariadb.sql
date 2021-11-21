-- MariaDB dump 10.19  Distrib 10.6.4-MariaDB, for osx10.16 (x86_64)
--
-- Host: localhost    Database: groupme_reminder_bot
-- ------------------------------------------------------
-- Server version	10.6.4-MariaDB

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `bot_setting`
--

DROP TABLE IF EXISTS `bot_setting`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `bot_setting` (
  `id` int(11) NOT NULL COMMENT 'The unique ID of the bot setting.',
  `settings_json` varchar(191) NOT NULL COMMENT 'A JSON object formatted as a string of the settings of the bot.',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `creates`
--

DROP TABLE IF EXISTS `creates`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `creates` (
  `reminder_id` int(11) NOT NULL COMMENT 'The ID of the reminder.',
  `user_id` int(11) NOT NULL COMMENT 'The ID of the user who created the reminder.',
  PRIMARY KEY (`reminder_id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `creates_1` FOREIGN KEY (`reminder_id`) REFERENCES `reminder` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `creates_2` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `groups`
--

DROP TABLE IF EXISTS `groups`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `groups` (
  `id` int(11) NOT NULL COMMENT 'The unique GroupMe ID from the GroupMe API.',
  `name` varchar(191) NOT NULL COMMENT 'The name of the GroupMe group.',
  `added_bot_date` datetime NOT NULL COMMENT 'A datetime object of when the GroupMe group invited the bot into their group.',
  `size` int(11) NOT NULL COMMENT 'The number of members in the GroupMe group.',
  `bot_id` varchar(100) NOT NULL COMMENT 'The bot ID from the GroupMe API.',
  PRIMARY KEY (`id`),
  UNIQUE KEY `bot_id` (`bot_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_unicode_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'STRICT_TRANS_TABLES,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`neil`@`localhost`*/ /*!50003 TRIGGER on_group_delete AFTER DELETE ON groups FOR EACH ROW CALL user_remove() */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `has_setting`
--

DROP TABLE IF EXISTS `has_setting`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `has_setting` (
  `group_id` int(11) NOT NULL COMMENT 'The ID of the group.',
  `setting_id` int(11) NOT NULL COMMENT 'The ID of the unique settings JSON object.',
  PRIMARY KEY (`group_id`),
  KEY `setting_id` (`setting_id`),
  CONSTRAINT `has_setting_1` FOREIGN KEY (`group_id`) REFERENCES `groups` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `has_setting_2` FOREIGN KEY (`setting_id`) REFERENCES `bot_setting` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `keyword_mapping`
--

DROP TABLE IF EXISTS `keyword_mapping`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `keyword_mapping` (
  `group_id` int(11) NOT NULL COMMENT 'The ID of the group which has the keyword mapping.',
  `phrase` varchar(191) NOT NULL COMMENT 'The keyword that will map to a specific string.',
  `mapping` varchar(191) NOT NULL COMMENT 'The target content to send when the phrase is found in a message.',
  PRIMARY KEY (`group_id`,`phrase`),
  CONSTRAINT `keyword_mapping_1` FOREIGN KEY (`group_id`) REFERENCES `groups` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `memories`
--

DROP TABLE IF EXISTS `memories`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `memories` (
  `memory_id` int(11) NOT NULL COMMENT 'The ID of the message, from the GroupMe API.',
  `group_id` int(11) NOT NULL COMMENT 'The group ID of the message that was sent. ',
  `date` datetime NOT NULL COMMENT 'The date the message was sent.',
  `text` varchar(191) NOT NULL COMMENT 'The contents of the message.',
  PRIMARY KEY (`memory_id`),
  KEY `memories_1` (`group_id`),
  CONSTRAINT `memories_1` FOREIGN KEY (`group_id`) REFERENCES `groups` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `part_of`
--

DROP TABLE IF EXISTS `part_of`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `part_of` (
  `user_id` int(11) NOT NULL COMMENT 'The user ID of the GroupMe user.',
  `group_id` int(11) NOT NULL COMMENT 'The group ID of the GroupMe group.',
  `is_group_admin` tinyint(1) NOT NULL COMMENT 'Whether the given user has admin privileges in the group.',
  PRIMARY KEY (`user_id`,`group_id`),
  KEY `group_id` (`group_id`),
  CONSTRAINT `part_of_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `part_of_2` FOREIGN KEY (`group_id`) REFERENCES `groups` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `reminder`
--

DROP TABLE IF EXISTS `reminder`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `reminder` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT 'The unique ID of the reminder that is auto-generated when the record is added to the DB.',
  `text` varchar(191) NOT NULL COMMENT 'The content of the reminder to send to the group.',
  `timestamp` datetime NOT NULL COMMENT 'A datetime object of when to send the reminder. Will be updated if the reminder is recurring.',
  `frequency` int(11) DEFAULT NULL COMMENT 'How often the reminder should be sent, measured in minutes. If NULL, then the reminder is one-time.',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `reminder_history`
--

DROP TABLE IF EXISTS `reminder_history`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `reminder_history` (
  `reminder_id` int(11) NOT NULL COMMENT 'The ID of the reminder.',
  `sent` datetime NOT NULL COMMENT 'A datetime object of when the reminder was sent to the group. ',
  `text` varchar(191) NOT NULL COMMENT 'The reminder message that was sent to the group.',
  `group_id` int(11) NOT NULL COMMENT 'The group ID of the group in which the reminder was sent.',
  PRIMARY KEY (`reminder_id`),
  KEY `reminder_history_2` (`group_id`),
  CONSTRAINT `reminder_history_1` FOREIGN KEY (`reminder_id`) REFERENCES `reminder` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `reminder_history_2` FOREIGN KEY (`group_id`) REFERENCES `groups` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `reminder_type`
--

DROP TABLE IF EXISTS `reminder_type`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `reminder_type` (
  `reminder_id` int(11) NOT NULL COMMENT 'The ID of the reminder.',
  `type` varchar(191) NOT NULL COMMENT 'The type of the reminder (could have multiple rows for a single reminder).',
  PRIMARY KEY (`reminder_id`,`type`),
  CONSTRAINT `reminder_type_1` FOREIGN KEY (`reminder_id`) REFERENCES `reminder` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `reminds`
--

DROP TABLE IF EXISTS `reminds`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `reminds` (
  `reminder_id` int(11) NOT NULL COMMENT 'The ID of the reminder.',
  `group_id` int(11) NOT NULL COMMENT 'The ID of the group in which the reminder will be sent.',
  PRIMARY KEY (`reminder_id`),
  KEY `reminds_2` (`group_id`),
  CONSTRAINT `reminds_1` FOREIGN KEY (`reminder_id`) REFERENCES `reminder` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `reminds_2` FOREIGN KEY (`group_id`) REFERENCES `groups` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `users` (
  `id` int(11) NOT NULL COMMENT 'The unique user ID from the GroupMe API.',
  `name` varchar(191) NOT NULL COMMENT 'The username of the GroupMe user.',
  `num_reminders` int(11) NOT NULL COMMENT 'The number of reminders the GroupMe user has created.',
  `access_token` varchar(191) NOT NULL COMMENT 'The unique access token for the user through the GroupMe API after they login through the UI.',
  `image_url` varchar(500) DEFAULT NULL COMMENT 'User''s profile image.',
  PRIMARY KEY (`id`),
  UNIQUE KEY `access_token` (`access_token`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2021-11-21 15:34:48
