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
    # Create the table if it doesn't exist 
    # countaining the phash and blake3 hashes
    # and the judgement (0 or 1) and probability
    tx.execute(
        """
        CREATE TABLE images (
            id INTEGER PRIMARY KEY,
            phash BLOB,
            blake3 BLOB,
            judgement INTEGER,
            probability REAL
        )
        """
    )
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
    """
    Handles the POST request to add an image record to the database.

    Route:
        /results

    Methods:
        POST

    Request Body (JSON):
        - phash (str): Base64-encoded perceptual hash of the image.
        - blake3 (str): BLAKE3 hash of the image.
        - judgement (bool): Judgement value associated with the image.
        - probability (float): Probability score associated with the image.

    Responses:
        - 201: Successfully added the image record to the database.
            {
                "status": "success"
            }
        - 400: Bad request due to missing or invalid data.
            {
                "error": "Error message"
            }
        - 500: Internal server error due to database issues.
            {
                "error": "Error message"
            }

    Raises:
        - ValueError: If the data contains invalid types.
        - TypeError: If the data contains invalid types.
        - KeyError: If required keys are missing from the request body.
        - sqlite3.Error: If there is an error interacting with the database.
    """
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
    """
    Handles the GET request to query the database for images similar to the provided perceptual hash (phash).

    Route:
        /results

    Methods:
        GET

    Query Parameters:
        - phash (str): Base64-encoded perceptual hash of the image to query.

    Responses:
        - 200: Successfully retrieved matching images and calculated probabilities.
            {
                "p_yes": float,  # Probability of a "yes" judgement.
                "p_no": float,   # Probability of a "no" judgement.
                "n_matches": int # Number of matching images found.
            }
        - 400: Bad request due to missing or invalid query parameters.
            {
                "error": "Error message"
            }
        - 404: No matching images found in the database.
            {
                "error": "No matching image found"
            }
        - 500: Internal server error due to database issues.
            {
                "error": "Error message"
            }
    """
    try:
        # Decode the provided base64-encoded perceptual hash (phash) from the query parameter
        phash = base64.b64decode(request.args["phash"])
    except KeyError as e:
        # Return an error if the required query parameter is missing
        return jsonify({"error": f"Missing query param: {e}"}), 400

    try:
        with db_lock:
            # Query the database for images with a Hamming distance less than a threshold (min_dist)
            # and retrieve the closest matches, ordered by distance
            rows = db.execute(
                """
                    SELECT i.judgement, i.probability, hamming(i.phash, :phash) AS dist
                    FROM images AS i
                    WHERE dist < :min_dist
                    ORDER BY dist ASC
                    LIMIT :max_results
                """,
                # Parameters for the query: phash to compare, minimum distance, and max results to return
                dict(phash=phash, min_dist=5, max_results=10)
            ).fetchall()
    except sqlite3.Error as e:
        # Return an error if there is an issue with the database query
        return jsonify({"error": str(e)}), 500

    if len(rows) == 0:
        # Return a 404 error if no matching images are found
        return jsonify({"error": "No matching image found"}), 404

    # Calculate the probabilities of "yes" and "no" judgements based on the retrieved matches
    total_yes = sum(row[1] for row in rows if row[0] == 1) + sum((1 - row[1]) for row in rows if row[0] == 0)
    total_no =  sum(row[1] for row in rows if row[0] == 0) + sum((1 - row[1]) for row in rows if row[0] == 1)
    p_yes = total_yes / (total_yes + total_no)
    p_no = total_no / (total_yes + total_no)

    # Return the calculated probabilities and the number of matches found
    return jsonify({
        "p_yes": p_yes,       # Probability of a "yes" judgement
        "p_no": p_no,         # Probability of a "no" judgement
        "n_matches": len(rows) # Number of matching images found
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050)


