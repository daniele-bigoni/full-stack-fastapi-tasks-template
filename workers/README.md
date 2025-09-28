# Workers

The workers defined here are stub of [Celery](https://docs.celeryq.dev/) workers defining
different tasks. Workers are started through the main docker compose file.

# Creating the development environment

Run

```console
uv venv --python 3.13
```

in the worker's directory. This will create the ``.venv`` folder.
Activate the environment by

```console
source .venv/bin/activate
```

Synchronize the environment with the ``uv.lock`` file:

```console
uv sync --frozen
```


# Updating workers dependencies

By default, the version of the stack pacakges are locked but not the hash, as this can change depending on the
packaging system that produces the wheels. 
When deploying it is best practice to lock also the hashes of the packages once they are made available 
on a repository.

To update the ``uv.lock`` files of the workers you must first start the [PyPi Server](../pypiserver/README.md)
and then run:

```console
uv lock --default-index http://127.0.0.1:8082 --index https://pypi.org/simple --upgrade
```