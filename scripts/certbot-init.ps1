# Obtain initial Let's Encrypt certificate (Windows / PowerShell)
param(
    [Parameter(Mandatory = $true)][string]$Domain,
    [Parameter(Mandatory = $true)][string]$Email
)

$ErrorActionPreference = "Stop"
$env:DOMAIN = $Domain

Write-Host "Starting stack for ACME challenge..."
docker compose up -d web varnish nginx

Write-Host "Requesting certificate for $Domain..."
docker compose --profile production run --rm certbot certonly `
  --webroot -w /var/www/certbot `
  -d $Domain `
  --email $Email `
  --agree-tos `
  --no-eff-email `
  --force-renewal

Write-Host "Reloading nginx with TLS + HTTP/3..."
docker compose up -d --force-recreate nginx

Write-Host "Done. Visit https://$Domain/"
