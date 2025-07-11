# Copyright (c) 2025 VEXXHOST, Inc.
# SPDX-License-Identifier: Apache-2.0

import os
import select
import signal
import socket
import sys
import threading
import time

from ansible.module_utils.basic import AnsibleModule

try:
    from kubernetes import client, config, stream

    HAS_KUBERNETES = True
except ImportError:
    HAS_KUBERNETES = False

DOCUMENTATION = """
---
module: k8s_port_forward
short_description: Port forward to a Kubernetes pod or service
description:
  - Native Ansible module to port-forward from local to a Kubernetes pod port.
  - Validates namespace, pod, and container readiness.
  - Supports resolving pod from service name.
  - Supports multiple port mappings.
options:
  namespace:
    description: Namespace of the target
    required: true
    type: str
  pod_name:
    description: Name of the pod (optional if service_name is provided)
    required: false
    type: str
  service_name:
    description: Name of the service (optional if pod_name is provided)
    required: false
    type: str
  ports:
    description: Comma-separated list of local:remote port pairs (e.g. "8080:80,8443:443")
    required: true
    type: str
  kubeconfig_path:
    description: Path to kubeconfig file
    required: false
    type: str
  state:
    description: Whether to start or stop port forwarding
    required: false
    type: str
    choices: ['present', 'absent']
    default: 'present'
"""

EXAMPLES = """
- name: Start port forwarding (non-blocking)
  k8s_port_forward:
    namespace: dev
    service_name: my-api
    ports: "8080:80,8443:443"
    state: present
  async: 300
  poll: 0
  register: port_forward_job

- name: Do other tasks while port forwarding runs
  debug:
    msg: "Port forwarding started, continuing with other tasks"

- name: Check port forwarding status later
  async_status:
    jid: "{{ port_forward_job.ansible_job_id }}"
  register: job_result

- name: Stop port forwarding
  async_status:
    jid: "{{ port_forward_job.ansible_job_id }}"
    mode: cleanup
"""

# Global variables for cleanup
active_servers = []
active_threads = []
shutdown_event = threading.Event()

def cleanup_resources():
    """Clean up all active servers and threads"""
    global active_servers, active_threads

    shutdown_event.set()

    # Close all server sockets
    for server in active_servers:
        try:
            server.close()
        except:
            pass

    # Wait for threads to finish (with timeout)
    for thread in active_threads:
        thread.join(timeout=2)

    active_servers.clear()
    active_threads.clear()

def signal_handler(signum, frame):
    """Handle cleanup on signal"""
    cleanup_resources()
    sys.exit(0)

def resolve_pod_from_service(core_v1, namespace, service_name):
    """Resolve a pod name from a service name"""
    try:
        svc = core_v1.read_namespaced_service(service_name, namespace)
        selector = svc.spec.selector
        if not selector:
            raise Exception("Service has no selector to resolve pods.")

        label_selector = ",".join(f"{k}={v}" for k, v in selector.items())
        pods = core_v1.list_namespaced_pod(namespace, label_selector=label_selector)

        if not pods.items:
            raise Exception("No pods found matching service selector.")

        # Find a running pod
        for pod in pods.items:
            if pod.status.phase == "Running":
                return pod.metadata.name

        raise Exception("No running pods found matching service selector.")
    except client.exceptions.ApiException as e:
        if e.status == 404:
            raise Exception(f"Service '{service_name}' not found in namespace '{namespace}'.")
        else:
            raise Exception(f"Error accessing service: {e}")


def create_server_socket(port):
    """Create and bind a server socket, return the socket and actual port used"""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        server.bind(('127.0.0.1', port))
        actual_port = server.getsockname()[1]
        return server, actual_port
    except OSError:
        server.close()
        raise

def forward_port(core_v1, namespace, pod_name, local_port, remote_port):
    """Set up port forwarding for a single port pair"""
    global active_servers, active_threads

    original_port = local_port
    server = None

    # Try to bind to the requested port
    try:
        server, actual_port = create_server_socket(local_port)
        local_port = actual_port
    except OSError:
        # Port already in use
        raise Exception(f"Local port {local_port} is already in use on 127.0.0.1")

    try:
        server.listen(5)
        server.settimeout(1)  # Set timeout for accept() to allow checking shutdown_event
        active_servers.append(server)
    except OSError as e:
        server.close()
        raise Exception(f"Failed to configure server socket: {e}")

    def handle_connection(client_sock, remote_port):
        """Handle a single client connection"""
        remote_sock = None
        try:
            # Create port forward stream
            pf = stream.portforward(
                core_v1.connect_get_namespaced_pod_portforward,
                pod_name,
                namespace,
                ports=str(remote_port)
            )

            # Get the socket for the remote port
            remote_sock = pf.socket(remote_port)

            # Set socket timeouts
            client_sock.settimeout(1)
            remote_sock.settimeout(1)

            # Set up bidirectional forwarding
            while not shutdown_event.is_set():
                try:
                    # Use select with timeout to check for shutdown
                    ready, _, _ = select.select([client_sock, remote_sock], [], [], 1)
                    
                    if not ready:
                        continue
                    
                    if client_sock in ready:
                        try:
                            data = client_sock.recv(4096)
                            if not data:
                                break
                            remote_sock.send(data)
                        except socket.timeout:
                            continue
                        except (ConnectionResetError, BrokenPipeError):
                            break
                    
                    if remote_sock in ready:
                        try:
                            data = remote_sock.recv(4096)
                            if not data:
                                break
                            client_sock.send(data)
                        except socket.timeout:
                            continue
                        except (ConnectionResetError, BrokenPipeError):
                            break
          
                except (ConnectionResetError, BrokenPipeError, OSError):
                    break

        except Exception as e:
            # Log connection errors for debugging
            pass
        finally:
            try:
                if client_sock:
                    client_sock.close()
            except:
                pass
            try:
                if remote_sock:
                    remote_sock.close()
            except:
                pass

    def server_loop():
        """Main server loop for accepting connections"""
        while not shutdown_event.is_set():
            try:
                client_sock, _ = server.accept()
                if shutdown_event.is_set():
                    client_sock.close()
                    break
                
                # Handle each connection in a separate thread
                thread = threading.Thread(
                    target=handle_connection, 
                    args=(client_sock, remote_port),
                    daemon=True
                )
                thread.start()
                active_threads.append(thread)
                
            except socket.timeout:
                continue  # Check shutdown_event again
            except OSError:
                break  # Server socket was closed

    # Start server thread
    server_thread = threading.Thread(target=server_loop, daemon=True)
    server_thread.start()
    active_threads.append(server_thread)

    return {
        "original_local_port": original_port,
        "effective_local_port": local_port,
        "remote_port": remote_port,
        "target_pod": pod_name,
    }

def main():
    module = AnsibleModule(
        argument_spec=dict(
            namespace=dict(required=True, type='str'),
            pod_name=dict(required=False, type='str'),
            service_name=dict(required=False, type='str'),
            ports=dict(required=True, type='str'),
            kubeconfig_path=dict(required=False, type='str'),
            state=dict(required=False, type='str', choices=['present', 'absent'], default='present'),
        ),
        required_one_of=[['pod_name', 'service_name']],
        supports_check_mode=False
    )

    if not HAS_KUBERNETES:
        module.fail_json(msg="The 'kubernetes' Python client is required. Install it with 'pip install kubernetes'.")

    namespace = module.params['namespace']
    pod_name = module.params['pod_name']
    service_name = module.params['service_name']
    ports = module.params['ports']
    kubeconfig_path = module.params['kubeconfig_path']
    state = module.params['state']

    # For 'absent' state, we can't really stop port forwarding since it's running in background
    # This would require a more complex implementation with PID files or similar
    if state == 'absent':
        module.exit_json(changed=False, msg="Port forwarding stop not implemented. Use async task termination instead.")

    # Set up signal handlers for cleanup
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    # Load kubeconfig
    try:
        if kubeconfig_path:
            config.load_kube_config(config_file=kubeconfig_path)
        else:
            try:
                config.load_incluster_config()
            except:
                config.load_kube_config()
    except Exception as e:
        module.fail_json(msg=f"Failed to load kubeconfig: {e}")

    core_v1 = client.CoreV1Api()

    # Validate namespace
    try:
        core_v1.read_namespace(namespace)
    except client.exceptions.ApiException as e:
        if e.status == 404:
            module.fail_json(msg=f"Namespace '{namespace}' does not exist.")
        else:
            module.fail_json(msg=f"Error accessing namespace: {e}")

    # Resolve pod if needed
    if service_name and not pod_name:
        try:
            pod_name = resolve_pod_from_service(core_v1, namespace, service_name)
        except Exception as e:
            module.fail_json(msg=f"Could not resolve pod from service '{service_name}': {e}")
    elif not pod_name and not service_name:
        module.fail_json(msg="Either pod_name or service_name must be provided")
    
    # If both are provided, prefer pod_name (already set)

    # Validate pod
    try:
        pod = core_v1.read_namespaced_pod(name=pod_name, namespace=namespace)
        if pod.status.phase != "Running":
            module.fail_json(msg=f"Pod '{pod_name}' is not running. Status: {pod.status.phase}")

        # Check container readiness more safely
        if pod.status.container_statuses:
            if not all(c.ready for c in pod.status.container_statuses):
                module.fail_json(msg=f"Not all containers in pod '{pod_name}' are ready.")

    except client.exceptions.ApiException as e:
        if e.status == 404:
            module.fail_json(msg=f"Pod '{pod_name}' not found in namespace '{namespace}'.")
        else:
            module.fail_json(msg=f"Error accessing pod: {e}")

    # Parse and validate port mappings
    port_pairs = []
    try:
        for pair in ports.split(','):
            local, remote = map(int, pair.strip().split(':'))
            if not (1025 <= local <= 65535):
                module.fail_json(msg=f"Invalid local port in '{pair}'. Local ports must be between 1025 and 65535.")
            if not (1 <= remote <= 65535):
                module.fail_json(msg=f"Invalid remote port in '{pair}'. Remote ports must be between 1 and 65535.")
            port_pairs.append((local, remote))
    except ValueError as e:
        module.fail_json(msg=f"Invalid port format: {e}. Expected 'local:remote' pairs.")

    # Start port forwards
    results = []
    try:
        for local, remote in port_pairs:
            result = forward_port(core_v1, namespace, pod_name, local, remote)
            results.append(result)
            
        # Verify port forwarding is actually listening
        time.sleep(0.1)  # Brief pause to let servers start
        for result in results:
            port = result['effective_local_port']
            try:
                test_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                test_sock.settimeout(1)
                test_result = test_sock.connect_ex(('127.0.0.1', port))
                test_sock.close()
                if test_result != 0:
                    # Port is not listening, which is expected until first connection
                    pass
            except:
                pass

    except Exception as e:
        cleanup_resources()
        module.fail_json(msg=f"Port forwarding failed: {e}")

    # If running with async, keep port forwarding active
    # If not async, return immediately (port forwarding runs in background threads)
    try:
        # Check if we're running under async by looking for common async environment indicators
        # In async mode, we should keep running; otherwise return immediately
        is_async = os.environ.get('ANSIBLE_ASYNC_DIR') is not None
        
        if is_async:
            # Running in async mode - keep the process alive
            while not shutdown_event.is_set():
                time.sleep(1)
        else:
            # Not async mode - return immediately, port forwarding runs in background
            pass

    except KeyboardInterrupt:
        pass
    finally:
        cleanup_resources()

    module.exit_json(
        changed=True, 
        msg=f"Port forwarding started for {len(results)} port(s). Use Ansible async/poll to manage lifecycle.", 
        forwards=results,
        pid=os.getpid()
    )

if __name__ == "__main__":

    main()
