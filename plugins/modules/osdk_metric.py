#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2021,  Red Hat | Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function


__metaclass__ = type

ANSIBLE_METADATA = {
    "metadata_version": "1.1",
    "status": ["preview"],
    "supported_by": "community",
}

DOCUMENTATION = """
module: osdk_metric
short_description: Communicates a metric to be created or updated to the controller
version_added: "0.0.1"
author: "Fabian von Feilitzsch (@fabianvf)"
description:
  - Tells the controller to create or update a prometheus metric

options:
  name:
    type: str
    required: True
    description:
    - The name of the prometheus metric to be created or updated
  description:
    type: str
    required: True
    description:
    - The description of the prometheus metric, used for help text
  address:
    type: str
    required: False
    default: "http://localhost:5050/metrics"
    description:
    - The addresss of the Operator SDK metrics server
  counter:
    type: dict
    required: False
    description:
    - Instructs the controller to create a prometheus counter metric
    suboptions:
      increment:
        type: bool
        required: False
        description:
        - Instructs the controller to increment the counter
      add:
        type: float
        required: False
        description:
        - Instructs the controller to add the value to the counter
  gauge:
    type: dict
    required: False
    description:
    - Instructs the controller to create a prometheus gauge metric
    suboptions:
      set:
        type: float
        required: False
        description:
        - Instructs the controller to set the gauge to the provided value
      increment:
        type: bool
        required: False
        description:
        - Instructs the controller to increment the gauge
      decrement:
        type: bool
        required: False
        description:
        - Instructs the controller to decrement the gauge
      add:
        type: float
        required: False
        description:
        - Instructs the controller to add the value to the gauge
      subtract:
        type: float
        required: False
        description:
        - Instructs the controller to subract the value from the gauge
      set_to_current_time:
        type: bool
        required: False
        description:
        - Instructs the controller to reset the gauge time. TODO(asmacdo)
  histogram:
    type: dict
    required: False
    description:
    - Instructs the controller to create a prometheus histogram metric
    suboptions:
      observe:
        type: float
        required: False
        description:
        - Adds a single observation to the historgram.
  summary:
    type: dict
    required: False
    description:
    - Instructs the controller to create a prometheus summary metric
    suboptions:
      observe:
        type: float
        required: False
        description:
        - Adds a single observation to the summary.
"""

EXAMPLES = """
TODO(asmacdo)
"""

RETURN = """
"""

from ansible.module_utils.basic import AnsibleModule


def main():
    module = AnsibleModule(
        argument_spec={
            "name": {"type": "str", "required": True},
            "description": {"type": "str", "required": True},
            "address": {"type": "str", "required": False, "default": "http://localhost:5050/metrics"},
            "counter": {"type": "dict", "required": False, "options": {
                "increment": {"type": "bool", "required": False},
                "add": {"type": "float", "required": False},
            }},
            "gauge": {"type": "dict", "required": False, "options": {
                "set": {"type": "float", "required": False},
                "increment": {"type": "bool", "required": False},
                "decrement": {"type": "bool", "required": False},
                "add": {"type": "float", "required": False},
                "subtract": {"type": "float", "required": False},
                "set_to_current_time": {"type": "bool", "required": False},
            }},
            "histogram": {"type": "dict", "required": False, "options": {
                "observe": {"type": "float", "required": False},
            }},
            "summary": {"type": "dict", "required": False, "options": {
                "observe": {"type": "float", "required": False},
            }},
        }
    )
    try:
        import requests
    except ImportError:
        module.fail_json('`requests` is not installed, please install via pip or pipenv.')

    payload = dict(name=module.params.get("name"), description=module.params.get("description"))

    url = module.params.get("address")
    if module.params.get('counter'):
        payload["counter"] = module.params["counter"]
    if module.params.get('gauge'):
        payload["gauge"] = module.params["gauge"]
    if module.params.get('histogram'):
        payload["histogram"] = module.params["histogram"]
    if module.params.get('summary'):
        payload["summary"] = module.params["summary"]

    response = requests.post(url, json=payload)
    if response.status_code != 200:
        module.fail_json(msg=response.text)

    module.exit_json(changed=True)


if __name__ == "__main__":
    main()
