from osf_scraper_api.utilities.log_helper import _log, _capture_exception
from osf_scraper_api.utilities.osf_helper import get_fb_scraper
from osf_scraper_api.utilities.s3_helper import s3_delete_file
from osf_scraper_api.utilities.fs_helper import file_exists, load_dict
from osf_scraper_api.crawler.utils import fetch_friends_of_user, \
    get_posts_folder, get_user_from_user_file


def clear_errors(fb_username, fb_password):
    fb_scraper = get_fb_scraper(fb_username=fb_username, fb_password=fb_password)
    user = fb_scraper.get_currently_logged_in_user()
    fb_scraper.quit_driver()
    friends = fetch_friends_of_user(user)

    # get all extant user_files
    input_folder = get_posts_folder()
    user_files = ['{}/{}.json'.format(input_folder, user) for user in friends]
    _log('++ processing {} users'.format(len(user_files)))
    for index, user_file in enumerate(user_files):
        try:
            if not file_exists(user_file):
                continue
            user = get_user_from_user_file(user_file=user_file, input_folder=input_folder)
            data_dict = load_dict(user_file)
            if data_dict == 'Error':
                _log('++ removing Error file for user: {}'.format(user))
                s3_delete_file(user_file)
            if not index % 10:
                _log('++ processing {}/{}'.format(index, len(user_files)))
        except Exception as e:
            _capture_exception(e)
            continue

    _log('++ finished clearing errors')


if __name__ == '__main__':
    from osf_scraper_api.web.app import create_app
    app = create_app()
    with app.app_context():
        clear_errors(
            fb_username='',
            fb_password=''
        )
