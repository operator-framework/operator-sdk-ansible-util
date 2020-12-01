#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function


__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''

module: k8s_status

short_description: Update the status for a Kubernetes API resource

version_added: "0.0.1"

author: "Fabian von Feilitzsch (@fabianvf)"

description:
  - Sets the status field on a Kubernetes API resource. Only should be used if you are using Ansible to
    implement a controller for the resource being modified.

extends_documentation_fragment:
  - community.kubernetes.k8s_auth_options
  - community.kubernetes.k8s_name_options

options:
  status:
    type: dict
    description:
    - 'An object containing key: value pairs that will be set on the status object of the specified resource.'
    - One of I(status) or I(conditions) is required.
  conditions:
    type: list
    description:
    - A list of condition objects that will be set on the status.conditions field of the specified resource.
    - Unless I(force) is C(true) the specified conditions will be merged with the conditions already set on the status field of the specified resource.
    - Each element in the list will be validated according to the conventions specified in the
      [Kubernetes API conventions document](https://github.com/kubernetes/community/blob/master/contributors/devel/api-conventions.md#spec-and-status).
    - 'The fields supported for each condition are:
      `type` (required),
      `status` (required, one of "True", "False", "Unknown"),
      `reason` (single CamelCase word),
      `message`,
      `lastHeartbeatTime` (RFC3339 datetime string), and
      `lastTransitionTime` (RFC3339 datetime string).'
    - One of I(status) or I(conditions) is required.'
  force:
    description:
    - If set to C(True), the status will be set using `PUT` rather than `PATCH`, replacing the full status object.
    default: false
    type: bool

requirements:
    - "python >= 3.7"
    - "openshift >= 0.8.1"
    - "PyYAML >= 3.11"
'''

EXAMPLES = '''
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
      lastTransitionTime: "{{ ansible_date_time.iso8601 }}"

- name: |
    Create custom conditions. WARNING: The default Ansible Operator status management
    will never overwrite custom conditions, so they will persist indefinitely. If you
    want the values to change or be removed, you will need to clean them up manually.
  k8s_status:
    conditions:
    - type: Available
      status: "False"
      reason: PingFailed
      message: "The service did not respond to a ping"

'''

RETURN = '''
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
'''

import re
import copy
import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native

try:
    from ansible_collections.community.kubernetes.plugins.module_utils.common import (
        AUTH_ARG_SPEC,
        COMMON_ARG_SPEC,
        NAME_ARG_SPEC,
        KubernetesAnsibleModule,
    )
    HAS_KUBERNETES_COLLECTION = True
except ImportError as e:
    HAS_KUBERNETES_COLLECTION = False
    k8s_collection_import_exception = e
    K8S_COLLECTION_ERROR = traceback.format_exc()
    KubernetesAnsibleModule = AnsibleModule
    AUTH_ARG_SPEC = NAME_ARG_SPEC = COMMON_ARG_SPEC = {}
try:
    from openshift.dynamic.exceptions import DynamicApiError
except ImportError:
    class KubernetesException(Exception):
        pass


def condition_array(conditions):

    VALID_KEYS = ['type', 'status', 'reason', 'message', 'lastHeartbeatTime', 'lastTransitionTime']
    REQUIRED = ['type', 'status']
    CAMEL_CASE = re.compile(r'^(?:[A-Z]*[a-z]*)+$')
    RFC3339_datetime = re.compile(r'^\d{4}-\d\d-\d\dT\d\d:\d\d(:\d\d)?(\.\d+)?(([+-]\d\d:\d\d)|Z)$')

    def validate_condition(condition):
        if not isinstance(condition, dict):
            raise ValueError('`conditions` must be a list of objects')
        if isinstance(condition.get('status'), bool):
            condition['status'] = 'True' if condition['status'] else 'False'

        for key in condition.keys():
            if key not in VALID_KEYS:
                raise ValueError('{0} is not a valid field for a condition, accepted fields are {1}'.format(key, VALID_KEYS))
        for key in REQUIRED:
            if not condition.get(key):
                raise ValueError('Condition `{0}` must be set'.format(key))

        if condition['status'] not in ['True', 'False', 'Unknown']:
            raise ValueError('Condition `status` must be one of ["True", "False", "Unknown"], not {0}'.format(condition['status']))

        if condition.get('reason') and not re.match(CAMEL_CASE, condition['reason']):
            raise ValueError('Condition `reason` must be a single, CamelCase word')

        for key in ['lastHeartBeatTime', 'lastTransitionTime']:
            if condition.get(key) and not re.match(RFC3339_datetime, condition[key]):
                raise ValueError('`{0}` must be a RFC3339 compliant datetime string'.format(key))

        return condition

    return [validate_condition(c) for c in conditions]


STATUS_ARG_SPEC = {
    'status': {
        'type': 'dict',
        'required': False
    },
    'conditions': {
        'type': condition_array,
        'required': False
    }
}


def main():
    KubernetesAnsibleStatusModule().execute_module()


class KubernetesAnsibleStatusModule(KubernetesAnsibleModule):

    def __init__(self, *args, **kwargs):
        if not HAS_KUBERNETES_COLLECTION:
            self.fail_json(
                msg="The community.kubernetes collection must be installed",
                exception=K8S_COLLECTION_ERROR,
                error=to_native(k8s_collection_import_exception)
            )
        KubernetesAnsibleModule.__init__(
            self, *args,
            supports_check_mode=True,
            **kwargs
        )
        self.kind = self.params.get('kind')
        self.api_version = self.params.get('api_version')
        self.name = self.params.get('name')
        self.namespace = self.params.get('namespace')
        self.force = self.params.get('force')

        self.status = self.params.get('status') or {}
        self.conditions = self.params.get('conditions') or []

        if self.conditions and self.status and self.status.get('conditions'):
            raise ValueError("You cannot specify conditions in both the `status` and `conditions` parameters")

        if self.conditions:
            self.status['conditions'] = self.conditions

    def execute_module(self):
        self.client = self.get_api_client()

        resource = self.find_resource(self.kind, self.api_version, fail=True)
        if 'status' not in resource.subresources:
            self.fail_json(msg='Resource {0}.{1} does not support the status subresource'.format(resource.api_version, resource.kind))

        try:
            instance = resource.get(name=self.name, namespace=self.namespace).to_dict()
        except DynamicApiError as exc:
            self.fail_json(msg='Failed to retrieve requested object: {0}'.format(exc),
                           error=exc.summary())
        # Make sure status is at least initialized to an empty dict
        instance['status'] = instance.get('status', {})

        if self.force:
            self.exit_json(**self.replace(resource, instance))
        else:
            self.exit_json(**self.patch(resource, instance))

    def replace(self, resource, instance):
        if self.status == instance['status']:
            return {'result': instance, 'changed': False}
        instance['status'] = self.status
        try:
            result = resource.status.replace(body=instance).to_dict(),
        except DynamicApiError as exc:
            self.fail_json(msg='Failed to replace status: {0}'.format(exc), error=exc.summary())

        return {
            'result': result,
            'changed': True
        }

    def clean_last_transition_time(self, status):
        '''clean_last_transition_time removes lastTransitionTime attribute from each status.conditions[*] (from old conditions).
        It returns copy of status with updated conditions. Copy of status is returned, because if new conditions
        are subset of old conditions, then module would return conditions without lastTransitionTime. Updated status
        should be used only for check in object_contains function, not for next updates, because otherwise it can create
        a mess with lastTransitionTime attribute.

        If new conditions don't contain lastTransitionTime and they are different from old conditions
        (e.g. they have different status), conditions are updated and kubernetes should sets lastTransitionTime
        field during update. If new conditions contain lastTransitionTime, then conditions are updated.

        Parameters:
          status (dict): dictionary, which contains conditions list

        Returns:
          dict: copy of status with updated conditions
        '''
        updated_old_status = copy.deepcopy(status)

        for item in updated_old_status.get('conditions', []):
            if 'lastTransitionTime' in item:
                del item['lastTransitionTime']

        return updated_old_status

    def patch(self, resource, instance):
        # Remove lastTransitionTime from status.conditions[*] and use updated_old_status only for check in object_contains function.
        # Updates of conditions should be done only with original data not with updated_old_status.
        updated_old_status = self.clean_last_transition_time(instance['status'])
        if self.object_contains(updated_old_status, self.status):
            return {'result': instance, 'changed': False}
        instance['status'] = self.merge_status(instance['status'], self.status)
        try:
            result = resource.status.patch(body=instance, content_type='application/merge-patch+json').to_dict()
        except DynamicApiError as exc:
            self.fail_json(msg='Failed to replace status: {0}'.format(exc), error=exc.summary())

        return {
            'result': result,
            'changed': True
        }

    def merge_status(self, old, new):
        old_conditions = old.get('conditions', [])
        new_conditions = new.get('conditions', [])
        if not (old_conditions and new_conditions):
            return new

        merged = copy.deepcopy(old_conditions)

        for condition in new_conditions:
            idx = self.get_condition_idx(merged, condition['type'])
            if idx is not None:
                merged[idx] = condition
            else:
                merged.append(condition)
        new['conditions'] = merged
        return new

    def get_condition_idx(self, conditions, name):
        for i, condition in enumerate(conditions):
            if condition.get('type') == name:
                return i
        return None

    def object_contains(self, obj, subset):
        def dict_is_subset(obj, subset):
            return all([mapping.get(type(obj.get(k)), mapping['default'])(obj.get(k), v) for (k, v) in subset.items()])

        def list_is_subset(obj, subset):
            return all(item in obj for item in subset)

        def values_match(obj, subset):
            return obj == subset

        mapping = {
            dict: dict_is_subset,
            list: list_is_subset,
            tuple: list_is_subset,
            'default': values_match
        }

        return dict_is_subset(obj, subset)

    @property
    def argspec(self):
        args = copy.deepcopy(COMMON_ARG_SPEC)
        args.pop('state')
        args.update(AUTH_ARG_SPEC)
        args.update(STATUS_ARG_SPEC)
        args.update(NAME_ARG_SPEC)
        return args


if __name__ == '__main__':
    main()
