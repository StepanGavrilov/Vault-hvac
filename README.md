# Vault

# Description
+ Quickstart for Vault in container
+ Quickstart for hvac
---

# StartUP

- Get status

```bash
vault status
```

```bash
Key                Value
---                -----
Seal Type          shamir
Initialized        false
Sealed             true
Total Shares       0
Threshold          0
Unseal Progress    0/0
Unseal Nonce       n/a
Version            1.9.4
Storage Type       file
HA Enabled         false
```

- InIt

```bash
vault operator init
```

```bash
Unseal Key 1: zrxvJMpk6KPZaVmMihy+/E4mS1nvY9VO1GHHH7RqfABQ
Unseal Key 2: aM9JqWfDqVl+rboFHL7xEX2pSzpGaXhkcRC3xsN4Rtoa
Unseal Key 3: E8QeyeIJOboHmHsRSAd9S/ADNINN+v/8OhdqHKKrhefD
Unseal Key 4: hSP5Fyzap3ipstfXrP6ouZkqyvZ0RDWViJB+KWGDt0Nw
Unseal Key 5: JOj6yk0lHmXaTxZ5c+EBbSbH471gNH5A50zKdURckKjR

Initial Root Token: hvs.vWbbxKUxsKx8vT6AIFZ9P4tu
```

- unseal (need 3 time for unseal)

```bash
vault operator unseal
> OCvOBtAZitQjOR0BHEpGbpE+GdE6c8BXCnZn9LE9zyFt
```

```bash
Key                Value
---                -----
Seal Type          shamir
Initialized        true
Sealed             true
Total Shares       5
Threshold          3
Unseal Progress    1/3
Unseal Nonce       f05249c7-216c-0da4-3a83-a64a5a16c5df
Version            1.9.4
Storage Type       file
HA Enabled         false
```

- unsealed

```bash
Key             Value
---             -----
Seal Type       shamir
Initialized     true
Sealed          false
Total Shares    5
Threshold       3
Version         1.9.4
Storage Type    file
Cluster Name    vault-cluster-999bd97f
Cluster ID      ccf82654-9dcb-6afc-ffce-7e7baf9bf59e
HA Enabled      false
```

- login with root token (revoke this token!)

```bash
vault login hvs.vWbbxKUxsKx8vT6AIFZ9P4tu
```

```bash
Success! You are now authenticated. The token information displayed below
is already stored in the token helper. You do NOT need to run "vault login"
again. Future Vault requests will automatically use this token.

Key                  Value
---                  -----
token                s.3Tkl12W9BddB2Qc8T8SPTMl8
token_accessor       6A0iBzma7qYFce5uRRBobvtz
token_duration       ∞
token_renewable      false
token_policies       ["root"]
identity_policies    []
policies             ["root"]
```

- login default (127.0.0.1:8000 default) with token: master

![Untitled](Vault%20aceee2ca0bf3474385ad40f60d17dbfa/Untitled.png)

- get all secrets in vault

```bash
vault secrets list
```

```bash
Path          Type         Accessor              Description
----          ----         --------              -----------
cubbyhole/    cubbyhole    cubbyhole_ed3d4963    per-token private secret storage
identity/     identity     identity_de9bace3     identity store
sys/          system       system_ea1dd8ec       system endpoints used for control, policy and debuggin
```

- enable kv

```bash
vault secrets enable kv-v2
```

```bash
Success! Enabled the kv-v2 secrets engine at: kv-v2/
```

list

```bash
Path          Type         Accessor              Description
----          ----         --------              -----------
cubbyhole/    cubbyhole    cubbyhole_ed3d4963    per-token private secret storage
identity/     identity     identity_de9bace3     identity store
kv-v2/        kv           kv_c7bb6a04           n/a
sys/          system       system_ea1dd8ec       system endpoints used for control, policy and debugging
```

- set a secret

```bash
vault kv put kv-v2/app/service_db_1 host=localhost
```

```bash
Key                Value
---                -----
created_time       2023-03-14T10:07:20.641003007Z
custom_metadata    <nil>
deletion_time      n/a
destroyed          false
version            1
```

- get all secrets from app

```bash
vault kv list kv-v2/app
```

```bash
Keys
----
service_db_1
```

- retrive secret

```bash
vault kv get kv-v2/app/service_db_1
```

```bash
======= Metadata =======
Key                Value
---                -----
created_time       2023-03-14T10:07:20.641003007Z
custom_metadata    <nil>
deletion_time      n/a
destroyed          false
version            1

==== Data ====
Key     Value
---     -----
host    localhost
```

---

# Auth

- enable auth

```bash
vault auth enable userpass
```

```bash
Success! Enabled userpass auth method at: userpass/
```

- policy list

```bash
vault policy list
```

```bash
default
root
```

- retrieve police

```bash
vault policy read default
```

```bash
# Allow tokens to look up their own properties
path "auth/token/lookup-self" {
    capabilities = ["read"]
}

# Allow tokens to renew themselves
path "auth/token/renew-self" {
    capabilities = ["update"]
}

# Allow tokens to revoke themselves
path "auth/token/revoke-self" {
    capabilities = ["update"]
}

# Allow a token to look up its own capabilities on a path
path "sys/capabilities-self" {
    capabilities = ["update"]
}

# Allow a token to look up its own entity by id or name
path "identity/entity/id/{{identity.entity.id}}" {
  capabilities = ["read"]
}
path "identity/entity/name/{{identity.entity.name}}" {
  capabilities = ["read"]
}

...
```

- userpass

```bash
vault write auth/userpass/users/dev_postgre password=admin polices=kv-dev-postgres
```

```bash
{
  "path": {
    "dev/postgres/*": {
      "capabilities": [
        "read",
        "list"
      ]
    },
    "sys/mounts": {
      "capabilities": [
        "read"
      ]
    }
  }
}
```

### Mount point

![Untitled](Vault%20aceee2ca0bf3474385ad40f60d17dbfa/Untitled%201.png)