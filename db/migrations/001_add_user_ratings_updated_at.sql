-- 已建库项目的增量迁移：为用户评分表补充更新时间字段
-- 如果字段已经存在，本脚本会报重复字段错误，可忽略。
ALTER TABLE user_ratings
    ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
    AFTER created_at;
