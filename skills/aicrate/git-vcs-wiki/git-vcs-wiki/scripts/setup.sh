#!/bin/bash

python --version | python3 --version &> /dev/null
is_python_installed=$?
pip --version | pip3 --version &> /dev/null
is_pip_installed=$?

if [[ "${is_python_installed}" == "0" && "${is_pip_installed}" == "0" ]]; then
    echo "Python and pip are installed"
    exit 0
fi

if [[ -f /etc/os-release ]]; then
    . /etc/os-release
else
    echo "Cannot determine OS"
    exit 1
fi

pkgs=""
if [ "${is_python_installed}" != "0" ]; then
    pkgs="python3 "
fi
if [ "${is_pip_installed}" != "0" ]; then
    pkgs="python3-pip"
fi
case "$ID" in
    ubuntu)
        apt update
        apt install -y "${pkgs}"
        ;;
    fedora)
        dnf install -y "${pkgs}"
        ;;
    *)
        echo "Unknown distro: $ID"
        exit 1
        ;;
esac