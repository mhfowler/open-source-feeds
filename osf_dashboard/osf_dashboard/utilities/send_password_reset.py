import random
import string

from osf_dashboard.utilities.log_helper import _log
from osf_dashboard.utilities.email_helper import send_email
from osf_dashboard.models import User, PasswordResetLink
from osf_dashboard.settings import ENV_DICT
from osf_dashboard.web.extensions import db


def send_password_reset(user):
    """
    helper function which sends a password reset email to the inputted user
    :param user: User object to send an email to
    :return: None
    """
    _log('++ sending password reset email for: {} {}'.format(user.first_name, user.last_name))
    secret_string = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(20))

    # if local set the domain to localhost
    if ENV_DICT['ENVIRON'] == 'LOCAL':
        secret_link = 'http://localhost:8080/reset/{}/'.format(secret_string)
    # otherwise use the subdomain of the tenancy
    else:
        secret_link = 'http://{}.cpisearch.io/reset/{}/'.format(user.tenancy, secret_string)

    reset_link_object = PasswordResetLink(
        user_id=user.user_id,
        secret_link=secret_string,
        tenancy=user.tenancy,
    )
    db.session.add(reset_link_object)
    db.session.commit()
    send_email(
        to_email=user.email,
        subject='SuccessKit Password Reset',
        template_path='emails/password_reset_email.html',
        template_vars={
            'user': user,
            'secret_link': secret_link
        }
    )


if __name__ == '__main__':
    from osf_dashboard.web.app import create_app
    app = create_app()
    with app.app_context():
        user = db.session.query(User).filter(
            User.email == 'test@gmail.com',
        ).one_or_none()
        send_password_reset(user)