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

module: k8s_event

short_description: Create Kubernetes Events.

version_added: "0.0.1"

author: "Venkat Ramaraju (@VenkatRamaraju)"

description:
  -  Allows users to more easily emit events for their managed objects.

extends_documentation_fragment:
    - operator_sdk.util.osdk_auth_options

options:
  state:
    type: str
    description:
    - Determines whether an object should be created, patched or deleted. If set to "present" a new object will
      be created if it does not already exist. If the object already exists, it will be patched if the attributes
      differ from the new specifications. If attributes do not differ, no changes will be made. If set to "absent",
      the object will be deleted if it already exists. If it does not exist, no changes are made.
    - By default, state is set to "present".
    choices:
      - "present"
      - "absent"
    default: "present"
  name:
    type: str
    required: true
    description:
    - The unique name of the resource.
  namespace:
    type: str
    required: true
    description:
    - The space within which each name must be unique.
    - Not all objects are required to be scoped to a namespace.
  merge_type:
    type: list
    description:
    - Determines whether to override the default patch merge type with the specified.
    - The default is strategic merge.
    elements: str
    choices:
      - "json"
      - "merge"
      - "strategic-merge"
  message:
    type: str
    required: true
    description:
    - A human-readable description of the status of this operation.
  reason:
    type: str
    required: true
    description:
    - A human-readable description of the status of this operation.
  reportingComponent:
    type: str
    description:
    - Name of the controller that emitted this Event, e.g. kubernetes.io/kubelet.
  type:
    type: str
    description:
    - Type of this event. New types could be added in the future.
    choices:
      - "Normal"
      - "Warning"
  source:
    type: dict
    description: EventSource
    suboptions:
      component:
        description: Component for reporting this Event.
        type: str
        required: true
  involvedObject:
    type: dict
    description: The object that this event is about.
    suboptions:
      apiVersion:
        description: The apiVersion.
        type: str
        required: true
      kind:
        description: Resource kind.
        type: str
        required: true
      name:
        description: Resource name.
        type: str
        required: true
      namespace:
        description: Resource namespace.
        type: str
        required: true
  appendTimestamp:
    type: bool
    description: Event name should have timestamp appended to it

requirements:
  - python >= 2.7
  - kubernetes >= 25.3.0
"""

EXAMPLES = """
- name: Create Kubernetes Event
  k8s_event:
    state: present
    name: test-k8s-event
    namespace: default
    message: Event created
    merge-type: strategic-merge
    reason: Testing event creation
    reportingComponent: Reporting components
    appendTimestamp: true
    type: Normal
    source:
      component: test-component
    involvedObject:
      apiVersion: v1
      kind: Service
      name: test-k8s-events
      namespace: default
"""

RETURN = """
result:
  description:
  - If a change was made, will return the patched object, otherwise returns the instance object.
  returned: success
  type: complex
  contains:
   namespace:
     description: Namespace defines the space within which each name must be unique
     returned: success
     type: str
   name:
     description: The unique name of the resource.
     returned: success
     type: str
   count:
     description: Count of event occurrences
     returned: success
     type: int
   message:
     description: A human-readable description of the status of this operation.
     returned: success
     type: dict
   kind:
     description: Always 'Event'.
     returned: success
     type: str
   firstTimestamp:
     description: Timestamp of first occurrence of Event
     returned: success
     type: str
   reason:
     description: Machine understandable string that gives the reason for the transition into the object's status.
     returned: success
     type: dict
   reportingComponent:
     description: Name of the controller that emitted this Event
     returned: success
     type: str
   type:
     description: Type of this event. New types could be added in the future.
     returned: success
     type: str
   source:
     description: The component reporting this event.
     returned: success
     type: dict
   lastTimestamp:
     description: Timestamp of last occurrence of Event
     returned: success
     type: str
   involvedObject:
     description: The object that this event is about.
     returned: success
     type: dict
"""

import copy
import datetime
import traceback
from ansible.module_utils.basic import AnsibleModule

K8S_IMP_ERR = None
try:
    from ansible_collections.operator_sdk.util.plugins.module_utils.args_common import AUTH_ARG_SPEC
    from ansible_collections.operator_sdk.util.plugins.module_utils.api_utils import (
        get_api_client,
        find_resource,
    )
    import kubernetes
    HAS_K8S_MODULE_HELPER = True
    k8s_import_exception = None
except ImportError as e:
    HAS_K8S_MODULE_HELPER = False
    k8s_import_exception = e
    K8S_IMP_ERR = traceback.format_exc()

EVENT_ARG_SPEC = {
    "state": {"default": "present", "choices": ["present", "absent"]},
    "name": {"required": True},
    "namespace": {"required": True},
    "merge_type": {"type": "list", "elements": "str", "choices": ["json", "merge", "strategic-merge"]},
    "message": {"type": "str", "required": True},
    "reason": {"type": "str", "required": True},
    "reportingComponent": {"type": "str"},
    "type": {"choices": ["Normal", "Warning"]},
    "appendTimestamp": {"type": "bool"},
    "source": {
        "type": "dict",
        "options": {
            "component": {"type": "str", "required": True}
        }
    },
    "involvedObject": {
        "type": "dict",
        "options": {
            "apiVersion": {"type": "str", "required": True},
            "kind": {"type": "str", "required": True},
            "name": {"type": "str", "required": True},
            "namespace": {"type": "str", "required": True},
        }
    }
}


class KubernetesEvent(AnsibleModule):
    def __init__(self, *args, **kwargs):
        super(KubernetesEvent, self).__init__(*args, argument_spec=self.argspec, **kwargs)
        self.client = None

    @property
    def argspec(self):
        """ argspec property builder """
        argumentSpec = copy.deepcopy(AUTH_ARG_SPEC)
        argumentSpec.update(EVENT_ARG_SPEC)
        return argumentSpec

    def execute_module(self):
        self.client = get_api_client(self)
        now = datetime.datetime.now(datetime.timezone.utc)
        if self.params['appendTimestamp']:
            self.params["name"] = self.params["name"] + "." + str(now)

        metadata = {"name": self.params.get("name"), "namespace": self.params.get("namespace")}
        resource = find_resource(self.client, "Event", "v1")
        v1_events = self.client.resources.get(api_version="v1", kind='Event')
        event = {
            "kind": "Event",
            "eventTime": None,
            "message": self.params.get("message"),
            "metadata": metadata,
            "reason": self.params.get("reason"),
            "reportingComponent": self.params.get("reportingComponent"),
            "source": self.params.get("source"),
            "type": self.params.get("type"),
        }

        if self.params['appendTimestamp']:
            try:
                created_event = v1_events.create(body=event, namespace=self.params.get("namespace"))
                return dict(result=created_event.to_dict(), changed=True)
            except Exception as err:
                self.fail_json(msg="Unable to create event: {0}".format(err))

        prior_event = None
        try:
            prior_event = resource.get(
                name=metadata["name"],
                namespace=metadata["namespace"])
        except kubernetes.dynamic.exceptions.NotFoundError:
            pass

        prior_count = 1
        rfc = now.isoformat()
        first_timestamp = rfc
        last_timestamp = rfc

        if prior_event and prior_event["reason"] == self.params['reason']:
            prior_count = prior_event["count"] + 1
            first_timestamp = prior_event["firstTimestamp"]
            last_timestamp = rfc

        involved_obj = self.params.get("involvedObject")
        if involved_obj:
            try:
                involved_object_resource = find_resource(self.client, involved_obj["kind"], involved_obj.get("apiVersion", "v1"))
                if involved_object_resource:
                    api_involved_object = involved_object_resource.get(
                        name=involved_obj["name"], namespace=involved_obj["namespace"])

                    involved_obj["uid"] = api_involved_object["metadata"]["uid"]
                    involved_obj["resourceVersion"] = api_involved_object["metadata"]["resourceVersion"]

            except kubernetes.dynamic.exceptions.NotFoundError:
                pass

        # Return data
        added_event_fields = {
            "count": prior_count,
            "firstTimestamp": first_timestamp,
            "involvedObject": involved_obj,
            "lastTimestamp": last_timestamp,
        }

        event.update(added_event_fields)

        try:
            instance = v1_events.get(name=self.params.get("name"), namespace=self.params.get("namespace"))
        except kubernetes.dynamic.exceptions.NotFoundError:
            try:
                created_event = v1_events.create(body=event, namespace=self.params.get("namespace"))
                return dict(result=created_event.to_dict(), changed=True)
            except Exception as err:
                self.fail_json(msg="Unable to create event: {0}".format(err))

        try:
            result = v1_events.patch(body=event, namespace=self.params.get("namespace"))
            result_dict = result.to_dict()
            changed = instance.to_dict() != result_dict
            return dict(result=result_dict, changed=changed)
        except Exception as err:
            self.fail_json(msg="Unable to create event: {0}".format(err))


def main():
    module = KubernetesEvent()
    result_event = module.execute_module()
    module.exit_json(**result_event)


if __name__ == "__main__":
    main()
