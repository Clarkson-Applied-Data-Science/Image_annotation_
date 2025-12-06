

CREATE TABLE `images` (
  `Image_ID` int NOT NULL,
  `Image_path` varchar(255) DEFAULT NULL,
  `Date_added` datetime DEFAULT NULL,
  `Project_ID` int DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;



INSERT INTO `images` (`Image_ID`, `Image_path`, `Date_added`, `Project_ID`) VALUES
(1, 'static/uploads/1/humanoid-robot.jpg', '2025-12-03 10:47:48', 1),
(2, 'static/uploads/2/photo-1643990331688-68ff3eb61675.jfif', '2025-12-05 14:24:28', 2);



CREATE TABLE `labels` (
  `Label_ID` int NOT NULL,
  `L_Name` varchar(255) DEFAULT NULL,
  `UID` int DEFAULT NULL,
  `Image_ID` int DEFAULT NULL,
  `Description` varchar(500) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;



INSERT INTO `labels` (`Label_ID`, `L_Name`, `UID`, `Image_ID`, `Description`) VALUES
(1, 'robot', 5, 2, 'image of a robot sitting');

-- --------------------------------------------------------


CREATE TABLE `project` (
  `Project_ID` int NOT NULL,
  `Project_name` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;



INSERT INTO `project` (`Project_ID`, `Project_name`) VALUES
(1, 'weather'),
(2, 'images');



CREATE TABLE `users` (
  `UID` int NOT NULL,
  `name` varchar(255) NOT NULL,
  `email` varchar(255) NOT NULL,
  `role` varchar(50) NOT NULL DEFAULT 'user',
  `password` varchar(255) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;



INSERT INTO `users` (`UID`, `name`, `email`, `role`, `password`) VALUES
(3, 'Joijode', 'joijodp@clarkson.edu', 'customer', 'a4eb2e0f3e0cbac5c3e64ddc4d24f1df'),
(5, 'Tyler', 'tconlon@clarkson.edu', 'admin', 'adf47922f0bdb6b9a520ed2d43622d14');


ALTER TABLE `images`
  ADD PRIMARY KEY (`Image_ID`),
  ADD KEY `Project_ID` (`Project_ID`);


ALTER TABLE `labels`
  ADD PRIMARY KEY (`Label_ID`),
  ADD KEY `UID` (`UID`),
  ADD KEY `Image_ID` (`Image_ID`);

ALTER TABLE `project`
  ADD PRIMARY KEY (`Project_ID`);


ALTER TABLE `users`
  ADD PRIMARY KEY (`UID`),
  ADD UNIQUE KEY `email` (`email`);


ALTER TABLE `images`
  MODIFY `Image_ID` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;


ALTER TABLE `labels`
  MODIFY `Label_ID` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

ALTER TABLE `project`
  MODIFY `Project_ID` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;


ALTER TABLE `users`
  MODIFY `UID` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=7;


ALTER TABLE `images`
  ADD CONSTRAINT `images_ibfk_1` FOREIGN KEY (`Project_ID`) REFERENCES `project` (`Project_ID`);


ALTER TABLE `labels`
  ADD CONSTRAINT `labels_ibfk_1` FOREIGN KEY (`UID`) REFERENCES `users` (`UID`),
  ADD CONSTRAINT `labels_ibfk_2` FOREIGN KEY (`Image_ID`) REFERENCES `images` (`Image_ID`);
COMMIT;

