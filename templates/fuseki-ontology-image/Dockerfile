# Apache Jena Fuseki + the AgentArmy ontology toolchain, as one image.
#
# Built from eclipse-temurin (canonical JRE) + the official Apache Jena Fuseki
# and Jena CLI tarballs (archive.apache.org) — no third-party Docker image
# dependency. This keeps engine fixes a single-line tarball-URL bump.
#
# Adds: Jena CLI tools (`shacl`/`sparql`/`riot`/`tdb2.tdbloader`), Python +
# pyshacl + rdflib, and ROBOT (OBO workflow). Implements the AgentArmy ontology
# pipeline (strict SHACL sieve → store; SPARQL CONSTRUCT → emit).
#
# Pairs with: ARC-ADR-019 (Ontology + Reasoning Layer); knowledge-ontology
# agents (ontologist-ufo / ontologist-bfo / ontologist-generalist /
# knowledge-engineer / taxonomist).

ARG JENA_VERSION=5.5.0
FROM eclipse-temurin:21-jre

USER root
ARG JENA_VERSION
RUN set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends curl python3 python3-pip ca-certificates; \
    # Apache Jena Fuseki — fuseki-server + fuseki.war + configs.
    curl -fsSL "https://archive.apache.org/dist/jena/binaries/apache-jena-fuseki-${JENA_VERSION}.tar.gz" -o /tmp/fuseki.tgz; \
    mkdir -p /opt/fuseki; \
    tar -xzf /tmp/fuseki.tgz -C /opt/fuseki --strip-components=1; \
    rm /tmp/fuseki.tgz; \
    # Apache Jena CLI — riot/sparql/shacl/tdb2.tdbloader (same version).
    curl -fsSL "https://archive.apache.org/dist/jena/binaries/apache-jena-${JENA_VERSION}.tar.gz" -o /tmp/jena.tgz; \
    mkdir -p /opt/jena; \
    tar -xzf /tmp/jena.tgz -C /opt/jena --strip-components=1; \
    rm /tmp/jena.tgz; \
    # Python ontology toolkit (a second SHACL impl + scripting).
    pip install --break-system-packages --no-cache-dir pyshacl rdflib; \
    # ROBOT — OBO ontology workflow (reason/reduce/repair/convert/validate/diff).
    curl -fsSL "https://github.com/ontodev/robot/releases/latest/download/robot.jar" -o /opt/robot.jar; \
    printf '#!/bin/sh\nexec java -jar /opt/robot.jar "$@"\n' > /usr/local/bin/robot; \
    chmod +x /usr/local/bin/robot; \
    # Non-root runtime user (no fixed UID — eclipse-temurin's noble base may
    # already use UID 1000 for `ubuntu`, which collides with useradd -u 1000).
    groupadd -r fuseki; \
    useradd -r -g fuseki -m -d /home/fuseki fuseki; \
    rm -rf /var/lib/apt/lists/*

ENV PATH="/opt/jena/bin:/opt/fuseki:${PATH}" \
    JAVA_OPTS="-Xms256m -Xmx1g"

# AgentArmy pipeline surface: entrypoint dispatch + sieve/emit scripts + fixtures.
COPY entrypoint.sh /opt/agentarmy/entrypoint.sh
COPY scripts /opt/agentarmy/scripts
COPY fixtures /opt/agentarmy/fixtures
RUN chmod +x /opt/agentarmy/entrypoint.sh /opt/agentarmy/scripts/*.sh \
 && mkdir -p /fuseki/databases /shapes /ontologies \
 && chown -R fuseki:fuseki /opt/agentarmy /opt/fuseki /fuseki /shapes /ontologies

VOLUME ["/fuseki/databases", "/shapes", "/ontologies"]
EXPOSE 3030

HEALTHCHECK --interval=15s --timeout=5s --start-period=45s --retries=5 \
  CMD curl -fsS "http://127.0.0.1:3030/\$/ping" || exit 1

# Drop privileges — runtime as `fuseki` (CWE-269: root only during build).
USER fuseki
WORKDIR /fuseki

# server (default, TDB2 /knowledge dataset) | sieve | emit | shacl | sparql |
# riot | robot | pyshacl | <any command>
ENTRYPOINT ["/opt/agentarmy/entrypoint.sh"]
CMD ["server"]
