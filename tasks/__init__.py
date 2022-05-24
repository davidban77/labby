"""Collection point for all invoke tasks."""

from invoke import Collection
from tasks import check, docker

# Setup Invoke Task Collection
namespace = Collection(check, docker)
