<?php
session_start();
include 'connection.php';
function paymentConfig($type) {
    return (object)[
        'mode' => 'sandbox', // or 'production'
        'client_id' => 'TEST102831763629cf6f67f0ecafb28e67138201',
        'secret_key' => 'cfsk_ma_test_138893b3afbcd5632185a659a18fa07e_33609f7b'
    ];
}
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $pay_amount = isset($_POST['pay_amount']) ? $_POST['pay_amount'] : null;
    $customer_name = isset($_POST['customer_name']) ? $_POST['customer_name'] : null;
    $customer_mobile = isset($_POST['customer_mobile']) ? $_POST['customer_mobile'] : null;
    $order_id = isset($_POST['order_id']) ? $_POST['order_id'] : null;

    if (empty($pay_amount) || empty($customer_name) || empty($customer_mobile)) {
        echo json_encode(['message' => 'All fields are required', 'status' => 400]);
        exit;
    }
    $stmt = $conn->prepare("SELECT chat_id FROM dump WHERE order_id = ?");
    $stmt->bind_param("s", $order_id);
    $stmt->execute();
    $result = $stmt->get_result();
    if ($result->num_rows === 0) {
        echo json_encode(['message' => 'Invalid order id', 'status' => 400]);
        exit;
    }
    $dump = $result->fetch_assoc();
    $chat_id = $dump['chat_id'];
    $config = paymentConfig('cashfree');
    $url = $config->mode === 'production' ? 'https://api.cashfree.com/pg/orders' : 'https://sandbox.cashfree.com/pg/orders';
    $postData = [
        'order_id' => (string)$order_id,
        'order_amount' => $pay_amount,
        'order_currency' => 'INR',
        'customer_details' => [
            'customer_id' => $chat_id,
            'customer_name' => $customer_name,
            'customer_phone' => $customer_mobile,
        ],
        'order_meta' => [
            'return_url' => 'https://yourwebsite.com/verify_cf_payment.php?order_id=' . $order_id,
        ],
    ];
    $ch = curl_init($url);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_HTTPHEADER, [
        'Content-Type: application/json',
        'x-api-version: 2023-08-01',
        'x-client-id: ' . $config->client_id,
        'x-client-secret: ' . $config->secret_key,
    ]);
    curl_setopt($ch, CURLOPT_POST, true);
    curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($postData));
    $response = curl_exec($ch);
    curl_close($ch);
    $response = json_decode($response, true);
    if (isset($response['order_status']) && $response['order_status'] == 'ACTIVE') {
        echo json_encode($response);
    } else {
        echo json_encode(['message' => $response['message'] ?? 'Payment partner server error, please try again later.', 'status' => 400]);
    }
    exit;
}
?>
<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Payment</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet"
          integrity="sha384-QWTKZyjpPEjISv5WaRU9OFeRpok6YctnYmDr5pNlyT2bRjXh0JMhjY6hW+ALEwIH" crossorigin="anonymous">
</head>
<body>
<h1 class="text-center">Enter Details</h1>
<div class="container w-75 mx-auto">
    <form id="PaymentForm" method="post">
        <div class="mb-3">
            <label for="customer_name" class="form-label">Customer Name</label>
            <input type="text" class="form-control" name="customer_name" id="customer_name">
        </div>
        <div class="mb-3">
            <label for="customer_mobile" class="form-label">Customer Mobile</label>
            <input type="number" class="form-control" name="customer_mobile" id="customer_mobile">
        </div>
        <div class="mb-3">
            <label for="pay_amount" class="form-label">Amount</label>
            <input type="number" class="form-control" name="pay_amount" id="pay_amount">
        </div>
        <input type="hidden" name="order_id" value="<?php echo htmlspecialchars($_GET['order_id']); ?>">
        <button type="submit" class="btn btn-primary">Submit</button>
    </form>
</div>
<script src="https://code.jquery.com/jquery-3.5.1.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"
        integrity="sha384-YvpcrYf0tY3lHB60NNkmXc5s9fDVZLESaAA55NDzOxhy9GkcIdslK1eN7N6jIeHz"
        crossorigin="anonymous"></script>
<script src="https://sdk.cashfree.com/js/v3/cashfree.js"></script>
<script src="https://cdn.jsdelivr.net/npm/sweetalert2@11"></script>
<script>
    $('#PaymentForm').on('submit', function (event) {
        event.preventDefault();
        let formData = new FormData(this);
        const object = {};
        formData.forEach((value, key) => object[key] = value);
        const json = JSON.stringify(object);
        $.ajax({
            type: 'POST',
            url: 'payment.php',
            contentType: 'application/json',
            data: json,
            processData: false,
            success: function (response) {
                if (response.order_status === 'ACTIVE') {
                    const cashfree = Cashfree({
                        mode: "<?php echo $config->mode; ?>",
                    });
                    let checkoutOptions = {
                        paymentSessionId: response.payment_session_id,
                        redirectTarget: "_modal",
                    };
                    cashfree.checkout(checkoutOptions).then((result) => {
                        if (result.error) {
                            console.log("Payment error:", result.error);
                        } else if (result.paymentDetails) {
                            Swal.fire({
                                title: 'Success',
                                text: result.paymentDetails.paymentMessage,
                                icon: 'success',
                            });
                        }
                    });
                } else {
                    Swal.fire({
                        title: 'Error',
                        text: response.message,
                        icon: 'error',
                    });
                }
            },
            error: function (xhr) {
                const response = JSON.parse(xhr.responseText);
                Swal.fire({
                    title: 'Error',
                    text: response.message,
                    icon: 'error',
                });
            }
        });
    });
</script>
</body>
</html>
