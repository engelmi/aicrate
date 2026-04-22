#!/bin/bash

OCI_ARTIFACT_MOUNT_DIR="/var/oci-artifacts"
SKILL_DIR="${OCI_ARTIFACT_MOUNT_DIR}"/skills

for skill in "${SKILL_DIR}"/*; do
    tar -xf "${skill}" -C "/root/.claude/skills/"
done
