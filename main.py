import os

from flask import Flask
from google.cloud import firestore, secretmanager
from jwcrypto import jwk

from lti.cache import FirestoreCache
from lti.config import ToolConfFirestore
from lti.routes import bp

# Module-level singletons (cached across warm GCF invocations)
db = firestore.Client()

# Load RSA private key from Secret Manager
project = os.environ.get("GCP_PROJECT")
sm_client = secretmanager.SecretManagerServiceClient()
secret_name = f"projects/{project}/secrets/lti-private-key/versions/latest"
response = sm_client.access_secret_version(name=secret_name)
private_key_pem = response.payload.data.decode("utf-8")

# Derive public key JWK from private key
key_obj = jwk.JWK.from_pem(private_key_pem.encode("utf-8"))
public_key_jwk = key_obj.export_public(as_dict=True)
public_key_jwk["use"] = "sig"
public_key_jwk["alg"] = "RS256"

# Build Flask app
app = Flask(__name__)
app.config["TOOL_CONF"] = ToolConfFirestore(db, private_key_pem, public_key_jwk)
app.config["LTI_CACHE"] = FirestoreCache(db)
app.register_blueprint(bp)
