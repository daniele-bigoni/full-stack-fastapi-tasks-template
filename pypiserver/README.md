# PyPi Server

This service allow to emulate a PyPi server serving the shared packages needed by the different parts 
of the stack.

Three main packages are available from the template:

* ``stack-datamodel``: containing all the [SQLModel](https://sqlmodel.tiangolo.com/) for the stack
* ``stack-settings``: containing the [Pydantic settings](https://docs.pydantic.dev/latest/api/pydantic_settings/) for the stack
* ``stack-shared-tasks``: definitions of shared [Celery tasks](https://docs.celeryq.dev/en/stable/index.html)

## Starting the PyPi Server

From the root folder of the project:

```console
docker compose -f docker-compose-pypi.yml up
```

## Loading packages to the server

The script ``update.sh`` allows for the automatic loading of all the packages 
in the folder ``packages`` to the running PyPi Server. From the root folder of the project run:

```console
./pypiserver/upload.sh
```