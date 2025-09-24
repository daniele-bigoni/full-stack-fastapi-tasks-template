# Workers

The workers defined here are stub of [Celery](https://docs.celeryq.dev/) workers defining
different tasks. Workers are started through the main docker compose file.

# Updating workers dependencies

To update the ``uv.lock`` files of the workers you must first start the [PyPi Server](../pypiserver/README.md)
and then run:

```console
uv lock --default-index http://127.0.0.1:8082 --index https://pypi.org/simple --upgrade
```