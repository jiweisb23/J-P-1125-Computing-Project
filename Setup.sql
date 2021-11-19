--  CREATE CONTACTS DB

DROP DATABASE IF EXISTS `Vehicles`;
CREATE DATABASE IF NOT EXISTS `Vehicles`;
USE `Vehicles`;

--  CREATE Vehicles TABLE

CREATE TABLE `Vehicles` (
   `vehicleNo`   varchar (40),
   `currentTime`   varchar (40),
   `currentCharge`   varchar (40),
   `desiredCharge`   varchar (40),
   `departureTime`   varchar (40),
   `newStatus`   varchar (40),
   `lastChargingStatus`   varchar (40),
   `estimatedSavings`   varchar (40),
   `recordStatus`   varchar (40)
);

--  INSERT INTO Vehicles

-- INSERT INTO `contacts` VALUES('Peter');