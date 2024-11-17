from flask import Flask, request, jsonify, render_template
from werkzeug.middleware.proxy_fix import ProxyFix
import requests
import base64
from urllib.parse import urlparse, parse_qs
import time

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1)

@app.route('/')
def home():
    return jsonify({'server': 'https://discord.gg/6rDr2tPubr',})

def sleep(seconds):
    time.sleep(seconds)

def format_number(number):
    return "{:,}".format(number)

def get_turnstile_response():
    return "mock_turnstile_response"

def delta(id):
    try:
        response = requests.get(f"https://api-gateway.platoboost.com/v1/authenticators/8/{id}")
        response.raise_for_status()
        already_pass = response.json()

        if 'key' in already_pass:
            return {
                    "Status": "Success",
                    "key": already_pass["key"],
                }

        captcha = already_pass.get('captcha', '')
        post_response = requests.post(
            f"https://api-gateway.platoboost.com/v1/sessions/auth/8/{id}",
            json={
                "captcha": get_turnstile_response() if captcha else "",
                "type": "Turnstile" if captcha else "",
            }
        )
        post_response.raise_for_status()
        loot_link = post_response.json()

        sleep(2)
        decode_lootlink = requests.utils.unquote(loot_link['redirect'])
        r = urlparse(decode_lootlink).query
        r = parse_qs(r).get("r", [""])[0]
        decode_base64 = base64.b64decode(r).decode()
        tk = urlparse(decode_base64).query
        tk = parse_qs(tk).get("tk", [""])[0]
        sleep(5)
        
        final_response = requests.put(
            f"https://api-gateway.platoboost.com/v1/sessions/auth/8/{id}/{tk}"
        )

        if final_response.text.strip() == "":
            return {
                "Status": "Failed",
                "message": "No key found. Please check the URL or try again later."
            }
        
        try:
            response = requests.get(f"https://api-gateway.platoboost.com/v1/authenticators/8/{id}")
            response.raise_for_status()
            already_pass = response.json()

            if 'key' in already_pass:
                    return {
                    "Status": "Success",
                    "key": already_pass["key"],
                }
            
            else:
                 return ({"status": "error",  
                            "message": "Try Again!"})
        except ValueError:
            return ({"status": "error",  
                            "message": "Try Again!"}), 404
        
    except requests.RequestException:
        return ({"status": "error",  
                        "message": "Try Again!"}), 404

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/delta', methods=['GET'])
def get_id():
    url = request.args.get('url')
    if not url:
        return jsonify({"message": "Url is required"}), 400

    try:
        result = delta(parse_qs(urlparse(url).query).get("id", [""])[0])
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': 'An unexpected error occurred'}), 500

if __name__ == '__main__':
    app.run(debug=True)
