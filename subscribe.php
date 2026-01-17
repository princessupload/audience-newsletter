<?php
/**
 * Newsletter Subscription Handler
 * Handles subscribe/unsubscribe requests for the lottery newsletter
 * 
 * Deploy to: princessupload.net/subscribe.php
 */

header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST, GET');
header('Access-Control-Allow-Headers: Content-Type');

// File paths (relative to web root)
$subscribers_file = __DIR__ . '/data/subscribers.txt';
$unsubscribed_file = __DIR__ . '/data/unsubscribed.txt';

// Ensure data directory exists
if (!file_exists(__DIR__ . '/data')) {
    mkdir(__DIR__ . '/data', 0755, true);
}

// Get action from request
$action = isset($_GET['action']) ? $_GET['action'] : (isset($_POST['action']) ? $_POST['action'] : '');
$email = isset($_GET['email']) ? $_GET['email'] : (isset($_POST['email']) ? $_POST['email'] : '');

// Validate email
function is_valid_email($email) {
    return filter_var($email, FILTER_VALIDATE_EMAIL) !== false;
}

// Load emails from file
function load_emails($file) {
    if (!file_exists($file)) return [];
    $emails = [];
    foreach (file($file, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES) as $line) {
        $line = trim(strtolower($line));
        if ($line && strpos($line, '@') !== false && $line[0] !== '#') {
            $emails[] = $line;
        }
    }
    return array_unique($emails);
}

// Save email to file
function add_email($file, $email) {
    $email = strtolower(trim($email));
    $emails = load_emails($file);
    if (!in_array($email, $emails)) {
        file_put_contents($file, $email . "\n", FILE_APPEND | LOCK_EX);
        return true;
    }
    return false;
}

// Remove email from file
function remove_email($file, $email) {
    $email = strtolower(trim($email));
    $emails = load_emails($file);
    $new_emails = array_filter($emails, function($e) use ($email) {
        return $e !== $email;
    });
    file_put_contents($file, implode("\n", $new_emails) . "\n", LOCK_EX);
    return count($emails) !== count($new_emails);
}

// Generate unsubscribe token (simple hash)
function get_unsub_token($email) {
    return substr(md5($email . 'lottery_unsub_2026'), 0, 16);
}

// Handle actions
switch ($action) {
    case 'subscribe':
        if (!$email || !is_valid_email($email)) {
            echo json_encode(['success' => false, 'message' => 'Please enter a valid email address.']);
            exit;
        }
        
        $email = strtolower(trim($email));
        
        // Check if unsubscribed before
        $unsubscribed = load_emails($unsubscribed_file);
        if (in_array($email, $unsubscribed)) {
            // Remove from unsubscribed list
            remove_email($unsubscribed_file, $email);
        }
        
        // Check if already subscribed
        $subscribers = load_emails($subscribers_file);
        if (in_array($email, $subscribers)) {
            echo json_encode(['success' => true, 'message' => 'You\'re already subscribed! 🎉']);
            exit;
        }
        
        // Add to subscribers
        add_email($subscribers_file, $email);
        echo json_encode([
            'success' => true, 
            'message' => 'Welcome! 🎉 You\'ll receive the lottery newsletter daily at noon CT.'
        ]);
        break;
        
    case 'unsubscribe':
        if (!$email || !is_valid_email($email)) {
            echo json_encode(['success' => false, 'message' => 'Invalid email address.']);
            exit;
        }
        
        $email = strtolower(trim($email));
        $token = isset($_GET['token']) ? $_GET['token'] : (isset($_POST['token']) ? $_POST['token'] : '');
        
        // Verify token for security
        if ($token && $token !== get_unsub_token($email)) {
            echo json_encode(['success' => false, 'message' => 'Invalid unsubscribe link.']);
            exit;
        }
        
        // Remove from subscribers
        remove_email($subscribers_file, $email);
        
        // Add to unsubscribed list
        add_email($unsubscribed_file, $email);
        
        echo json_encode([
            'success' => true, 
            'message' => 'You\'ve been unsubscribed. Sorry to see you go! 💔'
        ]);
        break;
        
    case 'status':
        if (!$email || !is_valid_email($email)) {
            echo json_encode(['subscribed' => false]);
            exit;
        }
        
        $email = strtolower(trim($email));
        $subscribers = load_emails($subscribers_file);
        echo json_encode(['subscribed' => in_array($email, $subscribers)]);
        break;
        
    case 'count':
        // Public subscriber count
        $subscribers = load_emails($subscribers_file);
        echo json_encode(['count' => count($subscribers)]);
        break;
    
    case 'list':
        // Protected list action - requires secret key
        $key = isset($_GET['key']) ? $_GET['key'] : (isset($_POST['key']) ? $_POST['key'] : '');
        $secret_key = getenv('SUBSCRIBER_KEY') ?: 'lottery_newsletter_2026_secret';
        
        if ($key !== $secret_key) {
            echo json_encode(['success' => false, 'message' => 'Unauthorized']);
            exit;
        }
        
        $subscribers = load_emails($subscribers_file);
        echo json_encode(['success' => true, 'subscribers' => $subscribers]);
        break;
        
    default:
        // Show simple HTML form for direct access
        header('Content-Type: text/html');
        $unsub_email = isset($_GET['email']) ? htmlspecialchars($_GET['email']) : '';
        $unsub_token = isset($_GET['token']) ? htmlspecialchars($_GET['token']) : '';
        
        if ($unsub_email && $unsub_token) {
            // Unsubscribe confirmation page
            echo '<!DOCTYPE html>
<html>
<head>
    <title>Unsubscribe - Lottery Newsletter</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: -apple-system, sans-serif; max-width: 500px; margin: 50px auto; padding: 20px; text-align: center; }
        .btn { background: #ff47bb; color: white; padding: 15px 30px; border: none; border-radius: 8px; font-size: 16px; cursor: pointer; }
        .btn:hover { background: #e03aa6; }
        .btn-cancel { background: #666; margin-left: 10px; }
    </style>
</head>
<body>
    <h1>😢 Unsubscribe</h1>
    <p>Are you sure you want to unsubscribe <strong>' . $unsub_email . '</strong> from the Lottery Newsletter?</p>
    <form method="post" action="subscribe.php">
        <input type="hidden" name="action" value="unsubscribe">
        <input type="hidden" name="email" value="' . $unsub_email . '">
        <input type="hidden" name="token" value="' . $unsub_token . '">
        <button type="submit" class="btn">Yes, Unsubscribe</button>
        <a href="lottery-newsletter.html" class="btn btn-cancel" style="text-decoration:none; display:inline-block;">Cancel</a>
    </form>
</body>
</html>';
        } else {
            // Default subscribe page
            echo '<!DOCTYPE html>
<html>
<head>
    <title>Subscribe - Lottery Newsletter</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: -apple-system, sans-serif; max-width: 500px; margin: 50px auto; padding: 20px; text-align: center; background: linear-gradient(135deg, #fff0f5 0%, #ffe4ec 100%); min-height: 100vh; }
        h1 { color: #ff47bb; }
        input[type="email"] { width: 100%; padding: 15px; font-size: 16px; border: 2px solid #ff47bb; border-radius: 8px; margin: 10px 0; box-sizing: border-box; }
        .btn { background: #ff47bb; color: white; padding: 15px 30px; border: none; border-radius: 8px; font-size: 16px; cursor: pointer; width: 100%; }
        .btn:hover { background: #e03aa6; }
        .message { padding: 15px; border-radius: 8px; margin: 15px 0; }
        .success { background: #d4edda; color: #155724; }
        .error { background: #f8d7da; color: #721c24; }
    </style>
</head>
<body>
    <h1>🎰 Lottery Newsletter</h1>
    <p>Get daily lottery analysis delivered to your inbox at noon CT!</p>
    <form method="post" action="subscribe.php" id="subForm">
        <input type="hidden" name="action" value="subscribe">
        <input type="email" name="email" placeholder="Enter your email" required>
        <button type="submit" class="btn">Subscribe 💖</button>
    </form>
    <p style="margin-top: 30px;"><a href="lottery-newsletter.html">← Back to Newsletter</a></p>
</body>
</html>';
        }
        break;
}
?>
