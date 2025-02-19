# containers_ocp

Repository for fully automated installation and configuration of the necessary environment to run **Containers in OpenShift** demo.

> [!IMPORTANT]  
> Tested versions: 
> - OpenShift: 4.17

## Install

- Open a terminal
- Login into OpenShift
- Run installation:

```sh
CLUSTER_DOMAIN=$(oc whoami --show-server | sed 's~https://api\.~~' | sed 's~:.*~~')
ansible-playbook installation/install.yaml -e "ocp_host=$CLUSTER_DOMAIN" -e "bw_token=<BITWARDEN_TOKEN_HERE>"
```

## Unistall

- Open a terminal
- Login into OpenShift
- Run installation:
```sh
CLUSTER_DOMAIN=$(oc whoami --show-server | sed 's~https://api\.~~' | sed 's~:.*~~')
ansible-playbook installation/uninstall.yaml -e "ocp_host=$CLUSTER_DOMAIN"
```

## Demo 

### Best Practices

- Initial dockerfile:

```dockerfile
FROM node:latest

WORKDIR /app

ADD . /app

RUN npm install -g nodemon
RUN apt-get update
RUN apt-get install -y curl

EXPOSE 8080 9090 10000

CMD ["node", "server.js"]
```

- Build and play with it:

```sh
cd node_example
ls -la

podman build -t node_example:1.0 .

podman images node_example

podman image inspect node_example:1.0 --format '{{ len .RootFS.Layers }}'
```


- Fixed dockerfile (keeping root bad behaviour)

```dockerfile
FROM registry.redhat.io/ubi9/ubi-minimal:9.3 #1

WORKDIR /app

COPY . . #2

RUN microdnf install -y nodejs npm shadow-utils procps && \ #2
    microdnf clean all && \
    npm install && \
    rm -rf /var/cache /tmp/*

ENV NODE_ENV=production #3

LABEL maintainer="calopezb@redhat.com>" #4

EXPOSE 3000 #5

ENTRYPOINT ["node"] #6

CMD ["server.js"] #7
```

- Create .dockerignore with node_modules and .git

- Build and play with it:

```sh
podman build -t node_example:2.0 .

podman images node_example

podman image inspect node_example:2.0 --format '{{ len .RootFS.Layers }}'

podman images --filter "label=maintainer=calopezb@redhat.com"
```

- Push to quay

```sh
podman tag node_example:2.0 quay.io/calopezb/node_example:2.0

podman push quay.io/calopezb/node_example:2.0
```

- Review Quay

### Users and Service Accounts

```sh
# Create a namespace
oc project demo-sa
# Create a ServiceAccount
oc create serviceaccount monitor
oc get sa

# Create a Role
cat <<EOF | oc apply -f -
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: pod-reader
rules:
- apiGroups: [""]
  resources: ["pods"]
  verbs: ["get", "list", "watch"]
EOF

oc get role
oc describe role pod-reader

# Bind the Role to the ServiceAccount
oc create rolebinding pod-reader-binding \
  --role=pod-reader \
  --serviceaccount=demo-sa:monitor \
  --namespace=demo-sa

# Check which roles the ServiceAccount has:
oc describe rolebinding pod-reader-binding

# List permissions for the ServiceAccount:
oc auth can-i list pods --as=system:serviceaccount:demo-sa:monitor
```

### ROOT

- Review previus app

```sh
# RUn app
podman run -d -p 3000:3000 --name node-example node_example:2.0

# Review -- root
podman exec -it node-example sh
ps aux
exit

# Review in laptop -- no root
ps aux | grep "node server.js"
```

- Fix containerfile

```dockerfile
FROM registry.redhat.io/ubi9/ubi-minimal:9.3

WORKDIR /app

USER root #1

COPY . .

RUN microdnf install -y nodejs npm shadow-utils procps && \
    microdnf clean all && \
    groupadd -r appuser && \ #3
    useradd -r -m -g appuser appuser && \ #3
    chown -R appuser:appuser /app && \ #3
    npm install && \
    rm -rf /var/cache /tmp/*

USER appuser

ENV NODE_ENV=production

LABEL maintainer="calopezb@redhat.com>"

EXPOSE 3000

ENTRYPOINT ["node"]

CMD ["server.js"]
```

- Build, run, push and deploy in OCP

```sh
# build
podman build -t node_example:3.0 .

podman images node_example

# RUn app
podman run -d -p 3000:3000 --name node-example node_example:3.0

# Review -- root
podman exec -it node-example sh
ps aux
exit

# Push
podman tag node_example:3.0 quay.io/calopezb/node_example:3.0

podman push quay.io/calopezb/node_example:3.0


# DEploy ocp
oc project demo-node

oc new-app --image=quay.io/calopezb/node_example:3.0 --name=node-example-v3

# Question? 2 would work in OCP
oc new-app --image=quay.io/calopezb/node_example:2.0 --name=node-example-v2
```

### Bitwarden Secret

curl -X POST http://api-public-layer.apps.hetzner.calopezb.com/pay -d "amount=10" 

```yaml
apiVersion: k8s.bitwarden.com/v1
kind: BitwardenSecret
metadata:
  labels:
    app.kubernetes.io/name: bitwardensecret
    app.kubernetes.io/instance: bitwardensecret
    app.kubernetes.io/part-of: sm-operator
    app.kubernetes.io/managed-by: kustomize
    app.kubernetes.io/created-by: sm-operator
  name: bitwardensecret
spec:
  organizationId: "cd864c42-0667-4521-afb0-aae600ef844c"
  secretName: database-credentials
  map:
    - bwSecretId: 2b4cf82d-7bb4-4f90-a391-b275008566eb
      secretKeyName: username
    - bwSecretId: 371a1632-c42e-4d01-85c8-b28800d967d0
      secretKeyName: password
  authToken:
    secretName: bw-auth-token
    secretKey: token
```

### Network policies

- Create a deny-all netwotk policy (in all namespaces)

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-all-traffic
  namespace: <namespace>
spec:
  podSelector: {}
  policyTypes:
  - Ingress
```

- Validate: 

```sh
curl -X POST -d "amount=10" http://api-public-layer.apps.hetzner.calopezb.com/pay

curl http://api-public-layer.apps.hetzner.calopezb.com
```

- Allow from ingress netwotk policy in public layer

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-from-openshift-ingress
  namespace: public-layer
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          network.openshift.io/policy-group: ingress
```

- Validate: 

```sh
curl -X POST -d "amount=10" http://api-public-layer.apps.hetzner.calopezb.com/pay

curl http://api-public-layer.apps.hetzner.calopezb.com
```

- Allow public into app layer

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-from-api-pods
  namespace: app-layer
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          kubernetes.io/metadata.name: public-layer
      podSelector:
        matchLabels:
          app: api
```

- Validate: 

```sh
curl -X POST -d "amount=10" http://api-public-layer.apps.hetzner.calopezb.com/pay

oc project public-layer

oc get pods

oc rsh <pod-id>
curl backend.app-layer:5000
```

- Allow database access

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-backend-port-5000
  namespace: data-layer
spec:
  podSelector:
    matchLabels:
      app: database
  policyTypes:
  - Ingress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          kubernetes.io/metadata.name: app-layer
      podSelector:
        matchLabels:
          app: backend
    ports:
    - protocol: TCP
      port: 5000
```

- Validate: 

```sh
curl -X POST -d "amount=10" http://api-public-layer.apps.hetzner.calopezb.com/pay
```





