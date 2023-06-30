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

To run the molecule integration tests, ensure you have molecule and the kubernetes python client installed and run

```
make test-molecule
```

### Release Docs

To perform a release, do the following steps:
1. Branch:
   - If this is a z-stream bump, checkout the minor version release branch.
   - If this is a minor version bump, create a new branch ``release-<semantic-version-number>``. For example: ``release-0.3``.


2. Change the version in Makefile and galaxy.yml to the new semantic version.


3. Run ``make build`` to generate a zip of the release.


4. If it's a minor version bump, open a pull request against the master branch of the main repository.


5. Once the pull request to master merged, push a tag that named by the semantic version number of this release. Ex: v0.3.1


6. Draft a release on that tag. The release notes should list the changes since the last release, as well as a zip of the current version.


7. Publish the collection using:
```
$ make release GALAXY_API_KEY=...
```

You can find your galaxy api key at https://galaxy.ansible.com/me/preferences
