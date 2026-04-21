#!/bin/bash -e

PACKAGE_NAME="aicrate"
SCRIPT_DIR="$(dirname "$(readlink -f "$0")")"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BUILD_DIR="${PROJECT_ROOT}/out"
WHEEL_BUILD_DIR="${BUILD_DIR}/pypi"

VERSION_SCRIPT="$SCRIPT_DIR/version.sh"
VERSION="$($VERSION_SCRIPT short)"
RELEASE="$($VERSION_SCRIPT release)"

clean() {
    echo "Cleaning build artifacts..."
    rm -rf "${BUILD_DIR}"
    rm -rf "$PROJECT_ROOT/build"
    rm -rf "$PROJECT_ROOT/aicrate.egg-info"
    $($VERSION_SCRIPT clean)
    echo "Clean complete"
}

generate_version_py() {
    echo "Generating version.py: Version=$VERSION Release=$RELEASE"

    sed \
        -e "s|@VERSION@|${VERSION}|g" \
        -e "s|@RELEASE@|${RELEASE}|g" \
        < "$PROJECT_ROOT/aicrate/version.py.in" \
        > "$PROJECT_ROOT/aicrate/version.py"
    
    echo "Generated version.py"
}

generate_pyproject() {
    echo "Generating pyproject.toml: Version=$VERSION"

    generate_version_py

    sed \
        -e "s|@VERSION@|${VERSION}|g" \
        < "$PROJECT_ROOT/pyproject.toml.in" \
        > "$PROJECT_ROOT/pyproject.toml"
    
    echo "Generated pyproject.toml"
}

build_archive() {
    echo "Building source distribution for $PACKAGE_NAME-$VERSION"

    generate_pyproject
    generate_spec
    
    mkdir -p "$BUILD_DIR"
    cd "$PROJECT_ROOT"
    git archive \
        --format=tar.gz \
        -o "${BUILD_DIR}"/aicrate-"${VERSION}".tar.gz \
        --prefix=aicrate-"${VERSION}"/aicrate/ \
        --add-file=aicrate/version.py \
        --prefix=aicrate-"${VERSION}"/ \
        --add-file=pyproject.toml \
        --add-file=aicrate.spec \
        HEAD
    
    echo "$BUILD_DIR/$PACKAGE_NAME-$VERSION.tar.gz"
}

build_wheel() {
    echo "Building Python wheel for $PACKAGE_NAME-$VERSION"

    generate_pyproject
    
    mkdir -p "$WHEEL_BUILD_DIR"
    cd "$PROJECT_ROOT"
    python3 -m build --wheel --outdir "$WHEEL_BUILD_DIR"
}

COMMAND=""
PRINT_SOURCE_PATH=false
USAGE="Usage: build.sh [--spec|--toml|--tar|--wheel|--clean]"
while [[ $# -gt 0 ]]; do
    case $1 in
        --spec)
            COMMAND="generate_spec"
            shift
            ;;
        --toml)
            COMMAND="generate_pyproject"
            shift
            ;;
        --tar)
            COMMAND="build_archive"
            shift
            ;;
        --wheel)
            COMMAND="build_wheel"
            shift
            ;;
        --clean)
            COMMAND="clean"
            shift
            ;;
        -h|--help)
            echo "$USAGE"
            exit 0
            ;;
        -*|--*)
            echo "Unknown option $1"
            echo "$USAGE"
            exit 1
            ;;
        *)
            echo "Unknown positional argument: $1"
            echo "$USAGE"
            exit 1
            ;;
    esac
done

if [ -z "$COMMAND" ]; then
    echo "No command given"
    echo "$USAGE"
    exit 1
fi

$COMMAND

exit 0
