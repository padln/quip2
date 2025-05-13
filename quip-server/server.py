from flask import Flask, request, jsonify
import redis # type: ignore
import imagehash # type: ignore
from PIL import Image
import requests
from io import BytesIO
from flask_cors import CORS # type: ignore
import sqlite3
import threading
import logging
import base64

app = Flask(__name__)
CORS(app)
r = redis.Redis(host='redis', port=6379, decode_responses=True)

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("quip")

db_lock = threading.Lock()
# In memory for testing
db = sqlite3.connect(":memory:", check_same_thread=False)
db.enable_load_extension(True)
db.load_extension("./libsqlite_hamming.so")
db.enable_load_extension(False)
with db as tx:
    tx.execute("CREATE TABLE images (id INTEGER PRIMARY KEY, phash BLOB, blake3 BLOB, judgement INTEGER, probability REAL)")
    tx.commit()

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

@app.route("/results", methods=["POST"])
def add_image():
    data = request.get_json()
    try:
        phash = base64.b64decode(str(data["phash"]))
        blake3 = str(data["blake3"])
        judgement = bool(data["judgement"])
        probability = float(data["probability"])
    except (ValueError, TypeError) as e:
        return jsonify({"error": str(e)}), 400
    except KeyError as e:
        return jsonify({"error": f"Missing key: {e}"}), 400

    try:
        with db_lock, db as tx:
            # Insert image record
            tx.execute("INSERT INTO images (phash, blake3, judgement, probability) VALUES (?, ?, ?, ?)",
                       (phash, blake3, judgement, probability))
            tx.commit()
        logger.debug("Image added to database: %s", data)
        return jsonify({"status": "success"}), 201
    except sqlite3.Error as e:
        return jsonify({"error": str(e)}), 500


@app.route("/results", methods=["GET"])
def query_images():
    try:
        phash = base64.b64decode(request.args["phash"])
    except KeyError as e:
        return jsonify({"error": f"Missing query param: {e}"}), 400

    try:
        with db_lock:
            # Retrieve n closest image records
            rows = db.execute(
                """
                    SELECT i.judgement, i.probability, hamming(i.phash, :phash) AS dist
                    FROM images AS i
                    WHERE dist < :min_dist
                    ORDER BY dist ASC
                    LIMIT :max_results
                """,
                # TODO: Values for closeness and number of results to consider should be determined experimentally
                dict(phash=phash, min_dist=5, max_results=10)
            ).fetchall()
    except sqlite3.Error as e:
        return jsonify({"error": str(e)}), 500

    if len(rows) == 0:
        return jsonify({"error": "No matching image found"}), 404

    # Calculate probabilities of yes/no. Perhaps the distance should also be considered?
    total_yes = sum(row[1] for row in rows if row[0] == 1) + sum((1 - row[1]) for row in rows if row[0] == 0)
    total_no =  sum(row[1] for row in rows if row[0] == 0) + sum((1 - row[1]) for row in rows if row[0] == 1)
    p_yes = total_yes / (total_yes + total_no)
    p_no = total_no / (total_yes + total_no)

    return jsonify({
        "p_yes": p_yes,
        "p_no": p_no,
        "n_matches": len(rows),
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050)


