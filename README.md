# Ansible Collection - operator_sdk.util

A collection of Ansible assets for use with Ansible-based operators
built with the [operator-sdk](https://github.com/operator-framework/operator-sdk/).

 https://galaxy.ansible.com/operator_sdk/util


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

### Tests

To run sanity tests locally, run

```
make test-sanity
```

To run the molecule integration tests, ensure you have molecule and the openshift python client installed and run

```
make test-molecule
```

### Build and Publish Collection

Before building the collection, edit `galaxy.yml` and update the
version.

**Build the collection:**

```
$ make build
```

**Publish the collection:**

```
$ GALAXY_API_KEY=... make publish
```

You can find your galaxy api key at https://galaxy.ansible.com/me/preferences
