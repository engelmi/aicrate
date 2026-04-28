import argparse

import aicrate.engine.podman as engine


def push_artifact(args: argparse.Namespace):
    artifact = args.artifact[0]
    engine.push_artifact(artifact)


def push_image(args: argparse.Namespace):
    image = args.image[0]
    engine.push_image(image)
