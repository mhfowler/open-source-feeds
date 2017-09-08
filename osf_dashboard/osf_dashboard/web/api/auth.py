import datetime

from flask import request, jsonify, Blueprint
from werkzeug.security import check_password_hash, generate_password_hash

from osf_dashboard.utilities.token_helper import generate_auth_token
from osf_dashboard.utilities.auth_helper import authentication_required
from osf_dashboard.utilities.log_helper import _log
from osf_dashboard.utilities.send_password_reset import send_password_reset
from osf_dashboard.models import User, PasswordResetLink
from osf_dashboard.settings import PASSWORD_RESET_LINK_EXPIRATION_DAYS, TEMPLATE_DIR
from osf_dashboard.web.extensions import db


def get_auth_blueprint():

    # blueprint for these routes
    auth_blueprint = Blueprint('auth_blueprint', __name__, template_folder=TEMPLATE_DIR)

    @auth_blueprint.route('/api/currentUser/', methods=['GET'])
    @authentication_required
    def api_get_current_user(**kwargs):
        """
        endpoint to return the currently logged in User

        See authentication_required decorator to see how current_user is supplied as an argument to
        all wrapped functions via kwargs
        """
        response = jsonify({
            'currentUser': kwargs['current_user'].to_dict(),
        })
        response.status_code = 200
        return response

    @auth_blueprint.route('/api/auth/', methods=['POST'])
    def auth_token_api():
        """
        endpoint to get an authentication token using email and password
        """
        data = request.get_json()
        if not data:
            response = jsonify({
                'success': False,
                'message': 'Missing request body'
            })
            response.status_code = 422
            return response

        # process argument
        login_type = data.get('auth_type')
        email = data.get('email').strip().lower()
        password = data.get('password')

        if not login_type or login_type not in ['email']:
            response = jsonify({
                'success': False,
                'message': 'Invalid auth_type'
            })
            response.status_code = 422
            return response

        # email authentication
        elif login_type == 'email':
            if not email:
                response = jsonify({
                    'success': False,
                    'message': 'Must provide email when auth_type is "email"'
                })
                response.status_code = 422
                return response
            user = db.session.query(User).filter(User.email == email, User.deleted == False).one_or_none()
            if not user:
                response = jsonify({
                    'success': False,
                    'message': 'Not Authorized: invalid email'
                })
                response.status_code = 403
                return response
            # check the user's password
            password_valid = check_password_hash(user.password, password)
            if not password_valid:
                response = jsonify({
                    'success': False,
                    'message': 'Not Authorized: invalid password'
                })
                response.status_code = 403
                return response

        token = generate_auth_token(user_id=user.user_id)
        response = jsonify({
            'success': True,
            'token': token
        })
        response.status_code == '200'
        return response

    @auth_blueprint.route('/api/forgotPassword/', methods=['POST'])
    def forgot_password_api():
        """
        endpoint which creates a new PasswordResetLink for the user with the given email
        and sends this user a password reset email
        """

        # get the data for this query
        data = request.get_json()
        if not data:
            response = jsonify({
                'success': False,
                'message': 'Missing request body'
            })
            response.status_code = 422
            return response

        user_email = data.get('email').strip().lower()

        # look for a user with this email
        user = db.session.query(User).filter(User.email == user_email).one_or_none()
        if not user:
            response = jsonify({
                'success': False,
                'message': 'No user with this email. Contact your system admin to create a user.'
            })
            response.status_code = 200
            return response

        # send this user a password reset email
        send_password_reset(user)
        response = jsonify({
            'success': True
        })
        response.status_code = 200
        return response

    @auth_blueprint.route('/api/resetPassword/', methods=['POST'])
    def reset_password_api():
        """
        endpoint for making a request to reset a user's password
        """

        # get the data for this query
        data = request.get_json()
        if not data:
            response = jsonify({
                'success': False,
                'message': 'Missing request body'
            })
            response.status_code = 422
            return response

        # confirm the password is not blank
        new_password_plain = data.get('password')
        if not new_password_plain:
            response = jsonify({
                'success': False,
                'message': 'Cannot have empty password'
            })
            response.status_code = 200
            return response

        # check if there is a PasswordResetLink with this secret_link
        secret_link = data.get('secret_link')
        max_age = datetime.datetime.now() - datetime.timedelta(days=PASSWORD_RESET_LINK_EXPIRATION_DAYS)
        reset_link_object = db.session.query(PasswordResetLink).filter(
            PasswordResetLink.secret_link == secret_link,
            PasswordResetLink.expired == False,
            PasswordResetLink.created_at > max_age
        ).one_or_none()
        if not reset_link_object:
            response = jsonify({
                'success': False,
                'message': 'This password reset link is no longer active. Use forgot password again to create a new one.'
            })
            response.status_code = 200
            return response

        # get the user associated with this PasswordResetLink
        user = db.session.query(User).filter(User.user_id == reset_link_object.user_id).one_or_none()
        if not user:
            response = jsonify({
                'success': False,
                'message': 'Not Authorized: invalid user'
            })
            response.status_code = 403
            return response

        # generate and set new password
        new_password = generate_password_hash(new_password_plain)
        user.password = new_password
        reset_link_object.expired = True
        db.session.add(user)
        db.session.add(reset_link_object)
        db.session.commit()

        # return authenticated token
        token = generate_auth_token(user_id=user.user_id)
        response = jsonify({
            'success': True,
            'token': token
        })
        response.status_code = 200
        return response

    @auth_blueprint.route('/api/activateAccount/', methods=['POST'])
    def activate_account_api():
        """
        endpoint to activate a user's account by looking for a matching activation link
        """

        # get the data for this query
        data = request.get_json()
        if not data:
            response = jsonify({
                'success': False,
                'message': 'Missing request body'
            })
            response.status_code = 422
            return response

        # process arguments
        arg_email = data.get('email').strip().lower()

        # check if there is a user with this activation_link
        secret_link = data.get('secret_link')
        user = db.session.query(User).filter(
            User.activation_link == secret_link,
        ).one_or_none()
        if not user:
            response = jsonify({
                'success': False,
                'message': 'This activation link is no longer active. Contact your system administrator to receive a new one.'
            })
            response.status_code = 200
            return response

        # check if this user has already activated their account
        if user.activated:
            response = jsonify({
                'success': False,
                'message': 'This account has already been activated. Try forgot password to recover your password.'
            })
            response.status_code = 200
            return response

        # check if the correct email address was supplied
        if user.email != arg_email:
            response = jsonify({
                'success': False,
                'message': 'This is not the correct email for this activation link. Contact your system administrator to request a link for this email.'
            })
            response.status_code = 200
            return response

        # generate and set new password
        new_password = generate_password_hash(data.get('password'))
        user.password = new_password
        user.activated = True
        db.session.add(user)
        db.session.commit()

        # log that a user just activated their account
        _log('++ {} just activated their account'.format(user.email), '_signup')

        # return authenticated token
        token = generate_auth_token(user_id=user.user_id)
        response = jsonify({
            'success': True,
            'token': token
        })
        response.status_code = 200
        return response

    # finally return blueprint
    return auth_blueprint