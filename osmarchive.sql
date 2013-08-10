CREATE TABLE IF NOT EXISTS `osm_changesets` (
  `id` int(10) unsigned NOT NULL,
  `created_at` DATETIME NOT NULL,
  `closed_at` DATETIME NULL DEFAULT NULL,
  `userid` int(10) unsigned NULL DEFAULT NULL,
  `username` varchar(255) COLLATE utf8_bin NULL DEFAULT NULL,
  `top` decimal(10,7) DEFAULT NULL,
  `left` decimal(10,7) DEFAULT NULL,
  `bottom` decimal(10,7) DEFAULT NULL,
  `right` decimal(10,7) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin;

CREATE TABLE IF NOT EXISTS `osm_changeset_tags` (
  `changeset_id` int(10) unsigned NOT NULL,
  `sequence` smallint(5) unsigned NOT NULL DEFAULT '0',
  `key` varchar(255) COLLATE utf8_bin NOT NULL,
  `value` varchar(255) COLLATE utf8_bin NOT NULL,
  PRIMARY KEY (`changeset_id`,`sequence`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin;

CREATE TABLE IF NOT EXISTS `osm_nodes` (
  `id` bigint(20) NOT NULL,
  `version` smallint(6) NOT NULL,
  `changeset` int(11) NOT NULL,
  `userid` int(11) NOT NULL,
  `username` varchar(255) COLLATE utf8_bin NOT NULL,
  `visible` tinyint(1) NOT NULL DEFAULT '1',
  `timestamp` datetime NOT NULL,
  `lat` decimal(10,7) NOT NULL,
  `lon` decimal(10,7) NOT NULL,
  `geohash` varchar(12) COLLATE utf8_bin DEFAULT NULL,
  PRIMARY KEY (`id`,`version`),
  KEY `changeset` (`changeset`),
  KEY `userid` (`userid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin;

CREATE TABLE IF NOT EXISTS `osm_node_tags` (
  `node_id` int(10) unsigned NOT NULL,
  `node_version` smallint(5) unsigned NOT NULL,
  `sequence` smallint(5) unsigned NOT NULL,
  `key` varchar(255) COLLATE utf8_bin NOT NULL,
  `value` varchar(255) COLLATE utf8_bin NOT NULL,
  PRIMARY KEY (`node_id`,`node_version`,`sequence`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin;

CREATE TABLE IF NOT EXISTS `osm_relations` (
  `id` bigint(20) NOT NULL,
  `version` smallint(6) NOT NULL,
  `changeset` int(11) NOT NULL,
  `userid` int(11) NOT NULL,
  `username` varchar(255) COLLATE utf8_bin NOT NULL,
  `visible` tinyint(1) NOT NULL DEFAULT '1',
  `timestamp` datetime NOT NULL,
  `geohash` varchar(12) COLLATE utf8_bin DEFAULT NULL,
  PRIMARY KEY (`id`,`version`),
  KEY `changeset` (`changeset`),
  KEY `userid` (`userid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin;

CREATE TABLE IF NOT EXISTS `osm_relation_members` (
  `relation_id` bigint(20) unsigned NOT NULL,
  `relation_version` int(10) unsigned NOT NULL,
  `member_role` varchar(255) COLLATE utf8_bin NOT NULL,
  `member_type` enum('node','way','relation') COLLATE utf8_bin NOT NULL,
  `member_id` bigint(20) unsigned NOT NULL,
  `member_order` smallint(5) unsigned NOT NULL,
  PRIMARY KEY (`relation_id`,`relation_version`,`member_order`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin;

CREATE TABLE IF NOT EXISTS `osm_relation_tags` (
  `relation_id` int(10) unsigned NOT NULL,
  `relation_version` smallint(5) unsigned NOT NULL,
  `sequence` smallint(5) unsigned NOT NULL,
  `key` varchar(255) COLLATE utf8_bin NOT NULL,
  `value` varchar(255) COLLATE utf8_bin NOT NULL,
  PRIMARY KEY (`relation_id`,`relation_version`,`sequence`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin;

CREATE TABLE IF NOT EXISTS `osm_ways` (
  `id` bigint(20) NOT NULL,
  `version` smallint(6) NOT NULL,
  `changeset` int(11) NOT NULL,
  `userid` int(11) NOT NULL,
  `username` varchar(255) COLLATE utf8_bin NOT NULL,
  `visible` tinyint(1) NOT NULL DEFAULT '1',
  `timestamp` datetime NOT NULL,
  `geohash` varchar(12) COLLATE utf8_bin DEFAULT NULL,
  PRIMARY KEY (`id`,`version`),
  KEY `changeset` (`changeset`),
  KEY `userid` (`userid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin;

CREATE TABLE IF NOT EXISTS `osm_way_nodes` (
  `way_id` bigint(20) unsigned NOT NULL,
  `way_version` int(11) unsigned NOT NULL,
  `node_order` smallint(5) unsigned NOT NULL,
  `node_id` bigint(20) unsigned NOT NULL,
  `node_version` int(11) unsigned NOT NULL,
  PRIMARY KEY (`way_id`,`way_version`,`node_order`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin;

CREATE TABLE IF NOT EXISTS `osm_way_tags` (
  `way_id` int(10) unsigned NOT NULL,
  `way_version` smallint(5) unsigned NOT NULL,
  `sequence` smallint(5) unsigned NOT NULL,
  `key` varchar(255) COLLATE utf8_bin NOT NULL,
  `value` varchar(255) COLLATE utf8_bin NOT NULL,
  PRIMARY KEY (`way_id`,`way_version`,`sequence`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin;
