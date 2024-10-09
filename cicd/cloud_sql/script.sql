
/* DDL for chats table. All the rest of tables are auto created while */
DROP IF EXISTS TABLE voiceClone_tg_chats;
CREATE TABLE voiceClone_tg_chats (
    document_id varchar(50)  COLLATE utf8mb4_unicode_ci,
    content nvarchar(1000) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;,
    timestamp datetime,
    role nvarchar(20) COLLATE utf8mb4_unicode_ci,
    content_type varchar(10) COLLATE utf8mb4_unicode_ci,
    reachout varchar(10) COLLATE utf8mb4_unicode_ci,
    response_status varchar(255) COLLATE utf8mb4_unicode_ci,
    message_id float,
    update_id float,
    data_loaded_on datetime
);
-- ALTER TABLE voiceClone_tg_chats MODIFY COLUMN content VARCHAR(1000) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
-- ALTER TABLE voiceClone_tg_chats MODIFY COLUMN document_id VARCHAR(50) COLLATE utf8mb4_unicode_ci;
-- ALTER TABLE voiceClone_tg_chats MODIFY COLUMN role VARCHAR(20) COLLATE utf8mb4_unicode_ci;
-- ALTER TABLE voiceClone_tg_chats MODIFY COLUMN content_type VARCHAR(10) COLLATE utf8mb4_unicode_ci;
-- ALTER TABLE voiceClone_tg_chats MODIFY COLUMN reachout VARCHAR(10) COLLATE utf8mb4_unicode_ci;
-- ALTER TABLE voiceClone_tg_chats MODIFY COLUMN response_status VARCHAR(255) COLLATE utf8mb4_unicode_ci;

DROP TABLE IF EXISTS voiceClone_tg_logs;
CREATE TABLE voiceClone_tg_logs (
    document_id varchar(50)  COLLATE utf8mb4_unicode_ci,
    tg_user_id varchar(50)  COLLATE utf8mb4_unicode_ci,
    char_id varchar(50)  COLLATE utf8mb4_unicode_ci,
    message varchar(255) COLLATE utf8mb4_unicode_ci,
    message_id float,
    origin varchar(255) COLLATE utf8mb4_unicode_ci,
    status varchar(20) COLLATE utf8mb4_unicode_ci,
    status_cd varchar(5) COLLATE utf8mb4_unicode_ci,
    timestamp datetime,
    data_loaded_on datetime
);

-- DROP TABLE IF EXISTS error_analysis;
-- CREATE TABLE error_analysis (
--     document_id varchar(50)  COLLATE utf8mb4_unicode_ci,
--     tg_user_id varchar(50)  COLLATE utf8mb4_unicode_ci,
--     char_id varchar(50)  COLLATE utf8mb4_unicode_ci,
--     message varchar(255) COLLATE utf8mb4_unicode_ci,
--     message_id float,
--     origin varchar(255) COLLATE utf8mb4_unicode_ci,
--     error_category varchar(50)  COLLATE utf8mb4_unicode_ci,
--     log_date date,
--     data_loaded_on date
-- );

-- ALTER DATABASE <database_name> CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE voiceClone_characters MODIFY COLUMN char_id VARCHAR(50) COLLATE utf8mb4_unicode_ci;
ALTER TABLE voiceClone_characters MODIFY COLUMN character_name VARCHAR(50) COLLATE utf8mb4_unicode_ci;
ALTER TABLE voiceClone_tg_users MODIFY COLUMN document_id TEXT COLLATE utf8mb4_unicode_ci;
ALTER TABLE voiceClone_tg_users MODIFY COLUMN tg_user_id TEXT COLLATE utf8mb4_unicode_ci;
ALTER TABLE voiceClone_tg_users MODIFY COLUMN char_id TEXT COLLATE utf8mb4_unicode_ci;
ALTER TABLE voiceClone_tg_users MODIFY COLUMN first_name TEXT COLLATE utf8mb4_unicode_ci;
ALTER TABLE voiceClone_tg_users MODIFY COLUMN last_name TEXT COLLATE utf8mb4_unicode_ci;
ALTER TABLE voiceClone_tg_users MODIFY COLUMN username TEXT COLLATE utf8mb4_unicode_ci;
ALTER TABLE voiceClone_tg_users MODIFY COLUMN status TEXT COLLATE utf8mb4_unicode_ci;
ALTER TABLE voiceClone_tg_users MODIFY COLUMN is_bot TINYINT(1) COLLATE utf8mb4_unicode_ci;

/* View to aggregated KPIs related to chat */
drop view vw_user_chat_kpi;
CREATE VIEW vw_user_chat_kpi as
with user_chat_kpi as (with user_msg as (select document_id as col1,DATE_FORMAT(timestamp, "%d %M %Y") as col2, count(message_id) as user_msg_cnt from voiceClone_tg_chats where reachout is null and role = 'user' group by document_id,DATE_FORMAT(timestamp, "%d %M %Y")),
chat_duration as (select document_id as col1, chatdt as col2, sum(duration_in_sec) as chat_duration_in_sec
        from (SELECT document_id, DATE_FORMAT(timestamp, "%d %M %Y") as chatdt, IF(TIMESTAMPDIFF(SECOND, IF(LAG(timestamp, 1,0) OVER (PARTITION BY document_id, DATE_FORMAT(timestamp, "%d %M %Y") ORDER BY timestamp)='01-01-1900',null,LAG(timestamp, 1,0) OVER (PARTITION BY document_id, DATE_FORMAT(timestamp, "%d %M %Y") ORDER BY timestamp)) , timestamp)>1800,null,TIMESTAMPDIFF(SECOND, IF(LAG(timestamp, 1,0) OVER (PARTITION BY document_id, DATE_FORMAT(timestamp, "%d %M %Y") ORDER BY timestamp)='01-01-1900',null,LAG(timestamp, 1,0) OVER (PARTITION BY document_id, DATE_FORMAT(timestamp, "%d %M %Y") ORDER BY timestamp)) , timestamp)) as duration_in_sec
          FROM voiceClone_tg_chats where reachout is null) t1 group by document_id, chatdt)
select distinct c.document_id
, DATE_FORMAT(timestamp, "%d %M %Y") as chat_date
, DATEDIFF(c.timestamp, u.created_on_date) as day_count
, cd.chat_duration_in_sec as duration_in_sec
, um.user_msg_cnt
from voiceClone_tg_chats c
inner join voiceClone_tg_users u on u.document_id = c.document_id
left join user_msg um on um.col1 = c.document_id and um.col2 = DATE_FORMAT(c.timestamp, "%d %M %Y")
left join chat_duration cd on cd.col1 = c.document_id and cd.col2 = DATE_FORMAT(c.timestamp, "%d %M %Y")
where u.is_bot = 'false'
and c.reachout is null)
select distinct u.tg_user_id
, CONCAT(u.first_name, ' ',u.last_name) as user_fullname
, u.username
, u.status as user_status
, u.created_on_date as user_created_on_date
, u.document_id
, ch.character_name
, vw.chat_date
, ifnull(vw.day_count,0) as day_count
, ifnull(vw.duration_in_sec,0) as duration_in_sec
, ifnull(vw.user_msg_cnt,0) as user_msg_cnt
, replace(replace(lower(chat_analysis_tags),'_',' '),', ',',') as chat_analysis_tags
from user_chat_kpi vw
inner join voiceClone_tg_users u on u.document_id = vw.document_id
inner join voiceClone_characters ch on u.char_id = ch.char_id
left join voiceClone_tg_chats c on c.document_id = vw.document_id
left join chat_analysis ca on ca.document_id = c.document_id
where c.reachout is null
and u.is_bot = 0
and u.created_on_date >= '2024-08-15'
and u.tg_user_id not in ('6697940905','7142807432','6733334932')

-- CODE BELOW THIS IS NOT USED
/* Procedure for rpt_user_usage  - V0.1*/
-- DROP PROCEDURE IF EXISTS sp_load_rpt_user_usage;
-- CREATE PROCEDURE sp_load_rpt_user_usage()
-- BEGIN
--     DECLARE v_id VARCHAR(255);
--     DECLARE v_user_created_on_date DATETIME;
--     DECLARE diff_value INT;
--     DECLARE diff_in_days INT;
--     DECLARE temp_date DATE;
--     DECLARE done INT DEFAULT FALSE;

--     DECLARE cur CURSOR FOR 
--         SELECT distinct tg_user_id, user_created_on_date
--         FROM vw_user_chat_kpi;

--     DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;

--     CREATE temporary TABLE IF NOT EXISTS temp_results (
--         tg_user_id VARCHAR(255) COLLATE utf8mb4_unicode_ci,
--         user_created_on_date DATE COLLATE utf8mb4_unicode_ci,
--         chat_date DATE COLLATE utf8mb4_unicode_ci,
--         day_count INT COLLATE utf8mb4_unicode_ci
--     );
--     OPEN cur;
--     read_loop: LOOP
--         FETCH cur INTO v_id, v_user_created_on_date;
--         IF done THEN
--             LEAVE read_loop;
--         END IF;        
--         -- Calculate the difference in days
--         SET diff_in_days = DATEDIFF(CURDATE() - INTERVAL 1 DAY, v_user_created_on_date);
--         -- Iterate from day_val down to 0
--         SET diff_value = diff_in_days;
--         SET temp_date = CURDATE() - INTERVAL 1 DAY;
--         WHILE diff_value >= 0 DO
--             -- Insert the result into the temporary table
--             -- # INSERT INTO temp_results (tg_user_id, user_created_on_date, chat_date, day_val, difference_in_date, difference_value)
--             -- # VALUES (v_id, v_user_created_on_date, temp_date, diff_in_days, temp_date, diff_value);
--             INSERT INTO temp_results (tg_user_id, user_created_on_date, chat_date, day_count)
--             VALUES (v_id, v_user_created_on_date, temp_date, diff_value);
--             SET temp_date = temp_date - INTERVAL 1 DAY;
--             SET diff_value = diff_value - 1;
--         END WHILE;
--     END LOOP;
--     CLOSE cur;

--     -- INSERT INTO rpt_user_usage (tg_user_id, user_created_on_date, chat_date, day_count
--     -- , duration_in_sec, user_msg_cnt)
--     -- select k.tg_user_id,k.user_created_on_date,k.chat_date,k.day_count
--     -- , sum(duration_in_sec) as duration_in_sec, sum(user_msg_cnt) as user_msg_cnt
--     -- from vw_user_chat_kpi k where k.tg_user_id = current_tg_user_id
--     -- group by k.tg_user_id,k.user_created_on_date,k.chat_date,k.day_count
--     -- union
--     -- SELECT r.tg_user_id, r.user_created_on_date, r.chat_date, r.day_count, 0 as duration_in_sec, 0 as user_msg_cnt
--     -- FROM temp_results r
--     -- LEFT JOIN vw_user_chat_kpi k ON r.day_count = k.day_count AND k.tg_user_id = current_tg_user_id
--     -- WHERE r.tg_user_id = current_tg_user_id
--     -- AND k.day_count IS NULL;

--     select * from temp_results;
--     DROP TABLE IF EXISTS temp_results;
-- END;


-- /* SQL for user_usage report */
-- select distinct r.tg_user_id, r.user_created_on_date, r.chat_date, r.day_val, k.day_count
-- , if(r.day_val=k.day_count,r.day_val,null)
-- , if(r.day_val=k.day_count,sum(k.duration_in_sec),0)
-- , if(r.day_val=k.user_msg_cnt,sum(k.duration_in_sec),0)
-- , ifnull(sum(k.duration_in_sec),0)
-- , ifnull(sum(k.user_msg_cnt),0) from rpt_user_usage r
-- left join vw_user_chat_kpi k on k.tg_user_id = r.tg_user_id
-- where k.tg_user_id = '1136386025' 
-- -- and ifnull(k.day_count,r.day_val) = r.day_val
-- group by r.tg_user_id, r.user_created_on_date, r.chat_date, r.day_val, k.day_count
-- order by r.day_val;
