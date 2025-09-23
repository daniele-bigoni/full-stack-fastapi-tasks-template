import secrets
import uuid
from datetime import timedelta
from typing import Annotated, Any, Dict, Union

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi_sso import create_provider, OpenID
from httpx import AsyncClient
from starlette.responses import RedirectResponse

from app import crud
from app.api.deps import CurrentUser, SessionDep, get_current_active_superuser
from app.core import security
from app.core.config import settings
from app.core.security import get_password_hash
from stack_datamodel import Message, NewPassword, Token, UserPublic, UserCreateEmailPassword
from app.utils import (
    generate_verification_token,
    generate_reset_password_email,
    send_email,
    verify_verification_token,
)

router = APIRouter(
    tags=["auth"],
    prefix='/auth'
)


def generate_access_token(
        user_id: uuid.UUID
) -> Token:
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return Token(
        access_token=security.create_access_token(
            user_id, expires_delta=access_token_expires
        )
    )


@router.post("/login/access-token")
def login_access_token(
    session: SessionDep, form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
) -> Token:
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    user = crud.authenticate(
        session=session, email=form_data.username, password=form_data.password
    )
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    elif not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return generate_access_token(user.id)


@router.post("/login/test-token", response_model=UserPublic)
def test_token(current_user: CurrentUser) -> Any:
    """
    Test access token
    """
    return current_user


@router.post("/password-recovery/{email}")
def recover_password(email: str, session: SessionDep) -> Message:
    """
    Password Recovery
    """
    user = crud.get_user_by_email(session=session, email=email)

    if not user:
        raise HTTPException(
            status_code=404,
            detail="The user with this email does not exist in the system.",
        )
    password_reset_token = generate_verification_token(email=email)
    email_data = generate_reset_password_email(
        email_to=user.email, email=email, token=password_reset_token
    )
    send_email(
        email_to=user.email,
        subject=email_data.subject,
        html_content=email_data.html_content,
    )
    return Message(message="Password recovery email sent")


@router.post("/reset-password/")
def reset_password(session: SessionDep, body: NewPassword) -> Message:
    """
    Reset password
    """
    d = verify_verification_token(token=body.token)
    if not d or d['expired']:
        raise HTTPException(status_code=400, detail="Invalid token")
    email = d['email']
    user = crud.get_user_by_email(session=session, email=email)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="The user with this email does not exist in the system.",
        )
    elif not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    hashed_password = get_password_hash(password=body.new_password)
    user.hashed_password = hashed_password
    session.add(user)
    session.commit()
    return Message(message="Password updated successfully")


@router.post(
    "/password-recovery-html-content/{email}",
    dependencies=[Depends(get_current_active_superuser)],
    response_class=HTMLResponse,
)
def recover_password_html_content(email: str, session: SessionDep) -> Any:
    """
    HTML Content for Password Recovery
    """
    user = crud.get_user_by_email(session=session, email=email)

    if not user:
        raise HTTPException(
            status_code=404,
            detail="The user with this username does not exist in the system.",
        )
    password_reset_token = generate_verification_token(email=email)
    email_data = generate_reset_password_email(
        email_to=user.email, email=email, token=password_reset_token
    )

    return HTMLResponse(
        content=email_data.html_content, headers={"subject:": email_data.subject}
    )


#######
# SSO #
#######

def get_access_token_html_response(
        access_token: Token
) -> HTMLResponse:
    html_content = f"""
        <html>
            <script>
                window.opener.postMessage({{"access_token": "{access_token.access_token}"}}, "*");
                window.close();
            </script>
        </html>
        """
    return HTMLResponse(content=html_content, status_code=200)


##################
# SSO FUSIONAUTH #
##################

FUSIONAUTH_PROVIDER_NAME = 'fusionauth'

fusionauth_discovery = dict(
    authorization_endpoint=settings.OAUTH_FUSIONAUTH_AUTHORIZE_URL,
    token_endpoint=settings.OAUTH_FUSIONAUTH_ACCESS_TOKEN_URL,
    userinfo_endpoint=settings.OAUTH_FUSIONAUTH_USERINFO_URL
)

def fusionauth_convert_openid(response: Dict[str, Any], _client: Union[AsyncClient, None]) -> OpenID:
    """Convert user information returned by FusionAuth"""
    return OpenID(
        id=response.get("sub"),
        email=response.get("email"),
        provider=FUSIONAUTH_PROVIDER_NAME
    )

FusionAuthSSOProvider = create_provider(
    name=FUSIONAUTH_PROVIDER_NAME,
    discovery_document=fusionauth_discovery,
    response_convertor=fusionauth_convert_openid,
    default_scope=['openid', 'email']
)

def get_fusionauth_sso(
        request: Request,
        fusionauth_client_id: str,
        fusionauth_client_secret_app: str,
        fusionauth_callback: str
) -> FusionAuthSSOProvider:
    sso = FusionAuthSSOProvider(
        fusionauth_client_id,
        fusionauth_client_secret_app,
        redirect_uri=request.url_for(fusionauth_callback),
        allow_insecure_http=True  # TODO: forbid in prod
    )
    sso.uses_pkce = True
    return sso


async def base_fusion_auth_login(
        request: Request,
        fusionauth_client_id: str,
        fusionauth_client_secret_app: str,
        fusionauth_callback: str
) -> RedirectResponse:
    async with get_fusionauth_sso(
            request,
            fusionauth_client_id=fusionauth_client_id,
            fusionauth_client_secret_app=fusionauth_client_secret_app,
            fusionauth_callback=fusionauth_callback
    ) as fusionauth_sso:
        return await fusionauth_sso.get_login_redirect()


async def base_fusionauth_callback(
        session: SessionDep,
        request: Request,
        fusionauth_client_id: str,
        fusionauth_client_secret_app: str,
        fusionauth_callback: str
) -> Token:
    async with get_fusionauth_sso(
            request,
            fusionauth_client_id=fusionauth_client_id,
            fusionauth_client_secret_app=fusionauth_client_secret_app,
            fusionauth_callback=fusionauth_callback
    ) as fusionauth_sso:
        user = await fusionauth_sso.verify_and_process(request, convert_response=True)
    if user is None:
        raise HTTPException(401, "Failed to fetch user information")
    if user.email is None:
        raise HTTPException(401, "Failed to fetch email information")

    # Create user if missing
    db_user = crud.get_user_by_email(session=session, email=user.email)
    if not db_user:
        user_create = UserCreateEmailPassword(
            email=user.email,
            sso_provider=user.provider,
            sso_openid=user.id,
            password=secrets.token_urlsafe(32)  # A random unknown password is set
        )
        db_user = crud.create_user_email_and_password(session=session, user_create=user_create)
        crud.activate_user(session=session, db_user=db_user)
    return generate_access_token(db_user.id)


########################
# SSO FUSIONAUTH APP A #
########################

@router.get("/sso/fusionauth/app-a/login")
async def fusionauth_login_app_a(
        request: Request,
        # We can't use the following "depends" because we need to create the instance in a with so that the pkce code
        # is created properly.
        #fusionauth_sso: FusionAuthSSOProvider = Depends(get_fusionauth_sso)
) -> RedirectResponse:
    return await base_fusion_auth_login(
        request,
        fusionauth_client_id=settings.OAUTH_FUSIONAUTH_CLIENT_ID_APP_A,
        fusionauth_client_secret_app=settings.OAUTH_FUSIONAUTH_CLIENT_SECRET_APP_A,
        fusionauth_callback="fusionauth_callback_app_a"
    )


@router.get("/sso/fusionauth/app-a/login-html")
async def fusionauth_login_html_app_a(
        request: Request,
        # We can't use the following "depends" because we need to create the instance in a with so that the pkce code
        # is created properly.
        #fusionauth_sso: FusionAuthSSOProvider = Depends(get_fusionauth_sso)
) -> RedirectResponse:
    return await base_fusion_auth_login(
        request,
        fusionauth_client_id=settings.OAUTH_FUSIONAUTH_CLIENT_ID_APP_A,
        fusionauth_client_secret_app=settings.OAUTH_FUSIONAUTH_CLIENT_SECRET_APP_A,
        fusionauth_callback="fusionauth_callback_html_app_a"
    )


@router.get("/sso/fusionauth/app-a/callback")
async def fusionauth_callback_app_a(
        session: SessionDep,
        request: Request,
        # We can't use the following "depends" because we need to create the instance in a with so that the pkce code
        # is created properly.
        # fusionauth_sso: FusionAuthSSOProvider = Depends(get_fusionauth_sso),
) -> Token:
    return await base_fusionauth_callback(
        session, request,
        fusionauth_client_id=settings.OAUTH_FUSIONAUTH_CLIENT_ID_APP_A,
        fusionauth_client_secret_app=settings.OAUTH_FUSIONAUTH_CLIENT_SECRET_APP_A,
        fusionauth_callback="fusionauth_callback_app_a"
    )


@router.get("/sso/fusionauth/app-a/callback-html")
async def fusionauth_callback_html_app_a(
        session: SessionDep,
        request: Request,
) -> HTMLResponse:
    access_token = await base_fusionauth_callback(
        session, request,
        fusionauth_client_id=settings.OAUTH_FUSIONAUTH_CLIENT_ID_APP_A,
        fusionauth_client_secret_app=settings.OAUTH_FUSIONAUTH_CLIENT_SECRET_APP_A,
        fusionauth_callback="fusionauth_callback_html_app_a"
    )
    return get_access_token_html_response(access_token)


########################
# SSO FUSIONAUTH APP B #
########################

@router.get("/sso/fusionauth/app-b/login")
async def fusionauth_login_app_b(
        request: Request,
        # We can't use the following "depends" because we need to create the instance in a with so that the pkce code
        # is created properly.
        #fusionauth_sso: FusionAuthSSOProvider = Depends(get_fusionauth_sso)
) -> RedirectResponse:
    return await base_fusion_auth_login(
        request,
        fusionauth_client_id=settings.OAUTH_FUSIONAUTH_CLIENT_ID_APP_B,
        fusionauth_client_secret_app=settings.OAUTH_FUSIONAUTH_CLIENT_SECRET_APP_B,
        fusionauth_callback="fusionauth_callback_app_b"
    )


@router.get("/sso/fusionauth/app-b/login-html")
async def fusionauth_login_html_app_b(
        request: Request,
        # We can't use the following "depends" because we need to create the instance in a with so that the pkce code
        # is created properly.
        #fusionauth_sso: FusionAuthSSOProvider = Depends(get_fusionauth_sso)
) -> RedirectResponse:
    return await base_fusion_auth_login(
        request,
        fusionauth_client_id=settings.OAUTH_FUSIONAUTH_CLIENT_ID_APP_B,
        fusionauth_client_secret_app=settings.OAUTH_FUSIONAUTH_CLIENT_SECRET_APP_B,
        fusionauth_callback="fusionauth_callback_html_app_b"
    )


@router.get("/sso/fusionauth/app-b/callback")
async def fusionauth_callback_app_b(
        session: SessionDep,
        request: Request,
        # We can't use the following "depends" because we need to create the instance in a with so that the pkce code
        # is created properly.
        # fusionauth_sso: FusionAuthSSOProvider = Depends(get_fusionauth_sso),
) -> Token:
    return await base_fusionauth_callback(
        session, request,
        fusionauth_client_id=settings.OAUTH_FUSIONAUTH_CLIENT_ID_APP_B,
        fusionauth_client_secret_app=settings.OAUTH_FUSIONAUTH_CLIENT_SECRET_APP_B,
        fusionauth_callback="fusionauth_callback_app_b"
    )


@router.get("/sso/fusionauth/app-b/callback-html")
async def fusionauth_callback_html_app_b(
        session: SessionDep,
        request: Request,
) -> HTMLResponse:
    access_token = await base_fusionauth_callback(
        session, request,
        fusionauth_client_id=settings.OAUTH_FUSIONAUTH_CLIENT_ID_APP_B,
        fusionauth_client_secret_app=settings.OAUTH_FUSIONAUTH_CLIENT_SECRET_APP_B,
        fusionauth_callback="fusionauth_callback_html_app_b"
    )
    return get_access_token_html_response(access_token)