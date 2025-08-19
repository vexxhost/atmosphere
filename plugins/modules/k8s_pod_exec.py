# Copyright (c) 2025 VEXXHOST, Inc.
# SPDX-License-Identifier: Apache-2.0

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = """
---
module: k8s_pod_exec
short_description: Create Kubernetes pod, execute command, and retrieve output
description:
    - Creates a Kubernetes pod with specified configuration
    - Executes a command inside the pod
    - Retrieves command output from pod logs
    - Terminates the pod after execution
    - Supports mounting secrets, config maps, and setting environment variables
version_added: "1.0.0"
requirements:
    - kubernetes >= 12.0.0
options:
    namespace:
        description:
            - Kubernetes namespace where the pod will be created
        type: str
        required: true
    pod_name:
        description:
            - Name of the pod to create
        type: str
        required: true
    container_image:
        description:
            - Container image to use for the pod
        type: str
        required: true
    command:
        description:
            - Command to execute inside the container
        type: list
        elements: str
        required: true
    args:
        description:
            - Arguments to pass to the command
        type: list
        elements: str
        required: false
    image_pull_policy:
      description: Image pull policy for the container
      required: false
      type: str
      choices: ['IfNotPresent', 'Always', 'Never']
      default: 'Always'
    timeout:
        description:
            - Maximum time in seconds to wait for pod completion
        type: int
        default: 300
    kubeconfig:
        description:
            - Path to kubeconfig file for Kubernetes authentication
            - If not specified, will try default kubeconfig locations or in-cluster config
        type: str
        required: false
    env_vars:
        description:
            - Environment variables to set in the container
        type: dict
        required: false
    env_from_secrets:
        description:
            - List of secrets to load as environment variables
        type: list
        elements: dict
        required: false
        suboptions:
            secret_name:
                description: Name of the secret
                type: str
                required: true
            prefix:
                description: Prefix for environment variable names
                type: str
                required: false
    env_from_configmaps:
        description:
            - List of config maps to load as environment variables
        type: list
        elements: dict
        required: false
        suboptions:
            configmap_name:
                description: Name of the config map
                type: str
                required: true
            prefix:
                description: Prefix for environment variable names
                type: str
                required: false
    secret_mounts:
        description:
            - List of secrets to mount as volumes
        type: list
        elements: dict
        required: false
        suboptions:
            secret_name:
                description: Name of the secret to mount
                type: str
                required: true
            mount_path:
                description: Path where the secret should be mounted
                type: str
                required: true
            default_mode:
                description: Default file permissions for mounted files
                type: int
                default: 420
    configmap_mounts:
        description:
            - List of config maps to mount as volumes
        type: list
        elements: dict
        required: false
        suboptions:
            configmap_name:
                description: Name of the config map to mount
                type: str
                required: true
            mount_path:
                description: Path where the config map should be mounted
                type: str
                required: true
            default_mode:
                description: Default file permissions for mounted files
                type: int
                default: 420
    working_dir:
        description:
            - Working directory for the container
        type: str
        required: false
    service_account:
        description:
            - Service account to use for the pod
        type: str
        required: false
    node_selector:
        description:
            - Node selector constraints for pod scheduling
        type: dict
        required: false
    tolerations:
        description:
            - Tolerations for pod scheduling
        type: list
        elements: dict
        required: false
    resources:
        description:
            - Resource requests and limits for the container
        type: dict
        required: false
        suboptions:
            requests:
                description: Resource requests
                type: dict
            limits:
                description: Resource limits
                type: dict
    save_output_to:
        description:
            - Local file path to save the command output
        type: str
        required: false
    keep_pod:
        description:
            - Whether to keep the pod after execution (useful for debugging)
        type: bool
        default: false
"""

EXAMPLES = """
# Basic pod execution with default kubeconfig
- name: Execute simple command
  k8s_pod_exec:
    namespace: default
    pod_name: test-pod
    container_image: busybox
    command: ["echo", "Hello World"]

# Pod execution with custom kubeconfig
- name: Execute with custom kubeconfig
  k8s_pod_exec:
    namespace: default
    pod_name: test-pod
    container_image: alpine
    command: ["printenv"]
    kubeconfig: /path/to/custom/kubeconfig
    env_vars:
      MY_VAR: "test_value"

# Pod with environment variables and custom kubeconfig
- name: Execute with environment variables and custom auth
  k8s_pod_exec:
    namespace: default
    pod_name: test-pod
    container_image: alpine
    command: ["printenv"]
    kubeconfig: ~/.kube/production-config
    env_vars:
      MY_VAR: "test_value"
      ENVIRONMENT: "production"

# Pod with secret mount and custom kubeconfig
- name: Execute with secret mount and custom kubeconfig
  k8s_pod_exec:
    namespace: default
    pod_name: test-pod
    container_image: alpine
    command: ["cat", "/etc/secret/password"]
    kubeconfig: /etc/kubernetes/admin.conf
    secret_mounts:
      - secret_name: my-secret
        mount_path: /etc/secret
    env_from_secrets:
      - secret_name: my-secret
        prefix: SECRET_

# Pod with config map mount and custom kubeconfig
- name: Execute with config map and custom kubeconfig
  k8s_pod_exec:
    namespace: default
    pod_name: test-pod
    container_image: alpine
    command: ["cat", "/etc/config/app.conf"]
    kubeconfig: "{{ ansible_env.HOME }}/.kube/staging-config"
    configmap_mounts:
      - configmap_name: my-config
        mount_path: /etc/config

# Pod with resource limits, custom kubeconfig and save output
- name: Execute with resource limits and custom auth
  k8s_pod_exec:
    namespace: default
    pod_name: test-pod
    container_image: alpine
    command: ["df", "-h"]
    kubeconfig: /var/lib/kubernetes/kubeconfig
    resources:
      requests:
        memory: "64Mi"
        cpu: "100m"
      limits:
        memory: "128Mi"
        cpu: "200m"
    save_output_to: /tmp/disk_usage.txt
    timeout: 120
"""

RETURN = """
stdout:
    description: Command output from the pod
    type: str
    returned: always
stderr:
    description: Error output from the pod (if any)
    type: str
    returned: when available
pod_name:
    description: Name of the created pod
    type: str
    returned: always
pod_status:
    description: Final status of the pod
    type: str
    returned: always
execution_time:
    description: Time taken for pod execution in seconds
    type: float
    returned: always
saved_to:
    description: Path where output was saved (if save_output_to was specified)
    type: str
    returned: when save_output_to is specified
kubeconfig_used:
    description: Path to kubeconfig file used for authentication
    type: str
    returned: when kubeconfig parameter is specified
"""

import os
import time

from ansible.module_utils.basic import AnsibleModule

try:
    from kubernetes import client, config

    HAS_KUBERNETES = True
except ImportError:
    HAS_KUBERNETES = False


def load_kubernetes_config(kubeconfig=None):
    """Load Kubernetes configuration from specified path or defaults."""
    try:
        if kubeconfig:
            # Expand user home directory if ~ is used
            kubeconfig = os.path.expanduser(kubeconfig)

            # Check if kubeconfig file exists
            if not os.path.exists(kubeconfig):
                return {
                    "success": False,
                    "msg": f"Kubeconfig file not found: {kubeconfig}",
                }

            # Load config from specified path
            config.load_kube_config(config_file=kubeconfig)
            return {
                "success": True,
                "msg": f"Loaded kubeconfig from {kubeconfig}",
                "path": kubeconfig,
            }
        else:
            # Try default kubeconfig locations first
            try:
                config.load_kube_config()
                return {"success": True, "msg": "Loaded default kubeconfig"}
            except Exception:
                # Fall back to in-cluster config
                config.load_incluster_config()
                return {"success": True, "msg": "Loaded in-cluster config"}

    except Exception as e:
        return {"success": False, "msg": f"Failed to load Kubernetes config: {str(e)}"}


def build_pod_spec(module_params):
    """Build the pod specification based on module parameters."""

    # Container specification
    container = {
        "name": module_params["pod_name"],
        "image": module_params["container_image"],
        "command": module_params["command"],
        "imagePullPolicy": module_params["image_pull_policy"],
    }

    # Add args if provided
    if module_params.get("args"):
        container["args"] = module_params["args"]

    # Add working directory if provided
    if module_params.get("working_dir"):
        container["workingDir"] = module_params["working_dir"]

    # Environment variables
    env_vars = []

    # Direct environment variables
    if module_params.get("env_vars"):
        for key, value in module_params["env_vars"].items():
            env_vars.append({"name": key, "value": str(value)})

    # Environment variables from secrets
    env_from = []
    if module_params.get("env_from_secrets"):
        for secret_ref in module_params["env_from_secrets"]:
            env_from_entry = {"secretRef": {"name": secret_ref["secret_name"]}}
            if secret_ref.get("prefix"):
                env_from_entry["prefix"] = secret_ref["prefix"]
            env_from.append(env_from_entry)

    # Environment variables from config maps
    if module_params.get("env_from_configmaps"):
        for cm_ref in module_params["env_from_configmaps"]:
            env_from_entry = {"configMapRef": {"name": cm_ref["configmap_name"]}}
            if cm_ref.get("prefix"):
                env_from_entry["prefix"] = cm_ref["prefix"]
            env_from.append(env_from_entry)

    if env_vars:
        container["env"] = env_vars
    if env_from:
        container["envFrom"] = env_from

    # Volume mounts
    volume_mounts = []
    volumes = []

    # Secret mounts
    if module_params.get("secret_mounts"):
        for secret_mount in module_params["secret_mounts"]:
            volume_name = f"secret-{secret_mount['secret_name']}"
            volume_mounts.append(
                {"name": volume_name, "mountPath": secret_mount["mount_path"]}
            )
            volumes.append(
                {
                    "name": volume_name,
                    "secret": {
                        "secretName": secret_mount["secret_name"],
                        "defaultMode": secret_mount.get("default_mode", 420),
                    },
                }
            )

    # Config map mounts
    if module_params.get("configmap_mounts"):
        for cm_mount in module_params["configmap_mounts"]:
            volume_name = f"configmap-{cm_mount['configmap_name']}"
            volume_mounts.append(
                {"name": volume_name, "mountPath": cm_mount["mount_path"]}
            )
            volumes.append(
                {
                    "name": volume_name,
                    "configMap": {
                        "name": cm_mount["configmap_name"],
                        "defaultMode": cm_mount.get("default_mode", 420),
                    },
                }
            )

    if volume_mounts:
        container["volumeMounts"] = volume_mounts

    # Resource specifications
    if module_params.get("resources"):
        container["resources"] = module_params["resources"]

    # Pod specification
    pod_spec = {"containers": [container], "restartPolicy": "Never"}

    # Add volumes if any
    if volumes:
        pod_spec["volumes"] = volumes

    # Service account
    if module_params.get("service_account"):
        pod_spec["serviceAccountName"] = module_params["service_account"]

    # Node selector
    if module_params.get("node_selector"):
        pod_spec["nodeSelector"] = module_params["node_selector"]

    # Tolerations
    if module_params.get("tolerations"):
        pod_spec["tolerations"] = module_params["tolerations"]

    # Complete pod manifest
    pod_manifest = {
        "apiVersion": "v1",
        "kind": "Pod",
        "metadata": {
            "name": module_params["pod_name"],
            "labels": {"app": "k8s-pod-exec", "created-by": "ansible-k8s-pod-exec"},
        },
        "spec": pod_spec,
    }

    return pod_manifest


def create_pod(api_instance, namespace, pod_manifest):
    """Create a pod in the specified namespace."""
    try:
        api_instance.create_namespaced_pod(namespace=namespace, body=pod_manifest)
        return {
            "success": True,
            "msg": f"Pod {pod_manifest['metadata']['name']} created successfully",
        }
    except client.exceptions.ApiException as e:
        return {"success": False, "msg": f"Failed to create pod: {str(e)}"}


def wait_for_pod_completion(api_instance, namespace, pod_name, timeout):
    """Wait for the pod to complete execution."""
    start_time = time.time()

    while time.time() - start_time < timeout:
        try:
            pod = api_instance.read_namespaced_pod(name=pod_name, namespace=namespace)
            phase = pod.status.phase

            if phase in ["Succeeded", "Failed"]:
                execution_time = time.time() - start_time
                return {
                    "success": True,
                    "phase": phase,
                    "execution_time": execution_time,
                }

            time.sleep(2)

        except client.exceptions.ApiException as e:
            return {"success": False, "msg": f"Failed to check pod status: {str(e)}"}

    execution_time = time.time() - start_time
    return {
        "success": False,
        "msg": "Pod execution timeout",
        "execution_time": execution_time,
    }


def get_pod_logs(api_instance, namespace, pod_name):
    """Retrieve logs from the pod."""
    try:
        logs = api_instance.read_namespaced_pod_log(
            name=pod_name, namespace=namespace, pretty=True
        )
        return {"success": True, "logs": logs}
    except client.exceptions.ApiException as e:
        return {"success": False, "msg": f"Failed to get pod logs: {str(e)}"}


def delete_pod(api_instance, namespace, pod_name):
    """Delete the pod."""
    try:
        api_instance.delete_namespaced_pod(name=pod_name, namespace=namespace)
        return {"success": True, "msg": f"Pod {pod_name} deleted successfully"}
    except client.exceptions.ApiException as e:
        return {"success": False, "msg": f"Failed to delete pod: {str(e)}"}


def save_output_to_file(output, file_path):
    """Save output to a local file."""
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        with open(file_path, "w") as f:
            f.write(output)
        return {"success": True, "msg": f"Output saved to {file_path}"}
    except Exception as e:
        return {"success": False, "msg": f"Failed to save output: {str(e)}"}


def main():
    """Main module execution."""

    module_args = dict(
        namespace=dict(type="str", required=True),
        pod_name=dict(type="str", required=True),
        container_image=dict(type="str", required=True),
        command=dict(type="list", elements="str", required=True),
        args=dict(type="list", elements="str", required=False),
        image_pull_policy=dict(
            required=False,
            type="str",
            choices=["IfNotPresent", "Always", "Never"],
            default="Always",
        ),
        timeout=dict(type="int", default=300),
        kubeconfig=dict(type="str", required=False),
        env_vars=dict(type="dict", required=False),
        env_from_secrets=dict(
            type="list",
            elements="dict",
            required=False,
            options=dict(
                secret_name=dict(type="str", required=True),
                prefix=dict(type="str", required=False),
            ),
        ),
        env_from_configmaps=dict(
            type="list",
            elements="dict",
            required=False,
            options=dict(
                configmap_name=dict(type="str", required=True),
                prefix=dict(type="str", required=False),
            ),
        ),
        secret_mounts=dict(
            type="list",
            elements="dict",
            required=False,
            options=dict(
                secret_name=dict(type="str", required=True),
                mount_path=dict(type="str", required=True),
                default_mode=dict(type="int", default=420),
            ),
        ),
        configmap_mounts=dict(
            type="list",
            elements="dict",
            required=False,
            options=dict(
                configmap_name=dict(type="str", required=True),
                mount_path=dict(type="str", required=True),
                default_mode=dict(type="int", default=420),
            ),
        ),
        working_dir=dict(type="str", required=False),
        service_account=dict(type="str", required=False),
        node_selector=dict(type="dict", required=False),
        tolerations=dict(type="list", elements="dict", required=False),
        resources=dict(
            type="dict",
            required=False,
            options=dict(
                requests=dict(type="dict", required=False),
                limits=dict(type="dict", required=False),
            ),
        ),
        save_output_to=dict(type="str", required=False),
        keep_pod=dict(type="bool", default=False),
    )

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    # Check if kubernetes library is available
    if not HAS_KUBERNETES:
        module.fail_json(msg="kubernetes library is required for this module")

    # Load Kubernetes configuration
    kubeconfig = module.params.get("kubeconfig")
    config_result = load_kubernetes_config(kubeconfig)
    if not config_result["success"]:
        module.fail_json(msg=config_result["msg"])

    # Initialize API client
    api_instance = client.CoreV1Api()

    # Extract parameters
    namespace = module.params["namespace"]
    pod_name = module.params["pod_name"]
    timeout = module.params["timeout"]
    save_output_to = module.params.get("save_output_to")
    keep_pod = module.params["keep_pod"]

    # Build pod specification
    pod_manifest = build_pod_spec(module.params)

    # Check mode - don't actually create resources
    if module.check_mode:
        check_result = {
            "changed": True,
            "pod_manifest": pod_manifest,
            "config_loaded": config_result["msg"],
        }
        if kubeconfig:
            check_result["kubeconfig_used"] = config_result.get("path", kubeconfig)
        module.exit_json(**check_result)

    results = {
        "changed": True,
        "pod_name": pod_name,
        "stdout": "",
        "stderr": "",
        "pod_status": "",
        "execution_time": 0,
    }

    # Add kubeconfig info to results if specified
    if kubeconfig:
        results["kubeconfig_used"] = config_result.get("path", kubeconfig)

    try:
        # Create pod
        create_result = create_pod(api_instance, namespace, pod_manifest)
        if not create_result["success"]:
            module.fail_json(msg=create_result["msg"])

        # Wait for pod completion
        wait_result = wait_for_pod_completion(
            api_instance, namespace, pod_name, timeout
        )
        if not wait_result["success"]:
            # Try to cleanup before failing
            if not keep_pod:
                delete_pod(api_instance, namespace, pod_name)
            module.fail_json(msg=wait_result["msg"])

        results["pod_status"] = wait_result["phase"]
        results["execution_time"] = wait_result["execution_time"]

        # Get pod logs
        logs_result = get_pod_logs(api_instance, namespace, pod_name)
        if logs_result["success"]:
            results["stdout"] = logs_result["logs"]
        else:
            results["stderr"] = logs_result["msg"]

        # Save output to file if requested
        if save_output_to and results["stdout"]:
            save_result = save_output_to_file(results["stdout"], save_output_to)
            if save_result["success"]:
                results["saved_to"] = save_output_to
            else:
                module.warn(f"Failed to save output: {save_result['msg']}")

        # Delete pod unless keep_pod is True
        if not keep_pod:
            delete_result = delete_pod(api_instance, namespace, pod_name)
            if not delete_result["success"]:
                module.warn(f"Failed to delete pod: {delete_result['msg']}")

        # Check if pod failed
        if wait_result["phase"] == "Failed":
            module.fail_json(msg=f"Pod execution failed", **results)

        module.exit_json(**results)

    except Exception as e:
        # Cleanup on unexpected errors
        if not keep_pod:
            try:
                delete_pod(api_instance, namespace, pod_name)
            except:
                pass
        module.fail_json(msg=f"Unexpected error: {str(e)}")


if __name__ == "__main__":
    main()
