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

## Unnstall

- Open a terminal
- Login into OpenShift
- Run installation:
```sh
CLUSTER_DOMAIN=$(oc whoami --show-server | sed 's~https://api\.~~' | sed 's~:.*~~')
ansible-playbook installation/uninstall.yaml -e "ocp_host=$CLUSTER_DOMAIN"
```