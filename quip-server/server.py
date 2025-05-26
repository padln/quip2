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
    # Create table for storing images and judgments
    tx.execute("""
        CREATE TABLE IF NOT EXISTS images (
            id INTEGER PRIMARY KEY,
            mean BLOB,
            gradient BLOB,
            double_gradient BLOB,
            block BLOB,
            dct BLOB,
            blake3 BLOB,
            judgement INTEGER,
            probability REAL
        )
    """)

    # Create accuracy tracking for each hash type
    tx.execute("""
        CREATE TABLE IF NOT EXISTS hash_accuracy (
            hash_type TEXT PRIMARY KEY,
            correct INTEGER DEFAULT 0,
            incorrect INTEGER DEFAULT 0
        )
    """)

    # Seed the accuracy table with known hash types
    for hash_type in ["mean", "gradient", "double_gradient", "block", "dct"]:
        tx.execute("""
            INSERT OR IGNORE INTO hash_accuracy (hash_type, correct, incorrect)
            VALUES (?, 0, 0)
        """, (hash_type,))

    tx.commit()

def get_hash_weights():
    with db_lock, db as tx:
        rows = tx.execute("SELECT hash_type, correct, incorrect FROM hash_accuracy").fetchall()

    raw_weights = {}
    for hash_type, correct, incorrect in rows:
        total = correct + incorrect
        if total == 0:
            weight = 1.0  # If unused, start optimistically
        else:
            weight = correct / total
        raw_weights[hash_type] = weight

    # Normalize
    total_weight = sum(raw_weights.values()) or 1.0
    normalized_weights = {k: v / total_weight for k, v in raw_weights.items()}
    return normalized_weights

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
        hash_vector = data["hash_vector"]
        mean = base64.b64decode(hash_vector["mean"])
        gradient = base64.b64decode(hash_vector["gradient"])
        double_gradient = base64.b64decode(hash_vector["double_gradient"])
        block = base64.b64decode(hash_vector["block"])
        dct = base64.b64decode(hash_vector["dct"])

        blake3 = str(data["blake3"])
        judgement = int(bool(data["judgement"]))
        probability = float(data["probability"])

    except (ValueError, TypeError) as e:
        return jsonify({"error": str(e)}), 400
    except KeyError as e:
        return jsonify({"error": f"Missing key: {e}"}), 400

    try:
        with db_lock, db as tx:
            # Insert image record
            tx.execute("""
                INSERT INTO images (mean, gradient, double_gradient, block, dct, blake3, judgement, probability)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (mean, gradient, double_gradient, block, dct, blake3, judgement, probability))
            tx.commit()
        logger.debug("Image added to database: %s", data)
        return jsonify({"status": "success"}), 201
    except sqlite3.Error as e:
        return jsonify({"error": str(e)}), 500


@app.route("/results", methods=["GET"])
def query_images():
    try:
        # The request should include a full phash vector
        phash_vector = request.args.get("phash_vector")
        if not phash_vector:
            return jsonify({"error": "Missing phash_vector"}), 400

        # Parse and decode from base64 JSON string
        import json
        raw_vector = json.loads(phash_vector)
        query_hashes = {k: base64.b64decode(v) for k, v in raw_vector.items()}

    except Exception as e:
        return jsonify({"error": f"Failed to parse input: {e}"}), 400

    try:
        weights = get_hash_weights()

        with db_lock:
            rows = db.execute("""
                SELECT judgement, probability, mean, gradient, double_gradient, block, dct
                FROM images
            """).fetchall()

        results = []

        for row in rows:
            judgement, probability = row[0], row[1]
            stored_hashes = {
                "mean": row[2],
                "gradient": row[3],
                "double_gradient": row[4],
                "block": row[5],
                "dct": row[6]
            }

            total_weighted_distance = 0.0
            valid_types = 0

            for k in weights:
                if k in stored_hashes and k in query_hashes and stored_hashes[k] and query_hashes[k]:
                    dist = sum(bin(x ^ y).count("1") for x, y in zip(stored_hashes[k], query_hashes[k]))
                    total_weighted_distance += weights[k] * dist
                    valid_types += 1

            if valid_types > 0:
                results.append((judgement, probability, total_weighted_distance))

        # Sort by distance and take top N
        results.sort(key=lambda x: x[2])
        top_matches = results[:5]

        if not top_matches:
            return jsonify({"error": "No matching entries found", "check_model": True}), 404

        total_ai = sum(prob if judge == 1 else (1 - prob) for judge, prob, _ in top_matches)
        avg_ai_score = total_ai / len(top_matches)

        return jsonify({
            "p_yes": avg_ai_score,
            "p_no": 1 - avg_ai_score,
            "n_matches": len(top_matches),
            "likely_ai": avg_ai_score > 0.7  # adjustable threshold
        })

    except Exception as e:
        return jsonify({"error": f"Internal error: {e}"}), 500

@app.route("/feedback", methods=["POST"])
def feedback():
    """
    Endpoint to receive feedback on hash contributions for classification accuracy.

    Expects a JSON payload with:
        - "hash_contributions": dict mapping hash types to their contribution values (float or int).
        - "correct": boolean indicating if the classification was accurate.

    For each hash type, updates the 'hash_accuracy' table in the database by incrementing
    either the 'correct' or 'incorrect' column based on the 'correct' flag.

    Returns:
        - 200 JSON {"status": "updated"} on success.
        - 400 JSON {"error": "..."} if input is invalid.
        - 500 JSON {"error": "..."} if a database error occurs.
    """
    data = request.get_json()
    try:
        hash_contributions = data["hash_contributions"]  # { "mean": 0.21, "dct": 0.39, ... }
        correct = bool(data["correct"])  # whether the classification was accurate
    except (KeyError, TypeError, ValueError) as e:
        return jsonify({"error": f"Invalid input: {e}"}), 400

    try:
        with db_lock, db as tx:
            for hash_type, contribution in hash_contributions.items():
                if not isinstance(contribution, (int, float)):
                    continue  # skip malformed values

                if correct:
                    tx.execute("""
                        UPDATE hash_accuracy
                        SET correct = correct + ?
                        WHERE hash_type = ?
                    """, (contribution, hash_type))
                else:
                    tx.execute("""
                        UPDATE hash_accuracy
                        SET incorrect = incorrect + ?
                        WHERE hash_type = ?
                    """, (contribution, hash_type))
            tx.commit()
    except sqlite3.Error as e:
        return jsonify({"error": str(e)}), 500

    return jsonify({"status": "updated"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050)


