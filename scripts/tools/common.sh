#!/bin/bash

SCRIPT_DIR=$(dirname "$(readlink -f "$0")")
ROOT_DIR="${SCRIPT_DIR}"/../..

SKILLS_DIR="${ROOT_DIR}"/skills
ANTHROPIC_SKILLS_REPO="anthropic"
ANTHROPIC_SKILLS_DIR="${SKILLS_DIR}"/"${ANTHROPIC_SKILLS_REPO}"
OBRA_SKILLS_REPO="obra"
OBRA_SKILLS_DIR="${SKILLS_DIR}"/"${OBRA_SKILLS_REPO}"
MKEMEL_SKILLS_REPO="mkemel"
MKEMEL_SKILLS_DIR="${SKILLS_DIR}"/"${MKEMEL_SKILLS_REPO}"

AGENT_DIR="${ROOT_DIR}"/agents
AGENCY_AGENT_REPO="agency"
AGENCY_AGENT_DIR="${AGENT_DIR}"/"${AGENCY_AGENT_REPO}"

list_available_skills() {
    for dir in "${MKEMEL_SKILLS_DIR}"/*; do
        name=$(basename "${dir}")
        echo "${MKEMEL_SKILLS_REPO}/${name}"
    done
    
    for dir in "${ANTHROPIC_SKILLS_DIR}"/*; do
        name=$(basename "${dir}")
        echo "${ANTHROPIC_SKILLS_REPO}/${name}"
    done

    for dir in "${OBRA_SKILLS_DIR}"/*; do
        name=$(basename "${dir}")
        echo "${OBRA_SKILLS_REPO}/${name}"
    done
}

list_available_agents() {
    for dir in "${AGENCY_AGENT_DIR}"/*; do
        if [[ -d "${dir}" ]]; then
            for category in "${dir}"/*; do
                local path=$(realpath "${category}")
                local agent=$(basename "${path}")
                local category=$(basename "$(dirname ${path})")
                local provider_path=$(realpath "$(dirname "${path}")/..")
                local subgroup=$(basename "${provider_path}")
                echo "${subgroup}/${category}/${agent}"
            done
        fi
    done
}
