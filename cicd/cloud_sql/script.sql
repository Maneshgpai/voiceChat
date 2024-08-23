
/* View showing all chat & user related details */
drop view vw_user_chat;
CREATE VIEW vw_user_chat as 
select concat(concat(u.first_name,' '),u.last_name) as name, u.username,
u.document_id, u.tg_user_id,c.character_name, u.status,
FORMAT(u.created_on_date, 'dd-MMM-yy') as created_on,
u.created_on_time,
ch.content, FORMAT(ch.timestamp, 'dd-MMM-yy') as chat_date, ch.timestamp as chat_ts, ch.role, ch.content_type, ch.response_status, ch.message_id, IIF(ch.reachout='true', 1, 0) as reachout
from voiceClone_tg_users u
inner join voiceClone_characters c on u.char_id = c.char_id
inner join voiceClone_tg_chats ch on u.document_id = ch.document_id
where u.is_bot = 'false'

/* View to aggregated KPIs related to chat */
drop view vw_user_chat_kpi;
CREATE VIEW vw_user_chat_kpi as 
with user_msg as (select document_id as col1,chat_date as col2, count(message_id) as user_msg_cnt from vw_user_chat where reachout = 0 and role = 'user' group by document_id,chat_date)
select document_id, chat_date, DATEDIFF(Day, created_on, chat_date) as #_day, DATEDIFF(MINUTE, min(chat_ts) , max(chat_ts)) as chat_duration_in_min,um.user_msg_cnt
 from vw_user_chat as vw1
 left join user_msg um on um.col1 = document_id and um.col2 = chat_date
where reachout = 0
group by document_id, chat_date, DATEDIFF(Day, created_on, chat_date), um.user_msg_cnt
