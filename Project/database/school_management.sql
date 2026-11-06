SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS `attendance`;
DROP TABLE IF EXISTS `grades`;
DROP TABLE IF EXISTS `registrations`;
DROP TABLE IF EXISTS `courses`;
DROP TABLE IF EXISTS `students`;
DROP TABLE IF EXISTS `teachers`;
DROP TABLE IF EXISTS `users`;

CREATE TABLE `users` (
  `user_id` int NOT NULL AUTO_INCREMENT,
  `username` varchar(50) NOT NULL,
  `password` varchar(255) NOT NULL,
  `role` enum('admin','teacher','student') NOT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`user_id`),
  UNIQUE KEY `username` (`username`)
) ENGINE=InnoDB AUTO_INCREMENT=19 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `teachers` (
  `teacher_id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `first_name` varchar(50) NOT NULL,
  `last_name` varchar(50) NOT NULL,
  `email` varchar(100) NOT NULL,
  `phone` varchar(20) DEFAULT NULL,
  `department` varchar(100) DEFAULT NULL,
  `hire_date` date NOT NULL,
  PRIMARY KEY (`teacher_id`),
  UNIQUE KEY `user_id` (`user_id`),
  UNIQUE KEY `email` (`email`),
  KEY `idx_teachers_last_name` (`last_name`),
  KEY `idx_teachers_department` (`department`),
  CONSTRAINT `fk_teacher_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `students` (
  `student_id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `first_name` varchar(50) NOT NULL,
  `last_name` varchar(50) NOT NULL,
  `email` varchar(100) NOT NULL,
  `date_of_birth` date NOT NULL,
  `phone` varchar(20) DEFAULT NULL,
  `group_name` varchar(20) NOT NULL,
  `enrollment_date` date NOT NULL,
  PRIMARY KEY (`student_id`),
  UNIQUE KEY `user_id` (`user_id`),
  UNIQUE KEY `email` (`email`),
  KEY `idx_students_last_name` (`last_name`),
  KEY `idx_students_group_name` (`group_name`),
  CONSTRAINT `fk_student_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=16 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `courses` (
  `course_id` int NOT NULL AUTO_INCREMENT,
  `course_code` varchar(20) NOT NULL,
  `course_name` varchar(100) NOT NULL,
  `teacher_id` int NOT NULL,
  `credits` int NOT NULL DEFAULT '3',
  `semester` varchar(20) NOT NULL,
  `max_students` int NOT NULL DEFAULT '30',
  PRIMARY KEY (`course_id`),
  UNIQUE KEY `course_code` (`course_code`),
  KEY `idx_courses_name` (`course_name`),
  KEY `idx_courses_teacher` (`teacher_id`),
  CONSTRAINT `fk_course_teacher` FOREIGN KEY (`teacher_id`) REFERENCES `teachers` (`teacher_id`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `registrations` (
  `registration_id` int NOT NULL AUTO_INCREMENT,
  `student_id` int NOT NULL,
  `course_id` int NOT NULL,
  `registered_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`registration_id`),
  UNIQUE KEY `uq_reg` (`student_id`,`course_id`),
  KEY `idx_registrations_student` (`student_id`),
  KEY `idx_registrations_course` (`course_id`),
  CONSTRAINT `fk_reg_course` FOREIGN KEY (`course_id`) REFERENCES `courses` (`course_id`),
  CONSTRAINT `fk_reg_student` FOREIGN KEY (`student_id`) REFERENCES `students` (`student_id`)
) ENGINE=InnoDB AUTO_INCREMENT=43 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `grades` (
  `grade_id` int NOT NULL AUTO_INCREMENT,
  `registration_id` int NOT NULL,
  `grade` decimal(5,2) DEFAULT NULL,
  `letter_grade` varchar(2) DEFAULT NULL,
  `graded_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `comments` text,
  PRIMARY KEY (`grade_id`),
  UNIQUE KEY `registration_id` (`registration_id`),
  CONSTRAINT `fk_grade_reg` FOREIGN KEY (`registration_id`) REFERENCES `registrations` (`registration_id`)
) ENGINE=InnoDB AUTO_INCREMENT=76 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `attendance` (
  `attendance_id` int NOT NULL AUTO_INCREMENT,
  `registration_id` int NOT NULL,
  `att_date` date NOT NULL,
  `status` enum('Present','Absent','Late') NOT NULL DEFAULT 'Present',
  `marked_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`attendance_id`),
  UNIQUE KEY `uq_reg_date` (`registration_id`,`att_date`),
  CONSTRAINT `attendance_ibfk_1` FOREIGN KEY (`registration_id`) REFERENCES `registrations` (`registration_id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=12 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

INSERT INTO `users` VALUES
(1,'Tony_Stark','fe5ad05817f88c2dc247190b9b35e18f48a6a6665226f823c450ac3624b1ae92','teacher','2026-04-22 18:46:42'),
(2,'Bruce_Benner','80328be0774b084f89764b22086a4ceb54e362c0417c07576f1ff8f997e1f43a','teacher','2026-04-22 18:46:42'),
(3,'Harry_Potter','b7024faf10910fd56f2121d413bc866d92a5514c682c48cb1e64e223d7ef46cb','student','2026-04-22 18:46:42'),
(4,'Ludovick_TheFirst','761f0a9d8b88ca9812c36ca8334a37b84f489266f7e821a69912ddb996a62bbc','student','2026-04-22 18:46:42'),
(5,'Ariana_Grande','98047a6e1f47582c492f726038b7ae7e37c8bb1e8015eb5df9e060aa7c5f629b','student','2026-04-22 18:46:42'),
(6,'Olivia_Rodrigo','984358b1ceabe316feadf652c38e012154f3fb199ff0a7006a42ff6c1eebb419','student','2026-04-22 18:46:42'),
(7,'Oscar_Isaac','a0ed8215d30e9408cfd4f1256afc3a1ee2e72da9b9369200d9321edea35636e2','student','2026-04-22 18:46:42'),
(8,'Anya_Taylor','7db5b411f0cc3b533da74c29f01a1c73e11a53293accedfad4b28f5cfb6a8490','student','2026-04-22 18:46:42'),
(9,'Timothee_Chalamet','b9e418bed662ee2d4e6581085ef0e89c185f7c65f9a358f517d09ce409977980','student','2026-04-22 18:46:42'),
(10,'Zendaya_Coleman','3dc012967ca819ae261125bcf216068ee503e836ad28b8ab8456c569c3f3dc5e','student','2026-04-22 18:46:42'),
(11,'Sydney_Sweeney','b31a9669e201d3716d6c38c973b905e55c770949965219aa14358a84fd845235','student','2026-04-22 18:46:42'),
(12,'Jacob_Elordi','02f09a323bf4abbdd4682ca6edadcbe5513039f0c0a3177e43045d3511afb732','student','2026-04-22 18:46:42'),
(13,'Sabrina_Carpenter','649a38f09be67d6cd1ac6d04509e74b3366360c4f75c45aa9be2faeec4899003','student','2026-04-22 18:46:42'),
(14,'Austin_Butler','289b0a27c20c3d856475af60dcae71a2019361ff5c94ff46f753f3a5def96ed7','student','2026-04-22 18:46:42'),
(15,'Jenipher_Alana','b4ecaca49d43e738065401b7673d27de2fdefc8a065ca0dfae31131f13c9ebbf','student','2026-04-24 12:08:16'),
(17,'Peter_Parker','edf431400408e764fc359b769a8cbf35c15315600385eef20690c9fa48592f90','student','2026-04-28 10:18:19'),
(18,'Alexandre_Ghlonti','e3c4b9366ae9f8b03357c03ea7953b24d7cb4523826ad7928ed2406fd277d200','student','2026-05-23 14:57:33');

INSERT INTO `teachers` VALUES
(1,1,'Tony','Stark','t.stark@coventry.edu.kz','+77011234567','Computer Science','2019-09-01'),
(2,2,'Bruce','Benner','b.benner@coventry.edu.kz','+77019876543','Mathematics','2020-01-15');

INSERT INTO `students` VALUES
(1,3,'Harry','Potter','h.potter@coventry.edu.kz','2007-03-15','+77051112233','CS-1','2025-09-01'),
(2,4,'Ludovick','TheFirst','l.t.first@coventry.edu.kz','2007-07-22','+77052223344','CS-1','2025-09-01'),
(3,5,'Ariana','Grande','a.grande@coventry.edu.kz','2006-11-08','+77053334455','CS-1','2025-09-01'),
(4,6,'Olivia','Rodrigo','o.rodrigo@coventry.edu.kz','2008-05-30','+77054445566','CS-1','2025-09-01'),
(5,7,'Oscar','Isaac','o.isaac@coventry.edu.kz','2007-09-14','+77055556677','CS-1','2025-09-01'),
(6,8,'Anya','Taylor','a.taylor@coventry.edu.kz','2008-01-25','+77056667788','CS-1','2025-09-01'),
(7,9,'Timothee','Chalamet','t.chalamet@coventry.edu.kz','2006-03-15','+77051112234','MT-2','2025-09-01'),
(8,10,'Zendaya','Coleman','z.coleman@coventry.edu.kz','2007-07-23','+77052223345','MT-2','2025-09-01'),
(9,11,'Sydney','Sweeney','s.sweeney@coventry.edu.kz','2006-11-09','+77053334456','MT-2','2025-09-01'),
(10,12,'Jacob','Elordi','j.elordi@coventry.edu.kz','2007-05-31','+77054445567','MT-2','2025-09-01'),
(11,13,'Sabrina','Carpenter','s.carpenter@coventry.edu.kz','2006-09-15','+77055556678','MT-2','2025-09-01'),
(12,14,'Austin','Butler','a.butler@coventry.edu.kz','2007-01-26','+77056667789','MT-2','2025-09-01'),
(13,15,'Jenipher','Alana','jalana@coventry.edu.kz','2007-03-21','+77759821035','MT-2','2025-09-12'),
(14,17,'Peter','Parker','p.parker@coventry.edu.kz','2007-03-12','+77004322345','CS-1','2025-09-05'),
(15,18,'Alexandre','Ghlonti','a.ghlonti@coventry.edu.kz','2007-08-19','+77608972234','CS-2','2025-10-01');

INSERT INTO `courses` VALUES
(1,'CS301','Database Systems',1,4,'Spring 2025',30),
(2,'CS302','Software Engineering',1,3,'Spring 2025',30),
(3,'MT301','Discrete Mathematics',2,3,'Spring 2025',35),
(4,'CS303','Algorithms & Data Structures',1,4,'Fall 2024',30),
(5,'MT302','Calculus 2',2,3,'Fall 2024',35),
(6,'EL205','English literature',2,4,'Fall 2025',25);

INSERT INTO `registrations` VALUES
(1,1,1,'2026-04-22 18:48:17'),(2,1,2,'2026-04-22 18:48:17'),(3,1,3,'2026-04-22 18:48:17'),
(4,2,1,'2026-04-22 18:48:17'),(5,2,2,'2026-04-22 18:48:17'),(6,2,3,'2026-04-22 18:48:17'),
(7,3,1,'2026-04-22 18:48:17'),(8,3,2,'2026-04-22 18:48:17'),(9,3,3,'2026-04-22 18:48:17'),
(10,4,1,'2026-04-22 18:48:17'),(11,4,2,'2026-04-22 18:48:17'),(12,4,3,'2026-04-22 18:48:17'),
(13,5,1,'2026-04-22 18:48:17'),(14,5,4,'2026-04-22 18:48:17'),(15,5,5,'2026-04-22 18:48:17'),
(16,6,1,'2026-04-22 18:48:17'),(17,6,4,'2026-04-22 18:48:17'),(18,6,5,'2026-04-22 18:48:17'),
(19,7,1,'2026-04-22 18:48:17'),(20,7,2,'2026-04-22 18:48:17'),(21,7,3,'2026-04-22 18:48:17'),
(22,8,1,'2026-04-22 18:48:17'),(23,8,4,'2026-04-22 18:48:17'),(24,8,5,'2026-04-22 18:48:17'),
(25,9,1,'2026-04-22 18:48:17'),(26,9,2,'2026-04-22 18:48:17'),(27,9,3,'2026-04-22 18:48:17'),
(28,10,1,'2026-04-22 18:48:17'),(29,10,4,'2026-04-22 18:48:17'),(30,10,5,'2026-04-22 18:48:17'),
(31,11,1,'2026-04-22 18:48:17'),(32,11,2,'2026-04-22 18:48:17'),(33,11,3,'2026-04-22 18:48:17'),
(34,12,1,'2026-04-22 18:48:17'),(35,12,4,'2026-04-22 18:48:17'),(36,12,5,'2026-04-22 18:48:17'),
(37,14,1,'2026-04-28 10:18:41'),(41,7,6,'2026-05-10 20:58:58'),(42,13,5,'2026-05-10 20:59:03');

INSERT INTO `grades` VALUES
(5,5,85.50,'B','2026-04-22 18:49:20','Solid, but be more careful'),
(6,6,78.00,'C+','2026-04-22 18:49:20','Basic understanding, keep working'),
(7,7,79.50,'C+','2026-04-22 18:49:20','Nice effort, review topics'),
(8,8,95.00,'A+','2026-04-22 18:49:20','Excellent work'),
(9,9,83.00,'B','2026-04-22 18:49:20','Good, small mistakes'),
(10,10,70.00,'C','2026-04-22 18:49:20','Passed, but needs practice'),
(11,11,88.00,'B+','2026-04-22 18:49:20','Well done overall'),
(62,1,88.50,'B+','2026-04-22 18:57:17','Good work, just refine queries'),
(63,2,92.00,'A','2026-04-22 18:57:17','Great job, very clear'),
(64,3,93.70,'A+','2026-05-11 10:33:59','Needs more practice'),
(65,4,91.00,'A','2026-04-22 18:57:17','Strong performance'),
(66,12,60.50,'D','2026-04-22 18:59:21','Needs improvement'),
(67,13,72.00,'C','2026-04-22 18:59:21','Average, can do better'),
(68,14,91.50,'A','2026-04-22 18:59:21','Very good job'),
(69,15,85.00,'B','2026-04-22 18:59:21','Good progress'),
(70,16,77.00,'C+','2026-04-22 18:59:21','A bit inconsistent'),
(71,17,89.00,'B+','2026-04-22 18:59:21','Almost there, good work'),
(72,18,93.00,'A','2026-04-22 18:59:21','Really strong work'),
(73,32,60.00,'C+','2026-05-10 11:16:13',NULL),
(74,31,23.00,'F','2026-05-10 21:08:36',NULL);

INSERT INTO `attendance` VALUES
(1,9,'2026-05-07','Present','2026-05-07 14:33:38'),
(2,34,'2026-05-07','Present','2026-05-07 14:56:51'),
(3,18,'2026-05-07','Late','2026-05-07 14:56:55'),
(4,5,'2026-05-07','Absent','2026-05-07 14:57:02'),
(5,31,'2026-05-08','Absent','2026-05-08 06:02:28'),
(7,34,'2026-05-10','Present','2026-05-10 15:59:23'),
(8,33,'2026-05-15','Late','2026-05-15 07:18:21'),
(9,3,'2026-05-26','Absent','2026-05-26 06:16:41'),
(10,3,'2026-05-25','Present','2026-05-26 06:16:58'),
(11,1,'2026-05-01','Late','2026-05-26 06:17:10');

SET FOREIGN_KEY_CHECKS = 1;
