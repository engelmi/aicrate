#!/bin/bash -e

VERSION="0.3.0"
RELEASE="1"
IS_RELEASE="1"
RELEASE_FILE=$(dirname "$(readlink -f "$0")")/RELEASE

function short(){
    echo ${VERSION}
}

function long(){
    echo "$(short)-$(release)"
}

function release(){
    if [ -f "${RELEASE_FILE}" ]; then
        RELEASE="$(cat ${RELEASE_FILE})"
    else
        if [ $IS_RELEASE == "0" ]; then
            RELEASE="0.$(date +%04Y%02m%02d%02H%02M).git$(git rev-parse --short ${GITHUB_SHA:-HEAD})"
        fi
        echo ${RELEASE} > ${RELEASE_FILE}
    fi
    echo $RELEASE
}

function clean(){
    rm -f "${RELEASE_FILE}"
}

[ -z $1 ] && short || $1