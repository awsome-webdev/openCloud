import json
import os
from flask import Flask, request, jsonify
from pywebpush import webpush, WebPushException
from flask_cors import CORS
import logging as log
app = Flask(__name__)
CORS(app)
SUBSCRIPTIONS_FILE = "/home/awsome-webdev/push-not/subscriptions.json"
log.basicConfig(level=log.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s', filename='app.log')
VAPID_PRIVATE_KEY = "GbzP3OyCfdPJeoH-rSvZJCLFmgE_DBrmResPlRaRKNc"
VAPID_PUBLIC_KEY = "BA3eAq3SaAlTG9RtMoZUpIGrJS2cFrb3tyqrNxZy3opAmefJVLzOzCydxwp1rTXn5yuUDqZRRtw6LQlEOFn2mOI"
app.logger.info(f"Starting push-not")
# Load subscriptions from file (or empty dict if not exist)
def load_subscriptions():
    if os.path.exists(SUBSCRIPTIONS_FILE):
        with open(SUBSCRIPTIONS_FILE, "r") as f:
            return json.load(f)
    return {}

# Save subscriptions to file
def save_subscriptions(subscriptions):
    with open(SUBSCRIPTIONS_FILE, "w") as f:
        json.dump(subscriptions, f, indent=2)

user_subscriptions = load_subscriptions()

@app.route("/subscribe/<username>", methods=["POST"])
def subscribe(username):
    subscription = request.get_json()
    user_subscriptions[username] = subscription
    save_subscriptions(user_subscriptions)
    return jsonify({"success": True}), 201
    app.logger.info(f"User {username} subscribed")
    

@app.route("/notify/<username>", methods=["POST"])
def notify(username):
    json = request.json
    message = json['message']
    app.logger.info(f"Message received: {message}")
    subscription = user_subscriptions.get(username)
    if not subscription:
        app.logger.warning(f"User {username} not subscribed")
        return jsonify({"error": "User not subscribed"}), 404
    try:
        webpush(
            subscription_info=subscription,
            data=message,
            vapid_private_key=VAPID_PRIVATE_KEY,
            vapid_claims={"sub": "mailto:admin@yourdomain.com"},
            ttl=60,  # Time-to-Live in seconds (e.g., 60 seconds)
            headers={"Urgency": "high"}  # Set urgency to high
        )
        app.logger.info(f"Notification sent to {username} with high urgency")
        return jsonify({"success": True})
    except WebPushException as ex:
        app.logger.error(f"Failed to send notification to {username}: {str(ex)}")
        return jsonify({"error": str(ex)}), 500

@app.route("/public_key", methods=["GET"])
def public_key():
    return jsonify({"vapidPublicKey": VAPID_PUBLIC_KEY})

if __name__ == "__main__":
    app.run(debug=True, port="38677")
