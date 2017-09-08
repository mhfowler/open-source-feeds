import jwt
import datetime
from osf_dashboard.settings import ENV_DICT, AUTH_TOKEN_EXPIRATION_WEEKS


def generate_token(token_type, exp, config=None):
    """
    Creates a token with a default payload and custom setting
    :param token_type: the type of token being made
    :param exp: time until token expires (this should be timedelta)
    :param config: any additional configurations for payload
    :return token: token containing the newly created payload
    """
    # Default payload includes:
    # iss: issuer of token (always montage)
    # token_type: the type of token this is
    # exp: expiration date, how long until token expires
    # iat: time of creation
    if not config:
        config = {}
    payload = {
        'iss': 'successkit',
        'token_type': token_type,
        'exp': datetime.datetime.utcnow() + exp,
        'iat': datetime.datetime.utcnow()
    }
    payload.update(config)
    token = jwt.encode(payload, ENV_DICT['JWT_SECRET'], algorithm='HS256')
    return token


def token_decode(token):
    """
    Decodes a given token and responds accordingly
    :param token: the token to be decoded
    :return result: a result is return based on the status of token. Either the token's payload or an
     appropriate error message.
    """
    if not token or token == 'null':
        return {
            'success': False,
            'message': 'Not Authorized: invalid token'
        }
    try:
        payload = jwt.decode(token, ENV_DICT['JWT_SECRET'], algorithms=['HS256'])
    except jwt.ExpiredSignatureError:
        return {
            'success': False,
            'message': 'Not Authorized: expired token'
        }
    except jwt.InvalidIssuerError:
        return {
            'success': False,
            'message': 'Not Authorized: invalid token'
        }
    except jwt.DecodeError:
        return {
            'success': False,
            'message': 'Not Authorized: malformed token'
        }
    return {
        'success': True,
        'payload': payload
    }


def generate_auth_token(user_id):
    """
    generates an authentication token for the user with the their user_id encoded into it
    :param user_id:
    :return:
    """
    config = {'user_id': user_id}
    token = generate_token(token_type='auth', exp=datetime.timedelta(weeks=AUTH_TOKEN_EXPIRATION_WEEKS),
                           config=config)
    return token