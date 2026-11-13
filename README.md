# Ansible: VMware ESXi Snapshot & Linux Yum Update

Author: Akshat Kalkhanda
Email: [akshatkalkhanda@gmail.com]

Automates two sequential operations against a standalone VMware ESXi host and its Linux VMs:

1. **Snapshot** — Queries ESXi for all registered VMs, filters to Linux VMs by guest OS type (`guestId`), and takes a dated snapshot of each before any changes are made.
2. **Update & Reboot** — SSH into each Linux VM, run a full `yum`/`dnf` update, reboot if a kernel or glibc update was installed, and wait for the host to return online.

---

## Prerequisites

### Control Node (machine running Ansible)

| Requirement | Version |
|---|---|
| Python | 3.9+ |
| Ansible | 2.14+ |
| `pyvmomi` Python library | latest |

Install Python dependencies:

```bash
pip install pyvmomi
```

Install Ansible collections:

```bash
ansible-galaxy collection install -r requirements.yml
```

### Managed Nodes (Linux VMs)

- SSH access from the control node
- `sudo` / root privileges for the Ansible user
- `needs-restarting` available (part of the `yum-utils` package on RHEL/CentOS)

Install `yum-utils` on managed nodes if not present:

```bash
yum install -y yum-utils    # RHEL/CentOS 7-8
dnf install -y yum-utils    # RHEL/CentOS 9 / Rocky / AlmaLinux
```

---

## Configuration

### 1. ESXi credentials — `group_vars/all.yml`

Open `group_vars/all.yml` and fill in your ESXi details:

```yaml
esxi_hostname: "esxi.example.com"   # IP or FQDN of the ESXi host
esxi_username: "root"               # ESXi username
esxi_password: ""                   # Required: set through Ansible Vault
esxi_validate_certs: true          # Required: trust the issuing CA
```

> **Security tip**: Store `esxi_password` in Ansible Vault rather than plain text.
> Run: `ansible-vault encrypt_string 'your_password' --name 'esxi_password'`

### 2. Linux VM inventory — `inventory/hosts.yml`

Add every Linux VM you want to update under the `linux_vms` group:

```yaml
linux_vms:
  hosts:
    vm-rhel-01:
      ansible_host: 192.168.1.101
    vm-centos-02:
      ansible_host: 192.168.1.102
  vars:
    ansible_user: root
    ansible_ssh_private_key_file: ~/.ssh/id_rsa
```

### 3. Optional tuning — role defaults

**`roles/vmware_snapshot/defaults/main.yml`**

| Variable | Default | Description |
|---|---|---|
| `snapshot_name_prefix` | `pre-update` | Prefix for the snapshot name (date is appended automatically) |
| `snapshot_description` | `Automated pre-update snapshot...` | Snapshot description shown in ESXi |
| `snapshot_memory` | `false` | Include VM memory state in snapshot |
| `snapshot_quiesce` | `false` | Quiesce guest filesystem before snapshot |
| `linux_guest_id_patterns` | `rhel, centos, ubuntu...` | List of substrings matched against ESXi `guestId` to identify Linux VMs |

**`roles/linux_yum_update/defaults/main.yml`**

| Variable | Default | Description |
|---|---|---|
| `yum_update_exclude` | `[]` | List of packages to exclude from the update (e.g. `["kernel*"]`) |
| `reboot_timeout` | `600` | Seconds to wait for host to return after reboot |
| `reboot_pre_reboot_delay` | `5` | Seconds to wait before issuing the reboot command |
| `reboot_post_reboot_delay` | `30` | Seconds to wait after the host comes back before continuing |

---

## Usage

### Full run (snapshot first, then update + reboot)

```bash
cd ansible/
ansible-playbook site.yml -i inventory/hosts.yml
```

### Snapshot only (skip the update)

```bash
ansible-playbook site.yml -i inventory/hosts.yml --tags snapshot
```

### Update only (skip snapshots — not recommended for production)

```bash
ansible-playbook site.yml -i inventory/hosts.yml --tags update
```

### Dry run (check mode — no changes made)

```bash
ansible-playbook site.yml -i inventory/hosts.yml --check
```

### Using Ansible Vault for the ESXi password

```bash
ansible-playbook site.yml -i inventory/hosts.yml --ask-vault-pass
```

---

## What happens, step by step

```
[Play 1 — localhost]
  1. Queries ESXi API for all registered VM names (vmware_vm_info)
  2. Retrieves detailed guest info for each VM (vmware_guest_info)
  3. Filters out Windows VMs (hw_guest_id matches 'windows' pattern)
  4. Filters to Linux VMs (hw_guest_id matches linux_guest_id_patterns)
  5. Creates snapshot "<snapshot_name_prefix>-YYYY-MM-DD" on each Linux VM
  6. Reports results

[Play 2 — linux_vms group, one host at a time]
  7. Gathers facts on each Linux VM
  8. Asserts the host uses yum or dnf
  9. Runs `yum/dnf update -y` (all packages)
  10. Reboots host unconditionally and waits for SSH to return
  11. Gathers facts post-reboot and reports the running kernel version
```

---

## Project Structure

```
ansible/
├── ansible.cfg                            # Ansible configuration
├── site.yml                               # Master playbook
├── requirements.yml                       # Collection dependencies
├── inventory/
│   └── hosts.yml                          # VM inventory
├── group_vars/
│   └── all.yml                            # ESXi credentials and shared vars
└── roles/
    ├── vmware_snapshot/
    │   ├── defaults/main.yml              # Configurable defaults
    │   ├── meta/main.yml                  # Role metadata
    │   └── tasks/main.yml                 # Snapshot tasks
    └── linux_yum_update/
        ├── defaults/main.yml              # Configurable defaults
        ├── handlers/main.yml              # Reboot handler
        ├── meta/main.yml                  # Role metadata
        └── tasks/main.yml                 # Update and reboot tasks
```

---

## Troubleshooting

| Problem | Solution |
|---|---|
| `No module named 'pyVmomi'` | Run `pip install pyvmomi` on the control node |
| `community.vmware collection not found` | Run `ansible-galaxy collection install -r requirements.yml` |
| No Linux VMs found | Check `linux_guest_id_patterns` in snapshot role defaults; verify guest IDs in ESXi UI |
| SSH connection refused | Check `ansible_user` and `ansible_ssh_private_key_file` in inventory |
| Certificate errors against ESXi | Import the issuing CA into the control node trust store; keep TLS verification enabled |

Credential requirements: [private deployment credentials](docs/credential-security.md).
