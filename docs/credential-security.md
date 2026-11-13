# Private deployment credentials

Deployment credentials default to empty and are validated before role changes.
Store real values in an encrypted Ansible Vault file and pass it with `-e @vault.yml`
and `--ask-vault-pass`. Do not commit decrypted credentials or reuse old published
example passwords. Existing deployments using published values need separate,
approved live rotation; this source change does not rotate running services.

Grafana and HAProxy statistics passwords must have at least 16 characters.
HAProxy statistics passwords cannot contain whitespace. Keepalived PASS accepts
exactly eight alphanumeric characters; use the same private value on VRRP peers.
ESXi passwords must have at least 12 characters. These requirements apply only
to roles in this repository that use the corresponding credential.

SSH host verification is enabled. Verify server fingerprints through a trusted
channel and populate known_hosts before deployment. ESXi certificate validation
is enabled and required by the snapshot preflight; install the issuing CA on the
Ansible controller rather than disabling verification.

Secret-bearing templates and tasks suppress logs and diffs. Config files written
by these roles restrict read access. `--check` and syntax checks are not a live
credential-rotation procedure.
