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
module: requeue_after
short_description: Tells the controller to re-trigger reconciliation after the specified time
version_added: "0.0.1"
author: "Venkat Ramaraju (@VenkatRamaraju)"
description:
  - Tells the controller to pause reconciliation and resume reconciliation after a specified amounts of time.
    If the requeue_reconciliation period is set to 't', reconciliation will occur in intervals of 't'.

options:
  time:
    type: str
    required: True
    description:
    - A string containing a time period that will be set on the returned JSON object and then used to requeue
      reconciliation of an event. Time can be specified in any combination of hours, minutes, and seconds.
"""

EXAMPLES = """
- name:
    requeue_after:
        time: 24h

- name:
    requeue_after:
        time: 30m

- name:
    requeue_after:
        time: 5s
"""

RETURN = """
result:
  description:
  - If a requeue period was specified under 'time' when calling the requeue_after period from the module,
    this module will return a JSON object.
  returned: success
  type: complex
  contains:
    _ansible_no_log:
       description: This is a boolean. If it's True then the playbook specified no_log (in a task's parameters or as a play parameter).
       returned: success
       type: bool
    changed:
       description: A boolean indicating if the task had to make changes.
       returned: success
       type: bool
    invocation:
       description: Information on how the module was invoked.
       returned: success
       type: dict
    period:
       description: A time value read in from a playbook that specifies how long the reconciliation should be requeued after.
       returned: success
       type: str
"""


from ansible.module_utils.basic import AnsibleModule
import re


def requeue_after():
    module = AnsibleModule(
        argument_spec={
            "time": {"type": "str", "required": True},
        }
    )

    if not re.match("^[hms0-9]*$", module.params["time"]):
        module.fail_json(msg="invalid time input")

    result = dict(
        period=module.params["time"],
    )

    module.exit_json(**result)


def main():
    requeue_after()


if __name__ == "__main__":
    main()
