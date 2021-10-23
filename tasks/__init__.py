"""Collection point for all invoke tasks."""

from invoke import Collection
from tasks import tests

# Setup Invoke Task Collection
namespace = Collection(tests)
