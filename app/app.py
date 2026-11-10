from flask import Flask, request, jsonify
from functools import wraps
import os

app = Flask(__name__)

# ---------------------------------------------------------------------------
# In-memory store
# ---------------------------------------------------------------------------
vehicles = {}
next_id = 1

# ---------------------------------------------------------------------------
# API Key authentication
# ---------------------------------------------------------------------------
API_KEY = os.environ.get("API_KEY", "your-api-key-here")

def require_api_key(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        key = request.headers.get("x-api-key") or request.args.get("apiKey")
        if key != API_KEY:
            return jsonify({"message": "Unauthorized: invalid or missing API key"}), 401
        return f(*args, **kwargs)
    return decorated

# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------
def vehicle_to_dict(v):
    return {
        "id":       v["id"],
        "nickName": v["nickName"],
        "vin":      v["vin"],
        "make":     v["make"],
        "model":    v["model"],
        "year":     v["year"],
        "miles":    v["miles"],
    }

REQUIRED_FIELDS = ["nickName", "vin", "make", "model", "year", "miles"]

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

# POST /vehicles — Create a vehicle
@app.route("/vehicles", methods=["POST"])
@require_api_key
def create_vehicle():
    global next_id
    try:
        data = request.get_json(force=True)
    except Exception:
        return jsonify({"message": "Invalid JSON body"}), 400

    if not data:
        return jsonify({"message": "Request body is required"}), 400

    # Validate required fields
    for field in REQUIRED_FIELDS:
        if field not in data or data[field] is None or data[field] == "":
            return jsonify({"message": f"Request body missing required attribute: {field}"}), 400

    # Check for duplicate VIN
    for v in vehicles.values():
        if v["vin"] == data["vin"]:
            return jsonify({
                "message": f"Vehicle with VIN {data['vin']} already exists. Existing vehicle ID: {v['id']}"
            }), 409

    vehicle = {
        "id":       next_id,
        "nickName": data["nickName"],
        "vin":      data["vin"],
        "make":     data["make"],
        "model":    data["model"],
        "year":     str(data["year"]),
        "miles":    data["miles"],
    }
    vehicles[next_id] = vehicle
    next_id += 1

    return jsonify(vehicle_to_dict(vehicle)), 201


# GET /vehicles — Get all vehicles
@app.route("/vehicles", methods=["GET"])
@require_api_key
def get_all_vehicles():
    return jsonify([vehicle_to_dict(v) for v in vehicles.values()]), 200


# GET /vehicles/:id — Retrieve a vehicle
@app.route("/vehicles/<int:vehicle_id>", methods=["GET"])
@require_api_key
def get_vehicle(vehicle_id):
    vehicle = vehicles.get(vehicle_id)
    if not vehicle:
        return jsonify({"message": f"Vehicle with id: {vehicle_id} not found."}), 404
    return jsonify(vehicle_to_dict(vehicle)), 200


# PATCH /vehicles/:id — Update a vehicle
@app.route("/vehicles/<int:vehicle_id>", methods=["PATCH"])
@require_api_key
def update_vehicle(vehicle_id):
    vehicle = vehicles.get(vehicle_id)
    if not vehicle:
        return jsonify({"message": f"Vehicle with id: {vehicle_id} not found."}), 404

    try:
        data = request.get_json(force=True)
    except Exception:
        return jsonify({"message": "Invalid JSON body"}), 400

    if not data:
        return jsonify({"message": "Request body is required"}), 400

    # Only allow updating known fields (not id)
    updatable = ["nickName", "vin", "make", "model", "year", "miles"]
    has_update = False
    for field in updatable:
        if field in data:
            if data[field] is None or data[field] == "":
                return jsonify({"message": f"Attribute '{field}' cannot be empty"}), 400
            vehicle[field] = data[field]
            has_update = True

    if not has_update:
        return jsonify({"message": "Request body must contain at least one updatable field"}), 400

    return jsonify(vehicle_to_dict(vehicle)), 200


# DELETE /vehicles/:id — Delete a vehicle
@app.route("/vehicles/<int:vehicle_id>", methods=["DELETE"])
@require_api_key
def delete_vehicle(vehicle_id):
    if vehicle_id not in vehicles:
        return jsonify({"message": f"Vehicle with id: {vehicle_id} not found."}), 404
    del vehicles[vehicle_id]
    return "", 204


# ---------------------------------------------------------------------------
# Generic error handlers
# ---------------------------------------------------------------------------
@app.errorhandler(404)
def not_found(e):
    return jsonify({"message": "Route not found"}), 404

@app.errorhandler(405)
def method_not_allowed(e):
    return jsonify({"message": "Method not allowed"}), 405

@app.errorhandler(500)
def internal_error(e):
    return jsonify({"message": "An unexpected error occurred"}), 500


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, port=port)
