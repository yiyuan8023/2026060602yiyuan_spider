CREATE TABLE `goods_data__goods_general_situation`
(
    `id`            bigint   NOT NULL AUTO_INCREMENT COMMENT '自增ID',
    `payOrdrAmt`    varchar(255)      DEFAULT NULL,
    `payOrdrCnt`    varchar(255)      DEFAULT NULL,
    `payUvRto`      varchar(255)      DEFAULT NULL,
    `gpv`           varchar(255)      DEFAULT NULL,
    `guv`           varchar(255)      DEFAULT NULL,
    `vstGoodsCnt`   varchar(255)      DEFAULT NULL,
    `payOrdrUsrCnt` varchar(255)      DEFAULT NULL,
    `cfmOrdrUsrCnt` varchar(255)      DEFAULT NULL,
    `cfmOrdrCnt`    varchar(255)      DEFAULT NULL,
    `goodsFavCnt`   varchar(255)      DEFAULT NULL,
    `createtime`    datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updatetime`    datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=6949 DEFAULT CHARSET=utf8mb3;