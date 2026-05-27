# AgentArmy OTel Collector — sidecar + standalone modes baked into one image.
# Base: otel/opentelemetry-collector-contrib pinned by digest (CWE-1357: no
# floating tags in production builds). Bumped per the upstream release cycle.
FROM otel/opentelemetry-collector-contrib:0.96.0@sha256:7ef2a2ff46b9e432321fdd63df104bfeedaf7b4e276950f42c634d0f23521fc4

# Bake both configs at well-known paths. The base image is distroless-adjacent
# (no /bin/sh), so mode selection happens at deploy time via the `command:`
# override in the compose file or k8s args — not via a shell wrapper.
#   - standalone (default CMD below): the fleet's terminal collector
#   - sidecar: override CMD to use sidecar.yaml
COPY config/sidecar.yaml    /etc/otelcol-contrib/sidecar.yaml
COPY config/standalone.yaml /etc/otelcol-contrib/standalone.yaml

# OTLP ingress (gRPC + HTTP), Prometheus self-scrape, health-check.
EXPOSE 4317 4318 8888 13133

# Non-root runtime (CWE-269). UID 10001 is the upstream contrib image's
# built-in non-root user; declaring it again here makes the security posture
# explicit (and satisfies static scanners that can't introspect the base).
USER 10001

# Inherit ENTRYPOINT=/otelcol-contrib from the base. Provide standalone as
# the default CMD; compose / k8s can override with the sidecar config path.
CMD ["--config=/etc/otelcol-contrib/standalone.yaml"]
