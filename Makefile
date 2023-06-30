# Also needs to be updated in galaxy.yml
VERSION = 0.5.0

TEST_ARGS ?= --docker --color

clean:
	rm -f operator_sdk-util-${VERSION}.tar.gz
	rm -rf ansible_collections
	rm -rf tests/output

build: clean
	ansible-galaxy collection build

release: build
	ansible-galaxy collection publish operator_sdk-util-${VERSION}.tar.gz --api-key ${GALAXY_API_KEY}

install: build
	ansible-galaxy collection install -p ansible_collections operator_sdk-util-${VERSION}.tar.gz

test-lint: install
	ansible-lint --profile safety

test-sanity: test-lint
	set -x && cd ansible_collections/operator_sdk/util && ansible-test sanity -v $(TEST_ARGS)

test-molecule: install
	molecule test
