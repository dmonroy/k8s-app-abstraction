# k8s-app-abstraction

Experimental abstraction layer for application deployment to kubernetes

## Goal

Simplify application deployment manifests.

## Whishlist

Not actual requirements but rather the owner's ideal feature set:

- Simple declarative manifests
  - simplified yaml interface
  - Separate config from manifest
- Advanced Yaml
  - include local and remote yaml
  - inheritance
  - templating
- Python API for low-level customization
  - Allows imperative approach to manifests
- Use helm under the hood
  - Release Management & Revision Control
  - Hooks
- Ingress routing
- Kubernetes version agnostic
- testability
- python plugin support

## Example deployment manifests

- Backend service with single replica:

```yaml
# k8s/worker.yml
# Defaults:
# - 1 replica
# - startup command from docker image
deployments:
  worker:
    image: voting/worker
```

- HTTP service exposing port 80 and HTTP GET healthcheck:

```yaml
# k8s/frontend.yml
# Healthcheck performs HTTP GET against /index.html for all probes
# Exposes the container port 80 to the service's port 80
deployments:
  frontend:
    image: voting/frontend
    expose:
      ports:
        - 80:80
    healthchecks:
      - get: /index.html
```

- Statefulsets with internally exposed port (type: ClusterIP)

```yaml
statefulsets:
  postgres:
    image: postgres:latest
    replicas: 1
    expose:
      ports:
        - scope: internal
          port: 5432
```

- Multiple deployments on single file with resource defaults and dependencies:

```yaml
# k8s/backend.yml
# Healthcheck performs HTTP GET against /index.html for all probes
# Exposes the container port 80 to the service's port 80
deployments:
  @defaults:
    image: voting/backend
    expose:
      ports:
        - 80:8000
    healthchecks:
      - get: /healthz

  api:
    command: python /app/api-service.py
    dependencies:
      - tcp: {{ resolve(postgres) }}:5432

  websocket-server:
    command: npm start
    dependencies:
      - exec: redis-cli -h {{ resolve(redis-ha) }} -p 6379 PING
        delay: 5
      - tcp: {{ resolve(postgres) }}:5432
```

- Multiple cronjobs with custom command, and environment variables:

```yaml
# k8s/cronjobs.yml
cronjobs:
  @defaults:
    image: voting/cronjobs
    environment:
      FOO: bar

  email-daily-updates:
    command: python /app/email-daily-update.py
    schedule: 0 8 * * TUE-SUN

  email-weekly-updates:
    command: python /app/email-weekly-update.py
    schedule: 0 8 * * MON
```

- Include base manifests from relative, absolute or remote locations, then
override or extend:

```yaml
include:
  - ~/company-defaults.yml
  - k8s/globals.yml
  - http://my.org/manifests/redis-ha.yml#da0706d88c2577f016937aeb27725a69
  - k8s/frontend.yml
  - k8s/backend.yml
  - k8s/cronjobs.yml
  - k8s/environments/{{ env["ENVIRONMENT_NAME"] }}.yml

deployments:
  frontend:
    dependencies:
      - get: http://{{ resolve(api) }}/healthz
      - ws: ws://{{ resolve(websocket-server) }}/
```
