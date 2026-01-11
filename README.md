# gcp-oidc

Example applications demonstrating service-to-service authentication using
Google-signed OpenID Connect ID tokens.

See the following blog post:
- [Service-to-Service Authentication with Google Cloud Run][Service-to-Service Authentication with Google Cloud Run]

## Deploy

1. Build the Docker container:

```bash
docker buildx build \
  --platform linux/amd64 \
  -t <REPOSITORY>/app:latest .
```

2. Apply the Terraform:

```bash
cd tf/
terraform init
terraform plan
terraform apply
```

[Service-to-Service Authentication with Google Cloud Run]: https://nickolaskraus.io/posts/service-to-service-authentication-with-google-cloud-run/
