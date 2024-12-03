import random
import sys
import time
import logging
import munch
import pykube
import lorem

from pykube import Pod, Deployment, ConfigMap

class ChaosController:
    def __init__(self):
        """
        Initializes the ChaosController by setting up logging, configuring the Kubernetes client,
        and retrieving the ChaosAgent configuration.
        """
        self.setup_logging()
        try:
            self.config = pykube.KubeConfig.from_env()
            self.api = pykube.HTTPClient(self.config)
            self.ChaosAgent = pykube.object_factory(self.api, "blackadder.io/v1beta1", "ChaosAgent")
            self.agent = self.get_agent()
            if not self.agent:
                self.logger.error("No ChaosAgent found, exiting")
                sys.exit(1)
            self.exclude_namespaces = self.agent.config.excludedNamespaces
            self.pause_duration = int(self.agent.config.pauseDuration)
        except Exception as e:
            self.logger.error(f"Error initializing ChaosController: {e}")
            sys.exit(1)

    def setup_logging(self):
        """
        Sets up logging for the ChaosController.
        """
        self.logger = logging.getLogger("ChaosController")
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.DEBUG)

    def get_agent(self):
        """
        Retrieves the ChaosAgent configuration from the Kubernetes API server.

        Returns:
            agent (pykube.objects): The ChaosAgent object with its configuration.
        """
        try:
            agents = list(self.ChaosAgent.objects(self.api, namespace=pykube.all))
            if not agents:
                return None
            agent = agents[0]
            agent.config = munch.munchify(agent.obj["spec"])
            self.logger.info("Successfully retrieved agent configuration")
            return agent
        except Exception as e:
            self.logger.error(f"Error retrieving agent configuration: {e}")
            sys.exit(1)

    def list_objects(self, k8s_obj):
        """
        Lists Kubernetes objects of the specified type, excluding those in specified namespaces.

        Args:
            k8s_obj (pykube.objects): The type of Kubernetes object to list.

        Returns:
            list: A list of Kubernetes objects.
        """
        exclude_namespaces = ",".join("metadata.namespace!=" + ns for ns in self.exclude_namespaces)
        try:
            objects = list(k8s_obj.objects(self.api).filter(namespace=pykube.all, field_selector=exclude_namespaces))
            self.logger.debug(f"Listed {len(objects)} objects of type {k8s_obj.__name__}")
            return objects
        except Exception as e:
            self.logger.error(f"Error listing objects: {e}")
            return []

    def randomly_kill_pods(self, pods, tolerance, eagerness):
        """
        Randomly kills pods based on the specified tolerance and eagerness.

        Args:
            pods (list): A list of Pod objects.
            tolerance (int): The minimum number of pods to keep alive.
            eagerness (int): The percentage chance to kill each pod.
        """
        try:
            if len(pods) < tolerance:
                self.logger.info(f"Skipping pod killing, only {len(pods)} pods found")
                return
            # Randomly select PODs to kill
            pods_to_kill = []
            for pod in pods:
                if random.randint(1, 100) <= eagerness:
                    pods_to_kill.append(pod)
            
            # Ensure we do not kill more pods than allowed by tolerance
            if len(pods) - len(pods_to_kill) < tolerance:
                self.logger.info(f"Skipping pod killing, would violate tolerance with {len(pods_to_kill)} pods to kill")
                return
            
            # Kill selected PODs
            self.logger.info(f"Attempting to kill {len(pods_to_kill)} pods out of {len(pods)} available pods")
            for pod in pods_to_kill:
                try:
                    self.logger.info(f"Killing pod {pod.namespace}/{pod.name}")
                    pod.delete()
                    self.logger.info(f"Killed pod {pod.namespace}/{pod.name}")
                except Exception as e:
                    self.logger.error(f"Error killing pod {pod.namespace}/{pod.name}: {e}")
        except Exception as e:
            self.logger.error(f"Error killing pods: {e}")

    def randomly_scale_deployments(self, deployments, eagerness):
        """
        Randomly scales deployments based on the specified eagerness.

        Args:
            deployments (list): A list of Deployment objects.
            eagerness (int): The percentage chance to scale each deployment.
        """
        for deployment in deployments:
            if random.randint(0, 100) < eagerness:
                try:
                    current_replicas = deployment.obj['spec']['replicas']
                    #  Scale deployment to double the current number of replicas, up to a maximum of 128
                    if current_replicas < 128:
                        new_replicas = min(current_replicas * 2, 128)
                    else:
                        new_replicas = current_replicas  # No change if already 128 or more

                    # Update the deployment with the new number of replicas
                    deployment.obj['spec']['replicas'] = new_replicas
                    deployment.update()
                    self.logger.info(f"Scaled {deployment.namespace}/{deployment.name} to {new_replicas}")
                except Exception as e:
                    self.logger.error(f"Error scaling deployment {deployment.namespace}/{deployment.name}: {e}")

    def randomly_write_configmaps(self, configmaps, eagerness):
        """
        Randomly modifies the data in Kubernetes ConfigMaps based on a specified eagerness level.

        Args:
            configmaps (list): A list of ConfigMap objects.
            eagerness (int): The percentage chance to modify each ConfigMap.
        """
        for cm in configmaps:
            self.logger.info(f"Checking {cm.namespace}/{cm.name}")
            
            # Check if the ConfigMap is immutable
            if cm.obj.get("immutable"):
                self.logger.info(f"Skipping immutable ConfigMap {cm.namespace}/{cm.name}")
                continue
            
            # Randomly decide whether to modify the ConfigMap based on eagerness
            if random.randint(0, 100) < eagerness:
                try:
                    # Replace each value in the data section with Lorem Ipsum text
                    for k, v in cm.obj["data"].items():
                        cm.obj["data"][k] = lorem.paragraph()
                    cm.update()
                    self.logger.info(f"Modified ConfigMap {cm.namespace}/{cm.name} with Lorem Ipsum text")
                except Exception as e:
                    self.logger.error(f"Error modifying ConfigMap {cm.namespace}/{cm.name}: {e}")
                    
    def run(self):
        """
        Runs the main loop of the ChaosController, periodically listing objects and performing chaos actions.
        """
        while True:
            try:
                pods = self.list_objects(Pod)
                deployments = self.list_objects(Deployment)
                if pods:
                    self.randomly_kill_pods(pods, tolerance=self.agent.config.tolerance, eagerness=self.agent.config.eagerness)
                if deployments:
                    self.randomly_scale_deployments(deployments, eagerness=self.agent.config.eagerness)
            except Exception as e:
                self.logger.error(f"Error in main loop: {e}")

            time.sleep(self.pause_duration)

if __name__ == "__main__":
    controller = ChaosController()
    controller.run()
