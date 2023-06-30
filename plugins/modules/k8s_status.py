#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function


__metaclass__ = type

ANSIBLE_METADATA = {
    "metadata_version": "1.1",
    "status": ["preview"],
    "supported_by": "community",
}

DOCUMENTATION = """

module: k8s_status

short_description: Update the status for a Kubernetes API resource

version_added: "0.0.1"

author: "Fabian von Feilitzsch (@fabianvf)"

description:
  - Sets the status field on a Kubernetes API resource. Only should be used if you are using Ansible to
    implement a controller for the resource being modified.

extends_documentation_fragment:
    - operator_sdk.util.osdk_auth_options
    - operator_sdk.util.osdk_name_options

options:
  status:
    type: dict
    description:
    - 'An object containing key: value pairs that will be set on the status object of the specified resource.'
    - One of I(status) or I(conditions) is required.
    - If you use I(conditions), you cannot include a conditions field beneath status.
    - If you add a conditions field under status, it will not be validated like conditions specified through I(conditions) are.
  conditions:
    type: list
    elements: dict
    description:
    - A list of condition objects that will be set on the status.conditions field of the specified resource.
    - Unless I(replace) is C(true) the specified conditions will be merged with the conditions already set on the status field of the specified resource.
    - Each element in the list will be validated according to the conventions specified in the
      [Kubernetes API conventions document](https://github.com/kubernetes/community/blob/master/contributors/devel/api-conventions.md#spec-and-status).
    - One of I(status) or I(conditions) is required.'
    suboptions:
      type:
        description:
          - The type of the condition. Used to identify it uniquely.
        type: str
        required: yes
      status:
        description:
          - The status of the condition.
        type: str
        choices:
          - "True"
          - "False"
          - "Unknown"
        required: yes
      reason:
        description:
          - The reason this condition has a particular status. A single, CamelCase word.
        type: str
      message:
        description:
          - A human readable message explaining the status of this condition.
        type: str
      lastHeartbeatTime:
        description:
          - An RFC3339 formatted datetime string
        type: str
      lastTransitionTime:
        description:
          - An RFC3339 formatted datetime string
        type: str
  replace:
    description:
    - If set to C(True), the status will be set using `PUT` rather than `PATCH`, replacing the full status object.
    default: false
    aliases:
      - force
    type: bool
  replace_lists:
    description:
    - If set to C(True), any lists except `conditions` will be fully replaced if mismatched.
    default: false
    type: bool

requirements:
    - "python >= 3.7"
    - "kubernetes >= 25.3.0"
"""

EXAMPLES = """
- name: Set custom status fields on TestCR
  k8s_status:
    api_version: apps.example.com/v1alpha1
    kind: TestCR
    name: my-test
    namespace: testing
    status:
      hello: world
      custom: entries

- name: Update the standard condition of an Ansible Operator
  k8s_status:
    api_version: apps.example.com/v1alpha1
    kind: TestCR
    name: my-test
    namespace: testing
    conditions:
      - type: Running
        status: "True"
        reason: MigrationStarted
        message: "Migration from v2 to v3 has begun"
        lastTransitionTime: "{{ lookup('pipe', 'date --rfc-3339 seconds') }}"

- name: |
    Create custom conditions. WARNING: The default Ansible Operator status management
    will never overwrite custom conditions, so they will persist indefinitely. If you
    want the values to change or be removed, you will need to clean them up manually.
  k8s_status:
    api_version: apps.example.com/v1alpha1
    kind: TestCR
    name: my-test
    namespace: testing
    conditions:
      - type: Available
        status: "False"
        reason: PingFailed
        message: "The service did not respond to a ping"
"""

RETURN = """
result:
  description:
  - If a change was made, will return the patched object, otherwise returns the instance object.
  returned: success
  type: complex
  contains:
     api_version:
       description: The versioned schema of this representation of an object.
       returned: success
       type: str
     kind:
       description: Represents the REST resource this object represents.
       returned: success
       type: str
     metadata:
       description: Standard object metadata. Includes name, namespace, annotations, labels, etc.
       returned: success
       type: dict
     spec:
       description: Specific attributes of the object. Will vary based on the I(api_version) and I(kind).
       returned: success
       type: dict
     status:
       description: Current status details for the object.
       returned: success
       type: dict
"""

import re
import copy
import traceback

from ansible.module_utils.basic import AnsibleModule, missing_required_lib
from ansible.module_utils._text import to_native

K8S_IMP_ERR = None
try:
    from ansible_collections.operator_sdk.util.plugins.module_utils.api_utils import (get_api_client, find_resource)
    from ansible_collections.operator_sdk.util.plugins.module_utils.args_common import (
        AUTH_ARG_SPEC,
        NAME_ARG_SPEC
    )
    import kubernetes
    from kubernetes.dynamic.exceptions import DynamicApiError
    HAS_K8S_MODULE_HELPER = True
    k8s_import_exception = None
except ImportError as e:
    HAS_K8S_MODULE_HELPER = False
    k8s_import_exception = e
    K8S_IMP_ERR = traceback.format_exc()

CONDITIONS_ARG_SPEC = {
    "type": "list",
    "required": False,
    "elements": "dict",
    "options": {
        "type": {"type": "str", "required": True},
        "status": {"type": "str", "required": True, "choices": ["True", "False", "Unknown"]},
        "reason": {"type": "str"},
        "message": {"type": "str"},
        "lastHeartbeatTime": {"type": "str"},
        "lastTransitionTime": {"type": "str"},
    }
}

STATUS_ARG_SPEC = {
    "status": {"type": "dict", "required": False},
    "conditions": CONDITIONS_ARG_SPEC,
    "replace": {"type": "bool", "required": False, "default": False, "aliases": ["force"]},
    "replace_lists": {"type": "bool", "required": False, "default": False},
}


def main():
    KubernetesAnsibleStatusModule().execute_module()


def format_api_error(exc):
    return dict(
        status=exc.status,
        reason=exc.reason,
        body=exc.body,
    )


def validate_conditions(conditions):

    VALID_KEYS = [
        "type",
        "status",
        "reason",
        "message",
        "lastHeartbeatTime",
        "lastTransitionTime",
    ]
    REQUIRED = ["type", "status"]
    CAMEL_CASE = re.compile(r"^(?:[A-Z]*[a-z]*)+$")
    RFC3339_datetime = re.compile(
        r"^\d{4}-\d\d-\d\d[T ]\d\d:\d\d(:\d\d)?(\.\d+)?(([+-]\d\d:\d\d)|Z)$"
    )

    def validate_condition(condition):
        if not isinstance(condition, dict):
            raise ValueError("`conditions` must be a list of objects")
        if isinstance(condition.get("status"), bool):
            condition["status"] = "True" if condition["status"] else "False"

        for key in condition.copy().keys():
            if key not in VALID_KEYS:
                raise ValueError(
                    "{0} is not a valid field for a condition, accepted fields are {1}".format(
                        key, VALID_KEYS
                    )
                )
            # remove keys with None value, to be able to compare with updated_old_status
            if condition[key] is None:
                del condition[key]
        for key in REQUIRED:
            if not condition.get(key):
                raise ValueError("Condition `{0}` must be set".format(key))

        if condition["status"] not in ["True", "False", "Unknown"]:
            raise ValueError(
                "Condition 'status' must be one of [\"True\", \"False\", \"Unknown\"], not {0}".format(
                    condition["status"]
                )
            )

        if condition.get("reason") and not re.match(CAMEL_CASE, condition["reason"]):
            raise ValueError("Condition 'reason' must be a single, CamelCase word")

        for key in ["lastHeartbeatTime", "lastTransitionTime"]:
            if condition.get(key) and not re.match(RFC3339_datetime, condition[key]):
                raise ValueError(
                    "'{0}' must be an RFC3339 compliant datetime string".format(key)
                )

        return condition

    return [validate_condition(c) for c in conditions]


class KubernetesAnsibleStatusModule(AnsibleModule):

    def __init__(self, *args, **kwargs):
        super(KubernetesAnsibleStatusModule, self).__init__(*args, argument_spec=self.argspec, **kwargs)
        if not HAS_K8S_MODULE_HELPER:
            self.fail_json(
                msg=missing_required_lib('kubernetes'),
                exception=K8S_IMP_ERR,
                error=to_native(k8s_import_exception))
        self.kubernetes_version = kubernetes.__version__

        self.kind = self.params.get("kind")
        self.api_version = self.params.get("api_version")
        self.name = self.params.get("name")
        self.namespace = self.params.get("namespace")
        self.replace_status = self.params.get("replace")
        self.replace_lists = self.params.get("replace_lists")

        self.status = self.params.get("status") or {}
        try:
            self.conditions = validate_conditions(self.params.get("conditions") or [])
        except ValueError as exc:
            self.fail_json(msg="The specified conditions failed to validate", error=to_native(exc))

        if self.conditions and self.status and self.status.get("conditions"):
            self.fail_json(msg="You cannot specify conditions in both the 'status' and 'conditions' parameters")

        if self.conditions:
            self.status["conditions"] = self.conditions

    def execute_module(self):
        self.client = get_api_client(self)

        resource = find_resource(self.client, self.kind, self.api_version)
        if resource is None:
            self.fail_json(msg='Failed to find exact match for {0}.{1} by [kind, name, singularName, shortNames]'.format(self.api_version, self.kind))

        if not resource.subresources or "status" not in resource.subresources:
            self.fail_json(
                msg="Resource {0}.{1} does not support the status subresource".format(
                    resource.api_version, resource.kind
                )
            )

        try:
            instance = resource.get(name=self.name, namespace=self.namespace).to_dict()
        except DynamicApiError as exc:
            self.fail_json(
                msg="Failed to retrieve requested object",
                error=format_api_error(exc),
            )
        # Make sure status is at least initialized to an empty dict
        instance["status"] = instance.get("status", {})

        if self.replace_status:
            self.exit_json(**self.replace(resource, instance))
        else:
            self.exit_json(**self.patch(resource, instance))

    def replace(self, resource, instance):
        if self.status == instance["status"]:
            return {"result": instance, "changed": False}
        instance["status"] = self.status
        try:
            result = (resource.status.replace(body=instance).to_dict(),)
        except DynamicApiError as exc:
            self.fail_json(
                msg="Failed to replace status: {0}".format(exc), error=format_api_error(exc)
            )

        return {"result": result, "changed": True}

    def patch(self, resource, instance):
        # if new status is empty, return with no changes
        if not self.status:
            return {"result": instance, "changed": False}

        # save original instance object
        original_instance = copy.deepcopy(instance)

        # merge conditions between original object and new status.
        # `merge_status_conditions` will update, append or preserve conditions
        # checking if any one has transition or not
        instance["status"] = self.merge_status_conditions(instance["status"], self.status)

        # it there are no modifications, return with no changes
        if self.object_contains(original_instance["status"], instance["status"]):
            return {"result": original_instance, "changed": False}

        # patch
        try:
            result = resource.status.patch(
                body=instance, content_type="application/merge-patch+json"
            ).to_dict()
        except DynamicApiError as exc:
            self.fail_json(
                msg="Failed to replace status: {0}".format(exc), error=format_api_error(exc)
            )

        return {"result": result, "changed": True}

    def merge_status_conditions(self, old_status, new_status):
        old_conditions = old_status.get("conditions", [])
        new_conditions = new_status.get("conditions", [])
        if not (old_conditions and new_conditions):
            return new_status

        merged = copy.deepcopy(old_conditions)

        for condition in new_conditions:
            idx = self.get_condition_idx(merged, condition["type"])
            if idx is not None:
                # if new condition has transitioned, save; otherwise preserve old condition
                if self.has_condition_transitioned(merged[idx], condition):
                    merged[idx] = condition
            else:
                merged.append(condition)
        new_status["conditions"] = merged
        return new_status

    def get_condition_idx(self, conditions, name):
        for i, condition in enumerate(conditions):
            if condition.get("type") == name:
                return i
        return None

    def has_condition_transitioned(self, old_condition, new_condition):
        # return true if any value in condition has changed, ignoring `lastTransitionTime`
        return any(
            k != "lastTransitionTime" and v != old_condition.get(k, None) for (k, v) in new_condition.items()
        )

    def object_contains(self, obj, subset):
        def dict_is_subset(obj, subset):
            return all(
                (
                    mapping["default"]
                    if self.replace_lists and isinstance(obj.get(k), list) and k != "conditions"
                    else mapping.get(type(obj.get(k)), mapping["default"])
                )(obj.get(k), v)
                for (k, v) in subset.items()
            )

        def list_is_subset(obj, subset):
            return all(item in obj for item in subset)

        def values_match(obj, subset):
            return obj == subset

        mapping = {
            dict: dict_is_subset,
            list: list_is_subset,
            tuple: list_is_subset,
            "default": values_match,
        }

        return dict_is_subset(obj, subset)

    @property
    def argspec(self):
        args = {}
        args.update(AUTH_ARG_SPEC)
        args.update(STATUS_ARG_SPEC)
        args.update(NAME_ARG_SPEC)
        return args


if __name__ == "__main__":
    main()
