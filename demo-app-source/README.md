# Demo App

This python app is used to create a scenario with the following components:

- API
- Backend
- Database

It is a single image that configures desired behavior based on environment variables.

The expected flow is:

CURL make payment -> API -> Backend -> Database -> Backend -> API

## Build Image

```sh
# Create image
podman build -t demo-app:1.0 . 

# Tag and push into quay (optional)
podman tag  demo-app:1.0 quay.io/calopezb/demo-app:1.0
podman push quay.io/calopezb/demo-app:1.0
```

## Run with Podman

- Run

```sh
podman network create demo_net

# Run Database
podman run -d --name database --network demo_net -e SERVICE_TYPE=db demo-app:1.0 

# Run Backend
podman run -d --name backend --network demo_net -e SERVICE_TYPE=backend -e DB_URL=http://database:5000 -e DB_USER=dbuser -e DB_PASS=secure-password demo-app:1.0

# Run API
podman run -d -p 8080:5000 --network demo_net --name api -e SERVICE_TYPE=api -e BACKEND_URL=http://backend:5000  demo-app:1.0
```

- Test

```sh
curl localhost:8080

curl -X POST -d "amount=10" localhost:8080/pay
```

- Cleanup

```sh
# Stop and delete containers
podman rm --force database backend api

# Remove network
podman network rm demo_net
```



