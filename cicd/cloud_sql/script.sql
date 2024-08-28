
/* DDL for chats table. All the rest of tables are auto created while */
drop table voiceClone_tg_chats;
CREATE TABLE voiceClone_tg_chats (
    document_id varchar(50)  COLLATE utf8mb4_unicode_ci,
    content nvarchar(1000),
    timestamp datetime,
    role nvarchar(20) COLLATE utf8mb4_unicode_ci,
    content_type varchar(10) COLLATE utf8mb4_unicode_ci,
    reachout varchar(10) COLLATE utf8mb4_unicode_ci,
    response_status varchar(255) COLLATE utf8mb4_unicode_ci,
    message_id float,
    update_id float,
    data_loaded_on datetime
);
ALTER TABLE voiceClone_tg_chats
MODIFY COLUMN content VARCHAR(1000) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

ALTER TABLE voiceClone_tg_users MODIFY COLUMN document_id TEXT COLLATE utf8mb4_unicode_ci;
ALTER TABLE voiceClone_tg_users MODIFY COLUMN tg_user_id TEXT COLLATE utf8mb4_unicode_ci;
ALTER TABLE voiceClone_tg_users MODIFY COLUMN char_id TEXT COLLATE utf8mb4_unicode_ci;
ALTER TABLE voiceClone_tg_users MODIFY COLUMN first_name TEXT COLLATE utf8mb4_unicode_ci;
ALTER TABLE voiceClone_tg_users MODIFY COLUMN last_name TEXT COLLATE utf8mb4_unicode_ci;
ALTER TABLE voiceClone_tg_users MODIFY COLUMN username TEXT COLLATE utf8mb4_unicode_ci;
ALTER TABLE voiceClone_tg_users MODIFY COLUMN status TEXT COLLATE utf8mb4_unicode_ci;
ALTER TABLE voiceClone_tg_users MODIFY COLUMN is_bot TINYINT(1) COLLATE utf8mb4_unicode_ci;

ALTER TABLE chat_analysis MODIFY COLUMN document_id VARCHAR(50) COLLATE utf8mb4_unicode_ci;
ALTER TABLE chat_analysis MODIFY COLUMN chat_analysis_tags VARCHAR(1000) COLLATE utf8mb4_unicode_ci;
ALTER TABLE chat_analysis MODIFY COLUMN data_loaded_on datetime COLLATE utf8mb4_unicode_ci;

ALTER TABLE voiceClone_characters MODIFY COLUMN char_id VARCHAR(50) COLLATE utf8mb4_unicode_ci;
ALTER TABLE voiceClone_characters MODIFY COLUMN character_name VARCHAR(50) COLLATE utf8mb4_unicode_ci;

ALTER TABLE voiceClone_tg_chats MODIFY COLUMN document_id VARCHAR(50) COLLATE utf8mb4_unicode_ci;
ALTER TABLE voiceClone_tg_chats MODIFY COLUMN role VARCHAR(20) COLLATE utf8mb4_unicode_ci;
ALTER TABLE voiceClone_tg_chats MODIFY COLUMN content_type VARCHAR(10) COLLATE utf8mb4_unicode_ci;
ALTER TABLE voiceClone_tg_chats MODIFY COLUMN reachout VARCHAR(10) COLLATE utf8mb4_unicode_ci;
ALTER TABLE voiceClone_tg_chats MODIFY COLUMN response_status VARCHAR(255) COLLATE utf8mb4_unicode_ci;

ALTER TABLE chat_analysis_pivot MODIFY COLUMN document_id VARCHAR(50) COLLATE utf8mb4_unicode_ci;
ALTER TABLE chat_analysis_pivot MODIFY COLUMN tag_key text COLLATE utf8mb4_unicode_ci;


-
/* View showing all chat & user related details */
-- drop view vw_user_chat;
-- CREATE VIEW vw_user_chat as 
-- select concat(concat(u.first_name,' '),u.last_name) as name, u.username,
-- u.document_id, u.tg_user_id,c.character_name, u.status,
-- DATE_FORMAT(u.created_on_date, "%d %M %Y") as created_on,
-- u.created_on_time,
-- ch.content, DATE_FORMAT(ch.timestamp, "%d %M %Y") as chat_date
-- , ch.timestamp as chat_ts, ch.role, ch.content_type, ch.response_status
-- , ch.message_id
-- , IF(ch.reachout='1', TRUE, FALSE) as reachout
-- from voiceClone_tg_users u
-- inner join voiceClone_characters c on u.char_id = c.char_id
-- inner join voiceClone_tg_chats ch on u.document_id = ch.document_id
-- where u.is_bot = 'false'


/* View to aggregated KPIs related to chat */
drop view vw_user_chat_kpi;
CREATE VIEW vw_user_chat_kpi as
with user_msg as (select document_id as col1,DATE_FORMAT(timestamp, "%d %M %Y") as col2, count(message_id) as user_msg_cnt from voiceClone_tg_chats where reachout is null and role = 'user' group by document_id,DATE_FORMAT(timestamp, "%d %M %Y")),
chat_duration as (select document_id as col1, chatdt as col2, sum(duration_in_sec) as chat_duration_in_sec 
        from (SELECT document_id, DATE_FORMAT(timestamp, "%d %M %Y") as chatdt, IF(TIMESTAMPDIFF(SECOND, IF(LAG(timestamp, 1,0) OVER (PARTITION BY document_id, DATE_FORMAT(timestamp, "%d %M %Y") ORDER BY timestamp)='01-01-1900',null,LAG(timestamp, 1,0) OVER (PARTITION BY document_id, DATE_FORMAT(timestamp, "%d %M %Y") ORDER BY timestamp)) , timestamp)>1800,null,TIMESTAMPDIFF(SECOND, IF(LAG(timestamp, 1,0) OVER (PARTITION BY document_id, DATE_FORMAT(timestamp, "%d %M %Y") ORDER BY timestamp)='01-01-1900',null,LAG(timestamp, 1,0) OVER (PARTITION BY document_id, DATE_FORMAT(timestamp, "%d %M %Y") ORDER BY timestamp)) , timestamp)) as duration_in_sec 
          FROM voiceClone_tg_chats where reachout is null) t1 group by document_id, chatdt)
select distinct c.document_id
, DATE_FORMAT(c.timestamp, "%d %M %Y") as chat_date
, DATEDIFF(c.timestamp, u.created_on_date) as day_count
, cd.chat_duration_in_sec as duration_in_sec
, um.user_msg_cnt
from voiceClone_tg_chats c
inner join voiceClone_tg_users u on u.document_id = c.document_id
left join user_msg um on um.col1 = c.document_id and um.col2 = DATE_FORMAT(c.timestamp, "%d %M %Y")
left join chat_duration cd on cd.col1 = c.document_id and cd.col2 = DATE_FORMAT(c.timestamp, "%d %M %Y")
where u.is_bot = 'false'
and c.reachout is null


/* SQL to analyze chat content */

select distinct user_msg_cnt from (
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
, ca.chat_analysis_tags
from user_chat_kpi vw
inner join voiceClone_tg_users u on u.document_id = vw.document_id
inner join voiceClone_characters ch on u.char_id = ch.char_id 
left join voiceClone_tg_chats c on c.document_id = vw.document_id
left join chat_analysis ca on ca.document_id = c.document_id
where c.reachout is null
and u.is_bot = 0
and u.created_on_date >= '2024-08-15'
and u.tg_user_id not in ('6697940905','7142807432','6733334932')) t1 order by 1 asc


select distinct chat_tags from chat_tag_lookup


-- Chat KPIs
-- What are people chatting about? Summarized, cateogrized & tagged
-- what all are people requesting? requests for pic/ video/ content - Insta, FB, etc/ conversation/ anything else
-- Are people sharing personal info. If so, what all?
-- Are people getting frustrated with these issues? - Chat content analysis
-- Are people getting bored with chats? - Chat content analysis
-- How many chats happening every sec/min/hr
-- Peak chatting time
-- Chat quality - how many errors/ junk response/ no reply/ any other issue?
-- Chat quality - how is response time/qualiy when render goes down?

-- User KPIs
-- How many users get added every day?
-- How many users drop off every day?
-- When are people getting mostly added?
-- Why are people dropping off?
-- Which characters are most people talking?
-- Why are people talking most to few characters? - Chat content analysis
-- Repeat / return user list
-- Heavy user list
-- Voice vs Text KPIs

-- Reachout effectiveness

-- System going down : How many times, what happens when this goes down

-- Cost: OpenAI, Render, GCP, Replicate, Elevenlabs, 