import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import emails  # type: ignore
import jwt
from jinja2 import Template
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError

from app.core import security
from app.core.config import settings
from stack_datamodel import User

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class EmailData:
    html_content: str
    subject: str


def render_email_template(*, template_name: str, context: dict[str, Any]) -> str:
    template_str = (
        Path(__file__).parent / "email-templates" / "build" / template_name
    ).read_text()
    html_content = Template(template_str).render(context)
    return html_content


def send_email(
    *,
    email_to: str,
    subject: str = "",
    html_content: str = "",
) -> None:
    assert settings.emails_enabled, "no provided configuration for email variables"
    message = emails.Message(
        subject=subject,
        html=html_content,
        mail_from=(settings.EMAILS_FROM_NAME, settings.EMAILS_FROM_EMAIL),
    )
    smtp_options = {"host": settings.SMTP_HOST, "port": settings.SMTP_PORT}
    if settings.SMTP_TLS:
        smtp_options["tls"] = True
    elif settings.SMTP_SSL:
        smtp_options["ssl"] = True
    if settings.SMTP_USER:
        smtp_options["user"] = settings.SMTP_USER
    if settings.SMTP_PASSWORD:
        smtp_options["password"] = settings.SMTP_PASSWORD.get_secret_value()
    response = message.send(to=email_to, smtp=smtp_options)
    logger.info(f"send email result: {response}")


def generate_test_email(email_to: str) -> EmailData:
    project_name = settings.PROJECT_NAME
    subject = f"{project_name} - Test email"
    html_content = render_email_template(
        template_name="test_email.html",
        context={"project_name": settings.PROJECT_NAME, "email": email_to},
    )
    return EmailData(html_content=html_content, subject=subject)


def generate_reset_password_email(email_to: str, email: str, token: str) -> EmailData:
    project_name = settings.PROJECT_NAME
    subject = f"{project_name} - Password recovery for user {email}"
    link = f"{settings.FRONTEND_HOST}/reset-password?token={token}"
    html_content = render_email_template(
        template_name="reset_password.html",
        context={
            "project_name": settings.PROJECT_NAME,
            "username": email,
            "email": email_to,
            "valid_hours": settings.EMAIL_RESET_TOKEN_EXPIRE_HOURS,
            "link": link,
        },
    )
    return EmailData(html_content=html_content, subject=subject)


def generate_new_account_mail_verification_email(
        email_to: str,
        activation_token: str,
        activation_token_expire_minutes: int
) -> EmailData:
    project_name = settings.PROJECT_NAME
    subject = f"{project_name} - email verification"
    html_content = render_email_template(
        template_name="new_account_mail_verification.html",
        context={
            "project_name": settings.PROJECT_NAME,
            "email": email_to,
            "link": settings.FRONTEND_HOST + '/activate' + f"?token={activation_token}",
            "activation_token_expire_minutes": activation_token_expire_minutes,
        }
    )
    return EmailData(html_content=html_content, subject=subject)


def generate_new_account_email(
    email_to: str, username: str
) -> EmailData:
    project_name = settings.PROJECT_NAME
    subject = f"{project_name} - New account for user {username}"
    html_content = render_email_template(
        template_name="new_account.html",
        context={
            "project_name": settings.PROJECT_NAME,
            "username": username,
            "email": email_to,
            "link": settings.FRONTEND_HOST,
        },
    )
    return EmailData(html_content=html_content, subject=subject)


def send_new_activation_token(user: User):
    activation_token = generate_verification_token(str(user.email))
    if settings.emails_enabled and user.email:
        email_data = generate_new_account_mail_verification_email(
            email_to=str(user.email),
            activation_token=activation_token,
            activation_token_expire_minutes=settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_MINUTES
        )
        send_email(
            email_to=str(user.email),
            subject=email_data.subject,
            html_content=email_data.html_content,
        )


def generate_verification_token(email: str) -> str:
    delta = timedelta(minutes=settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_MINUTES)
    now = datetime.now(timezone.utc)
    expires = now + delta
    exp = expires.timestamp()
    encoded_jwt = jwt.encode(
        {"exp": exp, "nbf": now, "sub": email},
        settings.SECRET_KEY,
        algorithm=security.ALGORITHM,
    )
    return encoded_jwt


def verify_verification_token(token: str) -> dict[str, Any] | None:
    """
    Args:
        token: JWT token

    Returns:
        dict: dictionary containing the email associated to the token and whether the token was expired or not
    """
    try:
        decoded_token = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[security.ALGORITHM],
            require=["exp", "nbf"],
            options=dict(
                verify_exp=True,
                verify_nbf=True
            )
        )
        return {'email': str(decoded_token["sub"]), 'expired': False}
    except ExpiredSignatureError:
        try:
            decoded_token = jwt.decode(
                token, settings.SECRET_KEY, algorithms=[security.ALGORITHM],
                require=["exp", "nbf"],
                options=dict(
                    verify_exp=False,
                    verify_nbf=True
                )
            )
            return {'email': str(decoded_token["sub"]), 'expired': True}
        except InvalidTokenError:
            return None
    except InvalidTokenError:
        return None
