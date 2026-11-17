CREATE TABLE IF NOT EXISTS `kanotugm_auth` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `token` VARCHAR(64) NOT NULL UNIQUE,
    `owner` VARCHAR(100),
    `active` TINYINT(1) NOT NULL DEFAULT 1,
    `created` DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS `kanotugm_logs` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `token` VARCHAR(64),
    `endpoint` VARCHAR(50) NOT NULL,
    `params` TEXT,
    `code` TINYINT,
    `msg` VARCHAR(255),
    `sqltime` DOUBLE,
    `ip` VARCHAR(45),
    `dt` DATETIME NOT NULL
);

INSERT IGNORE INTO `kanotugm_auth` (`token`, `owner`, `active`) VALUES ('123', 'kanotugm', 1);
