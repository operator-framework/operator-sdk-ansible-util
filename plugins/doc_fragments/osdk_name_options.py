# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Red Hat | Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Options for selecting or identifying a specific K8s object

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


class ModuleDocFragment(object):

    DOCUMENTATION = r'''
options:
  api_version:
    description:
    - Use to specify the object's API version.
    - Use in conjunction with I(kind), I(name), and I(namespace) to identify a specific object.
    type: str
    default: v1
    aliases:
    - api
    - version
  kind:
    description:
    - Use to specify an object kind.
    - Use in conjunction with I(api_version), I(name), and I(namespace) to identify a specific object.
    type: str
    required: yes
  name:
    description:
    - Use to specify an object name.
    - Use in conjunction with I(api_version), I(kind) and I(namespace) to identify a specific object.
    type: str
    required: yes
  namespace:
    description:
    - Use to specify an object namespace.
    - Use in conjunction with I(api_version), I(kind), and I(name) to identify a specific object.
    type: str
'''
