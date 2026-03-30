#!/bin/bash

OCI_ARTIFACT_MOUNT_DIR="/var/oci-artifacts"
SKILL_DIR="${OCI_ARTIFACT_MOUNT_DIR}"/skills

for dir in "${SKILL_DIR}"/*; do
    name=$(basename "${dir}")
    tar -xf "${dir}/${name}.tar" -C "/root/.claude/skills/"
done
