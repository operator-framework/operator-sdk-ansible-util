# Ansible Collection - operator_sdk.util

A collection of Ansible assets for use with Ansible-based operators
built with the operator-sdk.

https://github.com/operator-framework/operator-sdk/

## Installation

#### From Galaxy

```
ansible-galaxy collection install operator_sdk.util
```

#### Local

```
ansible-galaxy collection install operator_sdk-util-0.0.1.tar.gz -p ~/.ansible/collections
```

## Developer Docs

### Build and Publish Collection

Before building the collection, edit `galaxy.yml` and update the
version.

**Build the collection:**

```
$ ansible-galaxy collection build
```

**Publish the collection:**

```
ansible-galaxy collection publish operator_sdk-util-0.0.0.tar.gz --api-key=$GALAXY_API_KEY
```
