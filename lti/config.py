from pylti1p3.tool_config import ToolConfAbstract
from pylti1p3.registration import Registration


class ToolConfFirestore(ToolConfAbstract):
    """pylti1p3 tool configuration backed by Firestore."""

    _collection = "lti_registrations"

    def __init__(self, db, private_key_pem, public_key_jwk):
        super().__init__()
        self._db = db
        self._private_key_pem = private_key_pem
        self._public_key_jwk = public_key_jwk

    def _query(self, **filters):
        ref = self._db.collection(self._collection)
        for field, value in filters.items():
            ref = ref.where(field, "==", value)
        docs = ref.limit(1).get()
        return docs[0].to_dict() if docs else None

    def _to_registration(self, data):
        reg = Registration()
        reg.set_auth_login_url(data["auth_login_url"])
        reg.set_auth_token_url(data["auth_token_url"])
        reg.set_client_id(data["client_id"])
        reg.set_key_set_url(data.get("key_set_url"))
        reg.set_issuer(data["issuer"])
        reg.set_tool_private_key(self._private_key_pem)
        reg.set_tool_public_key(self._public_key_jwk)
        return reg

    def find_registration_by_issuer(self, iss, *args, **kwargs):
        data = self._query(issuer=iss)
        if not data:
            raise Exception(f"Registration not found for issuer: {iss}")
        return self._to_registration(data)

    def find_registration_by_params(self, iss, client_id, *args, **kwargs):
        data = self._query(issuer=iss, client_id=client_id)
        if not data:
            raise Exception(
                f"Registration not found for issuer={iss}, client_id={client_id}"
            )
        return self._to_registration(data)

    def find_deployment(self, iss, deployment_id):
        data = self._query(issuer=iss)
        if not data:
            return None
        if deployment_id in data.get("deployment_ids", []):
            return deployment_id
        return None

    def find_deployment_by_params(self, iss, deployment_id, client_id, *args, **kwargs):
        data = self._query(issuer=iss, client_id=client_id)
        if not data:
            return None
        if deployment_id in data.get("deployment_ids", []):
            return deployment_id
        return None

    def get_jwks(self):
        return {"keys": [self._public_key_jwk]}
