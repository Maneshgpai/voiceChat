
/* DDL for chats table. All the rest of tables are auto created while */
drop table voiceClone_tg_chats;
CREATE TABLE voiceClone_tg_chats (
    document_id varchar(50),
    content nvarchar(1000),
    timestamp datetime,
    role nvarchar(20),
    content_type varchar(10),
    reachout bit,
    response_status varchar(255),
    message_id float,
    update_id float,
);
ALTER TABLE voiceClone_tg_chats
MODIFY COLUMN content VARCHAR(1000) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;


/* View showing all chat & user related details */
drop view vw_user_chat;
CREATE VIEW vw_user_chat as 
select concat(concat(u.first_name,' '),u.last_name) as name, u.username,
u.document_id, u.tg_user_id,c.character_name, u.status,
DATE_FORMAT(u.created_on_date, "%d %M %Y") as created_on,
u.created_on_time,
ch.content, DATE_FORMAT(ch.timestamp, "%d %M %Y") as chat_date
, ch.timestamp as chat_ts, ch.role, ch.content_type, ch.response_status
, ch.message_id
, IF(ch.reachout='true', 1, 0) as reachout
from voiceClone_tg_users u
inner join voiceClone_characters c on u.char_id = c.char_id
inner join voiceClone_tg_chats ch on u.document_id = ch.document_id
where u.is_bot = 'false'


/* View to aggregated KPIs related to chat */
drop view vw_user_chat_kpi;
CREATE VIEW vw_user_chat_kpi as
with user_msg as (select document_id as col1,chat_date as col2, count(message_id) as user_msg_cnt from vw_user_chat where reachout = 0 and role = 'user' group by document_id,chat_date),
chat_duration as (select document_id as col1, chat_date as col2, sum(duration_in_sec) as chat_duration_in_sec 
        from (SELECT document_id, chat_date, IF(TIMESTAMPDIFF(SECOND, IF(LAG(chat_ts, 1,0) OVER (PARTITION BY document_id, chat_date ORDER BY chat_ts)='01-01-1900',null,LAG(chat_ts, 1,0) OVER (PARTITION BY document_id, chat_date ORDER BY chat_ts)) , chat_ts)>1800,null,TIMESTAMPDIFF(SECOND, IF(LAG(chat_ts, 1,0) OVER (PARTITION BY document_id, chat_date ORDER BY chat_ts)='01-01-1900',null,LAG(chat_ts, 1,0) OVER (PARTITION BY document_id, chat_date ORDER BY chat_ts)) , chat_ts)) as duration_in_sec 
          FROM vw_user_chat where reachout = 0) t1 group by document_id, chat_date)
select distinct document_id, chat_date
, TIMESTAMPDIFF(Day, created_on, chat_date) as day_count
, cd.chat_duration_in_sec as duration_in_sec
, um.user_msg_cnt
 from vw_user_chat as vw1
 left join user_msg um on um.col1 = document_id and um.col2 = chat_date
 left join chat_duration cd on cd.col1 = document_id and cd.col2 = chat_date
where reachout = 0



/* SQL to analyze chat content */
select * from vw_user_chat
where reachout = 0
and document_id = '1005738469_bPm741abegxqm3t7rfeB'
and chat_date = '22-Aug-24';

--NOT NEEDED Query to get time spent in chatting
select document_id as col1, chat_date as col2, sum(duration_in_sec) as chat_duration_in_sec 
from (SELECT document_id, chat_date
  --Column to calculate difference between current value and previous value of chat_ts. Logic added to use NULL for the very first value, when there is previous value for that group. Also don't consider the time interval if there is a gap of more 30min between chats.
  , IF(DATEDIFF(SECOND, IF(LAG(chat_ts, 1,0) OVER (PARTITION BY document_id, chat_date ORDER BY chat_ts)='01-01-1900',null,LAG(chat_ts, 1,0) OVER (PARTITION BY document_id, chat_date ORDER BY chat_ts)) , chat_ts)>1800,null,DATEDIFF(SECOND, IF(LAG(chat_ts, 1,0) OVER (PARTITION BY document_id, chat_date ORDER BY chat_ts)='01-01-1900',null,LAG(chat_ts, 1,0) OVER (PARTITION BY document_id, chat_date ORDER BY chat_ts)) , chat_ts)) as duration_in_sec 
  FROM vw_user_chat where reachout = 0 
and document_id = '1005738469_bPm741abegxqm3t7rfeB'
and chat_date = '22-Aug-24') t1 group by document_id, chat_date;


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