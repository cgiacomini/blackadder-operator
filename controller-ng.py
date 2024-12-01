import random
import sys
import time
import logging
import munch
import pykube

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
        if len(pods) < tolerance:
            return
        for pod in random.sample(pods, eagerness):
            try:
                pod.delete()
                self.logger.info(f"Killed pod {pod.namespace}/{pod.name}")
            except Exception as e:
                self.logger.error(f"Error killing pod {pod.namespace}/{pod.name}: {e}")

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
                    new_replicas = random.randint(1, 10)
                    deployment.obj['spec']['replicas'] = new_replicas
                    deployment.update()
                    self.logger.info(f"Scaled {deployment.namespace}/{deployment.name} to {new_replicas}")
                except Exception as e:
                    self.logger.error(f"Error scaling deployment {deployment.namespace}/{deployment.name}: {e}")

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
