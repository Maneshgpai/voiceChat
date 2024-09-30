<?php
include 'connection.php';
include (__DIR__ . '/vendor/autoload.php');
include 'Telegram.php';
function telegramWebhook($request) {
    $telegram = new Telegram('7215162784:AAG_xiYIyEaWW9sLXaXmGdyrj8JbQmPs6YY');
    $result = $telegram->getData();
    error_log("Telegram In Bound : " . json_encode($result));
    $msg = "";
    $from_id = $telegram->UserID() ?: "";
    $text = $telegram->Text() ?: "";
    $chat_id = $telegram->ChatID() ?: "";
    $update_type = $telegram->getUpdateType() ?: "";
    $msg_id = $telegram->MessageID() ?: "";
    if ($text == '/start') {
        $reply = 'Welcome to the Test Payment Bot, for payment click on the below button';
        $orderId = 'orderId_' . time() . bin2hex(random_bytes(2));
        $link = 'http://' . $_SERVER['HTTP_HOST'] . '/pay-now.php?id=' . $chat_id . '&orderId=' . $orderId;
        updateOrCreate($chat_id, $from_id, $link, $orderId);
        $content = array('chat_id' => $chat_id, 'text' => $reply, 'parse_mode' => 'HTML');
        $option = array(
            array($telegram->buildInlineKeyBoardButton("Pay Now", $link))
        );
        $keyb = $telegram->buildInlineKeyBoard($option);
        $content['reply_markup'] = $keyb;
        $response = $telegram->sendMessage($content);
        error_log("Telegram Out Bound : " . json_encode($response, JSON_PRETTY_PRINT));

        return $response;
    } else {
        return json_encode(['ok' => false, 'description' => 'invalid command']);
    }
}

function updateOrCreate($chat_id, $user_id, $pay_link, $order_id) {
    $stmt = $conn->prepare("INSERT INTO dump (chat_id, user_id, pay_link, order_id) VALUES (?, ?, ?, ?) ON DUPLICATE KEY UPDATE user_id = ?, pay_link = ?, order_id = ?");
    $stmt->bind_param("sssssss", $chat_id, $user_id, $pay_link, $order_id, $user_id, $pay_link, $order_id);
    if ($stmt->execute()) {
        error_log("Record updated or created successfully");
    } else {
        error_log("Error: " . $stmt->error);
    }
    $stmt->close();
}
