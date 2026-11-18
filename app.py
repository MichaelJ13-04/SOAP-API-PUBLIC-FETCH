
from flask import Flask, request, jsonify
from zeep import Client
from zeep.transports import Transport
from zeep.exceptions import Fault
from requests import Session
from requests.exceptions import RequestException

app = Flask(__name__)

# Public SOAP calculator WSDL
WSDL_URL = "https://funapi.dev/api/soap/v1/calculator.wsdl"


def calculate(operation, a, b):
    # Validate the requested operation
    allowed_operations = ["Add", "Subtract", "Multiply", "Divide"]

    if operation not in allowed_operations:
        raise ValueError(
            "Invalid operation. Choose Add, Subtract, Multiply, or Divide."
        )

    # Validate numeric inputs
    try:
        a = float(a)
        b = float(b)
    except (TypeError, ValueError):
        raise ValueError("Both inputs must be numbers.")

    if abs(a) > 100000 or abs(b) > 100000:
        raise ValueError("Numbers must be between -100000 and 100000.")

    if operation == "Divide" and b == 0:
        raise ValueError("Cannot divide by zero.")

    # Connect to the SOAP service
    session = Session()
    transport = Transport(session=session, timeout=20)
    client = Client(WSDL_URL, transport=transport)

    # Call the SOAP operation
    soap_method = getattr(client.service, operation)
    result = soap_method(a, b)

    return result


# GET and POST API endpoint
@app.route("/calculate", methods=["GET", "POST"])
def calculate_route():
    try:
        if request.method == "GET":
            data = request.args
        else:
            data = request.get_json(silent=True) or {}

        operation = data.get("operation", "Add")
        a = data.get("a")
        b = data.get("b")

        if a is None or b is None:
            return jsonify({
                "error": "Both a and b values are required."
            }), 400

        result = calculate(operation, a, b)

        return jsonify({
            "operation": operation,
            "first_number": a,
            "second_number": b,
            "result": result
        }), 200

    except ValueError as exc:
        return jsonify({
            "error": f"Validation error: {exc}"
        }), 400

    except (Fault, RequestException) as exc:
        return jsonify({
            "error": f"SOAP service error: {exc}"
        }), 502

    except Exception as exc:
        return jsonify({
            "error": f"Unexpected error: {exc}"
        }), 500


# Start Flask application
if __name__ == "__main__":
    app.run(debug=True)
