from flask import Flask, request, jsonify
import redis # type: ignore
import imagehash # type: ignore
from PIL import Image
import requests
from io import BytesIO
from flask_cors import CORS # type: ignore

app = Flask(__name__)
CORS(app)
r = redis.Redis(host='redis', port=6379, decode_responses=True)

@app.route("/check")
def check_image():
    image_url = request.args.get("url")
    if not image_url:
        return jsonify({"error": "No URL provided"}), 400

    try:
        response = requests.get(image_url, timeout=5)
        image = Image.open(BytesIO(response.content)).convert("RGB")
        phash = str(imagehash.phash(image))

        # Check if hash is in Redis
        cached_result = r.get(phash)
        if cached_result:
            return jsonify({
                "cached": True,
                "phash": phash,
                "result": cached_result
            })

        # Placeholder AI detection logic
        result = "ai" if "fake" in image_url.lower() else "real"  # dummy check
        r.set(phash, result)

        return jsonify({
            "cached": False,
            "phash": phash,
            "result": result
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050)


