-- 本地开发库初始化。调用时机：首次搭建开发环境时用超级用户执行一次。
-- 用法：psql -U postgres -f scripts\init-local-db.sql

CREATE ROLE skills LOGIN PASSWORD 'skills_dev';
CREATE DATABASE skills OWNER skills ENCODING 'UTF8';
