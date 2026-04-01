#!/bin/bash

OCI_ARTIFACT_MOUNT_DIR="/var/oci-artifacts"
AGENT_DIR="${OCI_ARTIFACT_MOUNT_DIR}"/agents

for dir in "${AGENT_DIR}"/*; do
    name=$(basename "${dir}"/*.tar)
    tar -xf "${dir}/${name}." -C "/root/.claude/agents/"
done
