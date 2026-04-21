#!/bin/bash

SCRIPT_DIR=$(dirname "$(readlink -f "$0")")

source "${SCRIPT_DIR}"/common.sh

push_skills() {
    local artifacts=$(aicrate ls --skills --json | jq -r '.artifacts[].Name')
    for artifact in $artifacts; do
        echo "Pushing artifact ${artifact} to OCI registry..." 
        aicrate push "${artifact}"
    done
}

push_agents() {
    local artifacts=$(aicrate ls --agents --json | jq -r '.artifacts[].Name')
    for artifact in $artifacts; do
        echo "Pushing artifact ${artifact} to OCI registry..." 
        aicrate push "${artifact}"
    done
}

push_artifacts() {
    local artifacts=$(aicrate ls --json | jq -r '.artifacts[].Name')
    for artifact in $artifacts; do
        echo "Pushing artifact ${artifact} to OCI registry..." 
        aicrate push "${artifact}"
    done
}


push_all() {
    push_artifacts
}



BASIC_USAGE=$(cat <<'EOF'
CLI to push OCI artifacts and images to registry

Usage:
    push.sh [command]

Available commands:
    claude      Push the OCI base image with claude CLI setup
    skills      Push OCI artifacts for all skills in aicrate
    agents      Push OCI artifacts for all agents in aicrate
    artifacts   Push OCI artifacts for all skills and agents in aicrate
    clean       Remove all temporary files

Flags:
    -h, --help  Print help
EOF
)

COMMAND=""
case $1 in
    claude)
        COMMAND=claude
        shift
        ;;
    skills)
        COMMAND=push_skills
        shift
        ;;
    agents)
        COMMAND=push_agents
        shift
        ;;
    artifacts)
        COMMAND=push_artifacts
        shift
        ;;
    -h|--help)
        echo "${BASIC_USAGE}"
        exit 0
        ;;
    *)
        echo "Unknown positional argument: $1"
        echo "${BASIC_USAGE}"
        exit 1
        ;;
esac

$COMMAND "$@"
