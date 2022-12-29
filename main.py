"""Fetch the product data using UPC."""
import base64
import json
import os
import traceback

import functions_framework
from google.cloud import firestore


@functions_framework.http
def get_product_by_upc(request):
    """HTTP Cloud Function to fetch the data from firestore using UPC.
    Along with this function log the details regarding request and response.

    Args:
        request (flask.Request): The request object.
        <https://flask.palletsprojects.com/en/1.1.x/api/#incoming-request-data>
    Returns:
        Json data containing brand, productName, etc.. if UPC is found in fireststore.
        Otherwise message with 'UPC not found'.
        <https://flask.palletsprojects.com/en/1.1.x/api/#flask.make_response>.
    """

    try:
        jwt_token = request.headers.get("X-Apigateway-Api-Userinfo", "")
        jwt_token = jwt_token + "=" * divmod(len(jwt_token), 4)[1]
        decoded_jwt_str = base64.b64decode(jwt_token).decode("utf-8")
        uid = json.loads(decoded_jwt_str).get("user_id", "")
    except Exception:  # pylint: disable=broad-except
        response_json = {"code": 500, "message": "Server error"}
        print("Got error while fetching uid.")
        traceback.print_exc()
        return (json.dumps(response_json), 500)

    upc = request.args.get("UPC", "")

    request_log = {"upc": upc, "uid": uid, "action": "request"}
    print(json.dumps(request_log))

    try:
        db_ = firestore.Client()
        doc_ref = db_.collection(
            os.environ.get("FIRESTORE_COLLECTION_NAME", "")
        ).document(upc)
        all_values = doc_ref.get().to_dict()
    except Exception:  # pylint: disable=broad-except
        response_json = {"code": 500, "message": "Server error"}
        print("got error while getting upc data from firestore.")
        traceback.print_exc()
        return (json.dumps(response_json), 500)

    status_code = 454
    response_json = {
        "code": 454,
        "message": "Hmmm... Sorry this barcode isn't in our food library.",
    }
    response_log = {
        "upc": upc,
        "uid": uid,
        "nv": None,
        "ev": None,
        "brand": None,
        "productName": None,
        "exists": False,
        "action": "response",
    }
    if upc and all_values:
        try:
            nv_ = all_values.get("nv", None)
            if nv_ is not None:
                nv_ = float(nv_)
        except Exception:  # pylint: disable=broad-except
            nv_ = None
        try:
            ev_ = all_values.get("ev", None)
            if ev_ is not None:
                ev_ = float(ev_)
        except Exception:  # pylint: disable=broad-except
            ev_ = None

        upc = all_values.get("code", None)
        status_code = 200
        response_json = {
            "upc": upc,
            "brand": all_values.get("brand", None),
            "productName": all_values.get("productName", None),
            "nv": nv_,
            "ev": ev_,
        }
        response_log = {
            "upc": upc,
            "uid": uid,
            "nv": nv_,
            "ev": ev_,
            "brand": all_values.get("brand", None),
            "productName": all_values.get("productName", None),
            "exists": True,
            "action": "response",
        }

    print(json.dumps(response_log))

    return (json.dumps(response_json), status_code)
