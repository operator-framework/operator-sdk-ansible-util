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
"""

EXAMPLES = """
- name: create my_counter_metric
  osdk_metric:
    name: my_counter_metric
    description: Random counter metric
    counter: {}

- name: increment my_counter_metric
  osdk_metric:
    name: my_counter_metric
    description: Random counter metric
    counter:
      increment: yes

- name: add 3.14 to my_counter_metric
  osdk_metric:
    name: my_counter_metric
    description: Random counter metric
    counter:
      add: 3.14
"""

RETURN = """
"""


from ansible.module_utils.basic import AnsibleModule


def main():
    module = AnsibleModule(
        argument_spec={
            "name": {"type": "str", "required": True},
            "description": {"type": "str", "required": True},
            "counter": {"type": "dict", "required": False, "options": {
                "increment": {"type": "bool", "required": False},
                "add": {"type": "float", "required": False},
            }},
        }
    )

    module.exit_json(**module.params)


if __name__ == "__main__":
    main()
