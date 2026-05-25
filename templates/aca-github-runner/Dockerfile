# GitHub Actions self-hosted runner image for Azure Container Apps Jobs.
#
# Design decisions:
#   - Ubuntu 22.04 base (glibc, apt, systemd-free) — matches ubuntu-latest runner
#     toolchain expectations closely enough for bash/python/node workflows.
#   - Pin the runner version via ARG so CI can override without editing this file:
#       docker build --build-arg RUNNER_VERSION=2.317.0 .
#   - Non-root `runner` user (uid 1001). The runner binary requires non-root by default;
#     the entrypoint does NOT use `--allow-root`.
#   - No Docker-in-Docker: DIND requires privileged containers which Azure Container
#     Apps does not support. Workflows must not use `docker build` or `services:`.
#     Python/Node toolchains are fetched at job time by actions/setup-python and
#     actions/setup-node (both download to $RUNNER_TOOL_CACHE, no root needed).
#   - installdependencies.sh is run at build time (not entrypoint) so the image is
#     self-contained and ephemeral cold-start is fast.
#   - The runner registers as ephemeral (--ephemeral) — it deregisters after one job,
#     and the container exits cleanly. KEDA then scales it to zero.

ARG RUNNER_VERSION=2.317.0
ARG UBUNTU_VERSION=22.04

FROM ubuntu:${UBUNTU_VERSION}

ARG RUNNER_VERSION

LABEL org.opencontainers.image.title="aca-github-runner" \
      org.opencontainers.image.description="Ephemeral self-hosted GitHub Actions runner for Azure Container Apps Jobs" \
      org.opencontainers.image.version="${RUNNER_VERSION}"

# ---------------------------------------------------------------------------
# System dependencies
# ---------------------------------------------------------------------------
# ca-certificates  — TLS verification for GitHub API calls
# curl             — used by the entrypoint + setup actions
# jq               — parse registration token response in entrypoint.sh
# git              — required by actions/checkout
# unzip            — needed by some composite actions
# sudo             — some setup-* actions invoke sudo internally; the runner user
#                    is granted passwordless sudo in the adduser step below.
# libssl-dev, libicu-dev — runner binary dependencies on Ubuntu 22.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      ca-certificates \
      curl \
      jq \
      git \
      unzip \
      sudo \
      libssl-dev \
      libicu-dev \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

# ---------------------------------------------------------------------------
# Runner user (non-root, uid 1001)
# ---------------------------------------------------------------------------
RUN useradd -m -u 1001 -s /bin/bash runner \
 && echo "runner ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers.d/runner \
 && chmod 0440 /etc/sudoers.d/runner

# ---------------------------------------------------------------------------
# Install the GitHub Actions runner binary
# ---------------------------------------------------------------------------
WORKDIR /home/runner/actions-runner

RUN curl -fsSL \
      "https://github.com/actions/runner/releases/download/v${RUNNER_VERSION}/actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz" \
      -o runner.tar.gz \
 && tar xzf runner.tar.gz \
 && rm runner.tar.gz \
 # Install runner dependencies (libicu, liblttng, etc.) — runs as root here
 && ./bin/installdependencies.sh \
 && chown -R runner:runner /home/runner/actions-runner

# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
# Strip any CRLF from Windows checkouts — a CRLF shebang causes exit 127.
RUN sed -i 's/\r$//' /usr/local/bin/entrypoint.sh \
 && chmod 0755 /usr/local/bin/entrypoint.sh

# Drop to non-root for runtime
USER runner
WORKDIR /home/runner/actions-runner

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
