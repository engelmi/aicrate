#!/bin/bash

OCI_ARTIFACT_MOUNT_DIR="/var/oci-artifacts"
AGENT_DIR="${OCI_ARTIFACT_MOUNT_DIR}"/agents

for agent in "${AGENT_DIR}"/*; do
    [[ -e "${agent}" ]] || continue
    tar -xf "${agent}" -C "/home/claude/.claude/agents/"
done
