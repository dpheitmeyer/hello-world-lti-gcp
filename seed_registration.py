#!/usr/bin/env python3
"""Seed Firestore with a Canvas LTI 1.3 platform registration.

Usage:
    python seed_registration.py \
        --issuer https://canvas.instructure.com \
        --client-id 10000000000001 \
        --deployment-id 1:abc123 \
        --auth-login-url https://canvas.instructure.com/api/lti/authorize_redirect \
        --auth-token-url https://canvas.instructure.com/login/oauth2/token \
        --key-set-url https://canvas.instructure.com/api/lti/security/jwks
"""

import argparse

from google.cloud import firestore


def main():
    parser = argparse.ArgumentParser(description="Seed LTI registration in Firestore")
    parser.add_argument("--issuer", required=True)
    parser.add_argument("--client-id", required=True)
    parser.add_argument("--deployment-id", required=True, action="append",
                        help="Can be specified multiple times")
    parser.add_argument("--auth-login-url", required=True)
    parser.add_argument("--auth-token-url", required=True)
    parser.add_argument("--key-set-url", required=True)
    args = parser.parse_args()

    db = firestore.Client()
    doc_id = f"{args.issuer}_{args.client_id}".replace("/", "_").replace(":", "_")

    db.collection("lti_registrations").document(doc_id).set({
        "issuer": args.issuer,
        "client_id": args.client_id,
        "auth_login_url": args.auth_login_url,
        "auth_token_url": args.auth_token_url,
        "key_set_url": args.key_set_url,
        "deployment_ids": args.deployment_id,
    })

    print(f"Registration seeded: {doc_id}")


if __name__ == "__main__":
    main()
