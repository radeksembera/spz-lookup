from flask import Flask, render_template, request, jsonify
import requests

app = Flask(__name__)

API_URL = "https://api.dataovozidlech.cz/api/vehicletechnicaldata/v2"
API_KEY = "QyJ_nyfMd-ErTTv7j-bHrOzaP4oRMXnP"


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

    fields = []
    if isinstance(data, dict):
        for key, label in FIELD_MAP:
            value = data.get(key)
            if value is not None and value != "":
                fields.append({"label": label, "value": str(value)})

        if not fields:
            for key, value in data.items():
                if value is not None and value != "":
                    fields.append({"label": key, "value": str(value)})

    if not fields:
        return {"error": "API nevrátilo žádné použitelné údaje.", "raw": data}

    return {"fields": fields}


def get_insurance_calculation_mock(reg_plate: str, zip_code: str, age: int) -> dict:
    """
    Dočasný mock pro POC.
    Až budeš mít reálný přístup k SURI, nahradíš tuhle funkci skutečným API voláním.
    """
    return {
        "vehicleSummary": f"Výsledek pro SPZ {reg_plate}",
        "quotes": [
            {
                "insuranceCompany": "UNIQA",
                "tariffName": "100/100 mil. Kč",
                "priceAnnual": 4195,
                "limitHealth": 100,
                "limitProperty": 100,
            },
            {
                "insuranceCompany": "Direct",
                "tariffName": "100/100 mil. Kč",
                "priceAnnual": 4881,
                "limitHealth": 100,
                "limitProperty": 100,
            },
            {
                "insuranceCompany": "Allianz",
                "tariffName": "70/70 mil. Kč",
                "priceAnnual": 4943,
                "limitHealth": 70,
                "limitProperty": 70,
            },
        ],
        "input": {
            "regPlate": reg_plate,
            "zip": zip_code,
            "age": age,
        },
    }


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/insurance", methods=["GET"])
def insurance():
    reg_plate = request.args.get("regPlate", "").strip().upper()
    zip_code = request.args.get("zip", "").strip()
    age_raw = request.args.get("age", "").strip()

    if not reg_plate or not zip_code or not age_raw:
        return render_template(
            "insurance.html",
            error="Vyplňte SPZ, PSČ a věk.",
            result=None,
        )

    try:
        age = int(age_raw)
    except ValueError:
        return render_template(
            "insurance.html",
            error="Věk musí být číslo.",
            result=None,
        )

    # TODO: tady později nahradit reálným voláním SURI API
    result = get_insurance_calculation_mock(reg_plate, zip_code, age)

    return render_template("insurance.html", error=None, result=result)


@app.route("/lookup", methods=["POST"])
def lookup():
    vin = request.form.get("vin", "").strip().upper()
    tp = request.form.get("tp", "").strip()
    orv = request.form.get("orv", "").strip()

    if not any([vin, tp, orv]):
        return jsonify({"error": "Zadejte alespoň jedno z: VIN, TP číslo, ORV číslo."}), 400

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