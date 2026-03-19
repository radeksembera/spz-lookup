from flask import Flask, render_template, request, jsonify
import requests

app = Flask(__name__)

API_URL = "https://api.dataovozidlech.cz/api/vehicletechnicaldata/v2"
API_KEY = "QyJ_nyfMd-ErTTv7j-bHrOzaP4oRMXnP"

# Mapping of API response fields to Czech labels
FIELD_MAP = [
    ("make",                      "Značka"),
    ("model",                     "Model"),
    ("firstRegistrationYear",     "Rok první registrace"),
    ("color",                     "Barva"),
    ("fuelType",                  "Palivo"),
    ("numberOfOwners",            "Počet vlastníků"),
    ("technicalInspectionStatus", "Stav STK"),
    ("vehicleStatus",             "Status vozidla"),
]


def lookup_vehicle(params: dict) -> dict:
    try:
        resp = requests.get(
            API_URL,
            headers={"api_key": API_KEY},
            params=params,
            timeout=15,
        )
    except requests.RequestException as e:
        return {"error": f"Chyba připojení: {e}"}

    print("API response:", resp.status_code, resp.text[:500])

    if resp.status_code == 404:
        return {"error": "Vozidlo nebylo nalezeno."}
    if resp.status_code == 401:
        return {"error": "Neplatný API klíč."}
    if not resp.ok:
        return {"error": f"Chyba API ({resp.status_code}): {resp.text[:200]}"}

    try:
        body = resp.json()
    except ValueError:
        return {"error": "API vrátilo neplatnou odpověď (není JSON)."}

    data = body.get("Data") or body
    print("Data keys:", list(data.keys()) if isinstance(data, dict) else type(data))

    fields = []
    for key, label in FIELD_MAP:
        value = data.get(key)
        if value is not None and value != "":
            fields.append({"label": label, "value": str(value)})

    # FIELD_MAP didn't match — fall back to showing all fields from Data
    if not fields and isinstance(data, dict):
        for key, value in data.items():
            if value is not None and value != "":
                fields.append({"label": key, "value": str(value)})

    if not fields:
        return {"error": "API nevrátilo žádné použitelné údaje.", "raw": data}

    return {"fields": fields}


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/lookup", methods=["POST"])
def lookup():
    vin = request.form.get("vin", "").strip().upper()
    tp  = request.form.get("tp",  "").strip()
    orv = request.form.get("orv", "").strip()

    if not any([vin, tp, orv]):
        return jsonify({"error": "Zadejte alespoň jedno z: VIN, TP číslo, ORV číslo."}), 400

    # Use first provided value as query parameter
    if vin:
        params = {"vin": vin}
        query_label = f"VIN: {vin}"
    elif tp:
        params = {"tp": tp}
        query_label = f"TP: {tp}"
    else:
        params = {"orv": orv}
        query_label = f"ORV: {orv}"

    result = lookup_vehicle(params)
    result["query"] = query_label
    return jsonify(result)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
