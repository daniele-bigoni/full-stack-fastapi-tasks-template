# SSO with FusionAuth

We use [FusionAuth](https://fusionauth.io/) to provide a standalone example of SSO authentication.

## The FusionAuth Server

The SSO server is configured in the file ``./kickstart/kickstart.json`` that contains:

* the definition of two applications associated to two different ``applicationId`` for ``appA`` and ``appB``
  (these must match the variables ``OAUTH_FUSIONAUTH_CLIENT_ID_APP_A`` and ``OAUTH_FUSIONAUTH_CLIENT_ID_APP_B``
  defined in the ``.env`` file).
* the client secrets for the two applications (these must match the variables ``OAUTH_FUSIONAUTH_CLIENT_SECRET_APP_A``
  and ``OAUTH_FUSIONAUTH_CLIENT_SECRET_APP_B`` defined in the ``.env`` file)
* the admin user for the FusionAuth server
* one user for each application (``richard@app-a.com`` and ``richard@app-b.com``) with the respective passwords

The FusionAuth server is started automatically with the other services of the stack.
To start the service by itself, one can run

```console
docker compose up fusionauth
```

The server can be reached at ``http://localhost:9011``.

## Backend

The backend provides the implementation of the APIs necessary to interact with the authentication server
on the routes ``/api/v1/auth/sso/fusionauth``. 
We refer to the documentation of the backend for more details.