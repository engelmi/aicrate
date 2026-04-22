#!/bin/bash

OCI_ARTIFACT_MOUNT_DIR="/var/oci-artifacts"
AGENT_DIR="${OCI_ARTIFACT_MOUNT_DIR}"/agents

for agent in "${AGENT_DIR}"/*; do
    tar -xf "${agent}" -C "/root/.claude/agents/"
done
