from __future__ import absolute_import, division, print_function

__metaclass__ = type


import os
import traceback

from ansible.module_utils._text import to_native
from ansible.module_utils.six import iteritems

K8S_IMP_ERR = None
try:
    from ansible_collections.operator_sdk.util.plugins.module_utils.args_common import (
        AUTH_ARG_SPEC,
        AUTH_ARG_MAP,
    )
    import kubernetes
    from kubernetes.dynamic import DynamicClient
    from kubernetes.dynamic.exceptions import (ResourceNotFoundError, ResourceNotUniqueError)
    HAS_K8S_MODULE_HELPER = True
    k8s_import_exception = None
except ImportError as e:
    HAS_K8S_MODULE_HELPER = False
    k8s_import_exception = e
    K8S_IMP_ERR = traceback.format_exc()


def get_api_client(module=None):
    auth = {}

    def _raise_or_fail(exc, message):
        if module:
            module.fail_json(msg=message, error=to_native(exc))
        else:
            raise exc

    # If authorization variables aren't defined, look for them in environment variables
    for true_name, arg_name in AUTH_ARG_MAP.items():
        if module and module.params.get(arg_name):
            auth[true_name] = module.params.get(arg_name)
        else:
            env_value = os.getenv('K8S_AUTH_{0}'.format(arg_name.upper()), None) or os.getenv('K8S_AUTH_{0}'.format(true_name.upper()), None)
            if env_value is not None:
                if AUTH_ARG_SPEC[arg_name].get('type') == 'bool':
                    env_value = env_value.lower() not in ['0', 'false', 'no']
                auth[true_name] = env_value

    def auth_set(*names):
        return all(auth.get(name) for name in names)

    if auth_set('username', 'password', 'host') or auth_set('api_key', 'host'):
        # We have enough in the parameters to authenticate, no need to load incluster or kubeconfig
        pass
    elif auth_set('kubeconfig') or auth_set('context'):
        try:
            kubernetes.config.load_kube_config(auth.get('kubeconfig'), auth.get('context'), persist_config=auth.get('persist_config'))
        except Exception as err:
            _raise_or_fail(err, 'Failed to load kubeconfig due to %s')

    else:
        # First try to do incluster config, then kubeconfig
        try:
            kubernetes.config.load_incluster_config()
        except kubernetes.config.ConfigException:
            try:
                kubernetes.config.load_kube_config(auth.get('kubeconfig'), auth.get('context'), persist_config=auth.get('persist_config'))
            except Exception as err:
                _raise_or_fail(err, 'Failed to load kubeconfig due to %s')

    # Override any values in the default configuration with Ansible parameters
    # As of kubernetes-client v12.0.0, get_default_copy() is required here
    try:
        configuration = kubernetes.client.Configuration().get_default_copy()
    except AttributeError:
        configuration = kubernetes.client.Configuration()

    for key, value in iteritems(auth):
        if key in AUTH_ARG_MAP.keys() and value is not None:
            if key == 'api_key':
                setattr(configuration, key, {'authorization': "Bearer {0}".format(value)})
            else:
                setattr(configuration, key, value)

    try:
        client = DynamicClient(kubernetes.client.ApiClient(configuration))
    except Exception as err:
        _raise_or_fail(err, 'Failed to get client due to %s')

    return client


def find_resource(client, kind, api_version):
    for attribute in ['kind', 'name', 'singular_name']:
        try:
            return client.resources.get(**{'api_version': api_version, attribute: kind})
        except (ResourceNotFoundError, ResourceNotUniqueError):
            pass
    try:
        return client.resources.get(api_version=api_version, short_names=[kind])
    except (ResourceNotFoundError, ResourceNotUniqueError):
        return None
