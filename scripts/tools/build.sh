#!/bin/bash

SCRIPT_DIR=$(dirname "$(readlink -f "$0")")

source "${SCRIPT_DIR}"/common.sh

build_skills() {
    mapfile -t available_skills < <(list_available_skills)
    for skill in "${available_skills[@]}"; do
        local subgroup=$(dirname "$skill")
        local path=$(realpath "${SKILLS_DIR}/${skill}")
        echo "Building skill ${path}..."
        aicrate build skill --dir "${path}" --oci-subgroup "${subgroup}"
    done
}

build_agents() {
    mapfile -t available_agents < <(list_available_agents)
    for agent in "${available_agents[@]}"; do
        local subgroup=$(basename $(realpath $(dirname "${AGENT_DIR}/${agent}")/..))
        local path=$(realpath "${AGENT_DIR}/${agent}")
        echo "Building agent ${path}..."
        aicrate build agent --dir "${path}" --oci-subgroup "${subgroup}"
    done
}

build_artifacts() {
    build_skills
    build_agents
}


build_all() {
    build_artifacts
}



BASIC_USAGE=$(cat <<'EOF'
CLI to build OCI artifacts and images

Usage:
    build.sh [command]

Available commands:
    claude      Build the OCI base image with claude CLI setup
    skills      Build OCI artifacts for all skills in aicrate
    agents      Build OCI artifacts for all agents in aicrate
    artifacts   Build OCI artifacts for all skills and agents in aicrate
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
        COMMAND=build_skills
        shift
        ;;
    agents)
        COMMAND=build_agents
        shift
        ;;
    artifacts)
        COMMAND=build_artifacts
        shift
        ;;
    clean)
        COMMAND=clean
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
