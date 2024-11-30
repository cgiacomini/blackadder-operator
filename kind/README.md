## Deploy Kubernetes cluster
Here we deploy a 4 nodes cluster with a control-plane and three workers nodes
The cluster also mount a local host dirctory in each nodes. 
```
$ kind create cluster --config ./singleton.yaml
```

## Deploy the nginx Ingress Controller
```
$ kubectl apply -f http://raw.githubusercontent.com/kubernetes/ingress-nginx/master/deploy/static/provider/baremetal/deploy.yaml
```

## Delete the cluster
```
kind delete cluster --name singleton
```
