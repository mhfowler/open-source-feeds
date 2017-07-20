import requests

from hello_settings import ENV_DICT


def bot_reply(fb_id, msg):
    message_data = msg
    if isinstance(msg, basestring):
        message_data = {'text': msg}

    data = {
        'recipient': {'id': fb_id},
        'message': message_data
    }
    url = 'https://graph.facebook.com/v2.6/me/messages?access_token={access_token}'.format(
        access_token=ENV_DICT['FB_ACCESS_TOKEN']
    )
    response = requests.post(url, json=data)

    return response
