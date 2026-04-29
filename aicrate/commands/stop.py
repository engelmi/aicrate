import argparse

import aicrate.engine.podman as engine


def stop(args: argparse.Namespace):
    pod_name = str(args.pod[0])
    if not pod_name.startswith("aicrate"):
        raise Exception("Can only stop aicrate pods with 'aicrate-' prefix")

    engine.stop_pod(pod_name)
