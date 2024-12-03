The Blackadder - a chaos engineering operator
=============================================

This a companion repository for the article in
the German Entwickler magazine about writing
Kubernetes Operators with Python.

The Operator's algorithm in pseudo code is:

```
client = connect_to_kubernetes()

# retrieves our agent configuration from the kube-api-server
chaos_agent = client.get_chaos_agent()

while True:
      pods = client.list_pods(exclude_namespaces)
      deployments = client.list_deployments(exclude_namespaces)
      namespaces =   client.list_configmaps(exclude_namespaces)
      
      if chaos_agent.tantrum:
         randomly_kill_pods(pods, chaos_agent.tolerance, chaos_agent.eagerness)

      if chaos_agent.cancer:
         randomly_scale_deployments(deployments, chaos_agent.eagerness)
      
      if chaos_agent.ipsum:
         randomly_write_configmaps(configmaps, chaos_agent.eagerness)

      time.sleep(chaos_agent.pause)
```

**WARNING**

DON'T RUN THIS IN PRODUCTION !!!  
DON'T RUN THIS IN PRODUCTION !!!  
DON'T RUN THIS IN PRODUCTION !!!  

## Why the name?
The name is obvisiouly inspired from the
british comedy [The Blackadder][1].

## Get Started
```
# Prepare Python virtual environment
$ python3 -m venv PyEnv
$ source PyEnv/bin/activate
$ pip install -r requirements.txt

# Deploy 'Kind' kubernetes cluster
$ make kind

# Create docker image
$ make docker

# Load the docker image on the cluster's nodes
$ make load

# Deploy the operator and test pods and deployments
make deploy
```

## What we expect? 
Sure! 

1. The controller randomly decides whether to kill each pod based on a specified probability (`eagerness`),   
   ensuring that the number of remaining pods does not fall below a specified minimum (`tolerance`).

2. It decides whether to scale each deployment based on a specified probability (`eagerness`).  
   If chosen, it doubles the number of replicas if they are less than 128, ensuring the total does not exceed 128.
 
3. It randomly modifies the data in Kubernetes ConfigMaps based on a specified probability (eagerness).  
   It replaces each value in the ConfigMap’s data section with Lorem Ipsum text, skipping immutable ConfigMaps.
    
   

[1]: https://en.wikipedia.org/wiki/The_Black_Adder
