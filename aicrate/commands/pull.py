import argparse

import aicrate.engine.podman as engine


def pull_artifact(args: argparse.Namespace):
    artifact = args.artifact[0]
    engine.pull_artifact(artifact)


def pull_image(args: argparse.Namespace):
    image = args.image[0]
    engine.pull_image(image)
