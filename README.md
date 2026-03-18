# LTI 1.3 Hello World — Google Cloud Functions

A serverless LTI 1.3 tool that displays a greeting with the user's name and all LTI launch parameters. Built with Python, Flask, and pylti1p3 on Google Cloud Functions Gen 2.

## Architecture

- **Cloud Function Gen 2** — Flask WSGI app with endpoints: `/login`, `/launch`, `/jwks`, `/config.xml`
- **Firestore** (Native mode) — OIDC state/nonce cache (`lti_cache`) + platform registrations (`lti_registrations`)
- **Secret Manager** — RSA private key (public key derived at runtime)
- **GitHub Actions** — Deploys on push to `main` via Workload Identity Federation

## GCP Setup

### 1. Create a GCP Project

```bash
export PROJECT_ID=your-project-id
gcloud config set project $PROJECT_ID
```

### 2. Enable APIs

```bash
gcloud services enable \
  cloudfunctions.googleapis.com \
  cloudbuild.googleapis.com \
  firestore.googleapis.com \
  secretmanager.googleapis.com \
  run.googleapis.com \
  iam.googleapis.com \
  iamcredentials.googleapis.com
```

### 3. Create Firestore Database

```bash
gcloud firestore databases create --location=us-central1
```

Set up a TTL policy on the cache collection to auto-delete expired docs:

```bash
gcloud firestore fields ttls update expires_at \
  --collection-group=lti_cache \
  --enable-ttl
```

### 4. Generate RSA Key and Store in Secret Manager

```bash
openssl genrsa -out private.pem 4096
gcloud secrets create lti-private-key --data-file=private.pem
rm private.pem
```

### 5. Set Up Workload Identity Federation for GitHub Actions

```bash
# Create workload identity pool
gcloud iam workload-identity-pools create github-pool \
  --location=global \
  --display-name="GitHub Actions Pool"

# Create provider
gcloud iam workload-identity-pools providers create-oidc github-provider \
  --location=global \
  --workload-identity-pool=github-pool \
  --display-name="GitHub Provider" \
  --attribute-mapping="google.subject=assertion.sub,attribute.repository=assertion.repository" \
  --attribute-condition="assertion.repository == 'dpheitmeyer/hello-world-lti-gcp'" \
  --issuer-uri="https://token.actions.githubusercontent.com"

# Create service account
gcloud iam service-accounts create github-deployer \
  --display-name="GitHub Actions Deployer"

# Grant roles
export SA=github-deployer@${PROJECT_ID}.iam.gserviceaccount.com
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${SA}" \
  --role="roles/cloudfunctions.developer"
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${SA}" \
  --role="roles/iam.serviceAccountUser"
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${SA}" \
  --role="roles/secretmanager.secretAccessor"
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${SA}" \
  --role="roles/datastore.user"

# Allow GitHub repo to impersonate the service account
export REPO=dpheitmeyer/hello-world-lti-gcp
gcloud iam service-accounts add-iam-policy-binding $SA \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/projects/$(gcloud projects describe $PROJECT_ID --format='value(projectNumber)')/locations/global/workloadIdentityPools/github-pool/attribute.repository/${REPO}"
```

### 6. Update `.github/workflows/deploy.yml`

Fill in the `TODO` placeholders with your project ID, WIF provider path, service account, and function URL.

## Seed Canvas Registration

After deploying, seed Firestore with your Canvas instance's details:

```bash
python seed_registration.py \
  --issuer https://canvas.instructure.com \
  --client-id YOUR_CLIENT_ID \
  --deployment-id YOUR_DEPLOYMENT_ID \
  --auth-login-url https://canvas.instructure.com/api/lti/authorize_redirect \
  --auth-token-url https://canvas.instructure.com/login/oauth2/token \
  --key-set-url https://canvas.instructure.com/api/lti/security/jwks
```

For self-hosted Canvas, replace `canvas.instructure.com` with your Canvas domain.

## Canvas Registration (4 Methods)

All four Canvas Developer Key registration methods are supported:

| Method | What to enter |
|--------|--------------|
| **By URL** | `{FUNCTION_URL}/config.xml` |
| **Paste XML** | Copy the XML from that URL and paste it |
| **By Client ID** | Create the Developer Key first, then enter the client_id in course settings |
| **Manual Entry** | OIDC Login: `{FUNCTION_URL}/login`, Target Link: `{FUNCTION_URL}/launch`, JWKS: `{FUNCTION_URL}/jwks` |

After creating the Developer Key, add the deployment to your seeded registration's `deployment_ids` array in Firestore.

## Local Testing

```bash
pip install -r requirements.txt
export GCP_PROJECT=your-project-id
export FUNCTION_URL=https://your-tunnel-url  # e.g., ngrok
functions-framework --target=app --debug --port=8080
```

## Verification

1. Deploy via push to `main` (or run locally with a tunnel)
2. Register in Canvas using any of the 4 methods
3. Add the tool to a course via Settings → Navigation
4. Click to launch — you should see "Hello, {name}!" with a table of all LTI claims
5. Check Firestore `lti_cache` collection for OIDC state docs
