from flask_mail import Message
from flask import render_template

from osf_dashboard.utilities.log_helper import _log
from osf_dashboard.web.extensions import mail
from osf_dashboard.settings import ENV_DICT


def send_email(to_email, subject, template_path, template_vars, attachment_path=None):

    if not ENV_DICT['SEND_EMAIL']:
        print '++ sending emails is currently disabled in this environment. Enable SEND_EMAIL to allow email sending'
        return

    # email address that emails will be sent from
    from_email = ENV_DICT['MAIL_DEFAULT_SENDER']

    # render HTML from template
    page_html = render_template(template_path, **template_vars)

    msg = Message(subject=subject,
                  sender=from_email,
                  recipients=[to_email],
                  html=page_html)

    if attachment_path:
        with open(attachment_path, 'r') as f:
            msg.attach("osf-results.json", "text/plain", f.read())

    mail.send(msg)


def send_debug_email(to_email, attachment_path=None):
    t_vars = {
        'first_name': 'Test',
        'last_name': 'User'
    }
    send_email(to_email=to_email,
               subject='Hello',
               template_path='emails/test_email.html',
               template_vars=t_vars,
               attachment_path=attachment_path)


if __name__ == '__main__':
    from osf_dashboard.web.app import create_app
    app = create_app()
    with app.app_context():
        send_debug_email(
            to_email='maxhfowler@gmail.com',
            attachment_path='/Users/maxfowler/computer/projects/opensourcefeeds/data/test.json'
        )