<?php
/**
 * Plugin Name: ThaiLawOnline Chatbot Connector
 * Description: Connects the WordPress chat widget to the ThaiLawOnline LLM Council chatbot API.
 * Version: 1.0.0
 * Author: ThaiLawOnline
 * Text Domain: thailaw-chatbot
 */

if (!defined('ABSPATH')) {
    exit;
}

// ============================================================
// Configuration
// ============================================================

// API endpoint — localhost because the backend runs on the same server
define('THAILAW_CHATBOT_API_URL', 'http://127.0.0.1:8001/api/chat');

// API key — stored server-side, never exposed to the browser
define('THAILAW_CHATBOT_API_KEY', defined('THAILAW_API_KEY')
    ? THAILAW_API_KEY
    : get_option('thailaw_chatbot_api_key', '')
);

// ============================================================
// Enqueue frontend JS
// ============================================================

add_action('wp_enqueue_scripts', function () {
    wp_enqueue_script(
        'thailaw-chatbot',
        plugin_dir_url(__FILE__) . 'chatbot-connector.js',
        [],
        '1.0.0',
        true // Load in footer
    );

    // Pass AJAX URL and nonce to the frontend
    wp_localize_script('thailaw-chatbot', 'ThaiLawChatbot', [
        'ajaxUrl' => admin_url('admin-ajax.php'),
        'nonce'   => wp_create_nonce('thailaw_chatbot_nonce'),
    ]);
});

// ============================================================
// AJAX handler — proxy to the FastAPI backend
// ============================================================

add_action('wp_ajax_thailaw_chat', 'thailaw_chatbot_handle_message');
add_action('wp_ajax_nopriv_thailaw_chat', 'thailaw_chatbot_handle_message');

function thailaw_chatbot_handle_message() {
    // Verify nonce
    if (!check_ajax_referer('thailaw_chatbot_nonce', 'nonce', false)) {
        wp_send_json_error(['message' => 'Invalid security token'], 403);
    }

    // Get message from POST data
    $message = isset($_POST['message']) ? sanitize_text_field(wp_unslash($_POST['message'])) : '';
    $session_id = isset($_POST['session_id']) ? sanitize_text_field(wp_unslash($_POST['session_id'])) : '';

    if (empty($message)) {
        wp_send_json_error(['message' => 'Message is required'], 400);
    }

    // Call the FastAPI backend
    $response = wp_remote_post(THAILAW_CHATBOT_API_URL, [
        'timeout' => 120, // Council process can take time
        'headers' => [
            'Content-Type' => 'application/json',
            'X-API-Key'    => THAILAW_CHATBOT_API_KEY,
        ],
        'body' => wp_json_encode([
            'message'    => $message,
            'session_id' => $session_id,
        ]),
    ]);

    // Handle errors
    if (is_wp_error($response)) {
        wp_send_json_error([
            'message' => 'Failed to connect to the chatbot service. Please try again.',
        ], 502);
    }

    $status_code = wp_remote_retrieve_response_code($response);
    $body = wp_remote_retrieve_body($response);
    $data = json_decode($body, true);

    if ($status_code !== 200) {
        $error_msg = isset($data['detail']) ? $data['detail'] : 'An error occurred';
        wp_send_json_error(['message' => $error_msg], $status_code);
    }

    // Return the chatbot response to the frontend
    wp_send_json_success($data);
}

// ============================================================
// Admin settings page
// ============================================================

add_action('admin_menu', function () {
    add_options_page(
        'ThaiLaw Chatbot Settings',
        'ThaiLaw Chatbot',
        'manage_options',
        'thailaw-chatbot',
        'thailaw_chatbot_settings_page'
    );
});

function thailaw_chatbot_settings_page() {
    if (isset($_POST['thailaw_chatbot_api_key']) && check_admin_referer('thailaw_chatbot_settings')) {
        update_option('thailaw_chatbot_api_key', sanitize_text_field(wp_unslash($_POST['thailaw_chatbot_api_key'])));
        echo '<div class="updated"><p>Settings saved.</p></div>';
    }

    $api_key = get_option('thailaw_chatbot_api_key', '');
    ?>
    <div class="wrap">
        <h1>ThaiLaw Chatbot Settings</h1>
        <form method="post">
            <?php wp_nonce_field('thailaw_chatbot_settings'); ?>
            <table class="form-table">
                <tr>
                    <th scope="row"><label for="thailaw_chatbot_api_key">API Key</label></th>
                    <td>
                        <input type="password" name="thailaw_chatbot_api_key" id="thailaw_chatbot_api_key"
                               value="<?php echo esc_attr($api_key); ?>" class="regular-text" />
                        <p class="description">
                            The API key used to authenticate with the chatbot backend.
                            This should match the WP_API_KEY in the backend's .env file.
                        </p>
                    </td>
                </tr>
            </table>
            <?php submit_button('Save Settings'); ?>
        </form>
    </div>
    <?php
}
