CREATE TABLE IF NOT EXISTS `user`(
  `id` INT UNSIGNED AUTO_INCREMENT,
  `username` VARCHAR(150) NOT NULL,
  `password` VARCHAR(128) NOT NULL,
  `fullname` VARCHAR(150),
  `email` VARCHAR(254) NOT NULL,
  `join_time` DATETIME NOT NULL,
  `role` TINYINT NOT NULL,
  `status` TINYINT NOT NULL,
  PRIMARY KEY ( `id` )
)ENGINE=InnoDB DEFAULT CHARSET=utf8;


CREATE TABLE IF NOT EXISTS `session`(
  `session_id` VARCHAR(40) NOT NULL,
  `user_id` INT NOT NULL,
  `session_data` LONGTEXT NOT NULL,
  `create_time` DATETIME NOT NULL,
  `expire_time` DATETIME NOT NULL,
  PRIMARY KEY ( `session_id` )
)ENGINE=InnoDB DEFAULT CHARSET=utf8;


CREATE TABLE IF NOT EXISTS `auditlog`(
  `id` INT UNSIGNED AUTO_INCREMENT,
  `user_id` INT NOT NULL,
  `uri` VARCHAR(200) NOT NULL,
  `method` VARCHAR(10) NOT NULL,
  `reqdata` LONGTEXT,
  `record_time` DATETIME,
  PRIMARY KEY ( `id` )
)ENGINE=InnoDB DEFAULT CHARSET=utf8;


CREATE TABLE IF NOT EXISTS `logfile`(
  `id` INT UNSIGNED AUTO_INCREMENT,
  `name` VARCHAR(200) NOT NULL,
  `host` LONGTEXT NOT NULL,
  `path` VARCHAR(1024) NOT NULL,
  `create_time` DATETIME,
  `comment` VARCHAR(200),
  `monitor_choice` INT,
  PRIMARY KEY ( `id` )
)ENGINE=InnoDB DEFAULT CHARSET=utf8;


CREATE TABLE IF NOT EXISTS `logfile_host`(
  `id` INT UNSIGNED AUTO_INCREMENT,
  `logfile_id` TINYINT NOT NULL,
  `host` VARCHAR(200) NOT NULL,
  PRIMARY KEY ( `id` )
)ENGINE=InnoDB DEFAULT CHARSET=utf8;


CREATE TABLE IF NOT EXISTS `monitor_item`(
  `id` INT UNSIGNED AUTO_INCREMENT,
  `logfile_id` INT NOT NULL,
  `match_regex` VARCHAR(200) NOT NULL,
  `name` VARCHAR(200) NOT NULL,
  `alert` INT,
  `intervals` INT,
  `expression` VARCHAR(100),
  `webhook` VARCHAR(500),
  `create_time` DATETIME,
  `comment` VARCHAR(200),
  PRIMARY KEY ( `id` )
)ENGINE=InnoDB DEFAULT CHARSET=utf8;


CREATE TABLE IF NOT EXISTS `monitor_count`(
  `id` INT UNSIGNED AUTO_INCREMENT,
  `logfile_id` INT NOT NULL,
  `host` VARCHAR(200) NOT NULL,
  `monitor_item_id` INT NOT NULL,
  `count` INT NOT NULL,
  `count_time` DATETIME,
  PRIMARY KEY ( `id` )
)ENGINE=InnoDB DEFAULT CHARSET=utf8;

ALTER TABLE user ADD INDEX username_idx(username);
ALTER TABLE logfile ADD INDEX name_idx(name);
ALTER TABLE auditlog ADD INDEX user_id_idx(user_id);
ALTER TABLE logfile_host ADD INDEX logfile_id_idx(logfile_id);
ALTER TABLE logfile_host ADD INDEX host_idx(host);
ALTER TABLE monitor_item ADD INDEX logfile_id_idx(logfile_id);
ALTER TABLE monitor_count ADD INDEX count_time_idx(count_time);