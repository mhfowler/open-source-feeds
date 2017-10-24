from osf_scraper_api.utilities.log_helper import _log
from osf_scraper_api.utilities.osf_helper import get_fb_scraper, wait_for_online
from osf_scraper_api.electron.utils import save_current_pipeline
from osf_scraper_api.utilities.fs_helper import save_dict, file_exists


def scrape_fb_friends_helper(fb_scraper, key_name, user):
    try:
        output_dict = fb_scraper.get_friends(users=[user])
        # if succesful reset num_initializations
        fb_scraper.num_initializations = 0
        return output_dict
    except Exception as e:
        _log('++ encountered exception: {}'.format(str(e)))
        if fb_scraper.num_initializations < 5:
            fb_scraper.re_initialize_driver()
            _log('++ retry attempt {}'.format(fb_scraper.num_initializations))
            return scrape_fb_friends_helper(fb_scraper=fb_scraper, key_name=key_name, user=user)
        else:
            raise e


def scrape_fb_friends(fb_username, fb_password):
    _log('++ starting fb_friends job')
    wait_for_online()
    fb_scraper = get_fb_scraper(fb_username=fb_username, fb_password=fb_password)
    fb_scraper.fb_login()

    user = fb_scraper.get_currently_logged_in_user()

    key_name = 'friends/{}.json'.format(user)
    if file_exists(key_name):
        _log('++ skipping {}'.format(key_name))
        return

    # otherwise scrape and then save
    output_dict1 = scrape_fb_friends_helper(fb_scraper=fb_scraper, key_name=key_name, user=user)
    output_dict2 = scrape_fb_friends_helper(fb_scraper=fb_scraper, key_name=key_name, user=user)
    friends1 = set(output_dict1[user])
    friends2 = set(output_dict2[user])
    friends = friends1.union(friends2)
    _log('++ saving {} friends'.format(len(friends)))
    output_dict = {user: list(friends)}
    save_dict(output_dict, key_name)
    _log('++ data saved to {}'.format(key_name))
    try:
        fb_scraper.quit_driver()
    except:
        pass

    _log('++ fb_friends pipeline complete')
    save_current_pipeline(
        pipeline_name='fb_friends',
        pipeline_status='finished'
    )