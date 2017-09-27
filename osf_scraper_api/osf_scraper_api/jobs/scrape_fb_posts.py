from osf_scraper_api.utilities.osf_helper import get_fb_scraper, convert_timestamp_to_date


def scrape_fb_posts(
        fb_username,
        fb_password,
        users,
        max_num_posts_per_user=None,
        after_timestamp=None,
        before_timestamp=None,
        jump_to_timestamp=None):

    # convert params
    after_date = convert_timestamp_to_date(after_timestamp)
    before_date = convert_timestamp_to_date(before_timestamp)
    jump_to = convert_timestamp_to_date(jump_to_timestamp)

    # initialize fb_scraper
    fb_scraper = get_fb_scraper(fb_username=fb_username, fb_password=fb_password)

    # scrape posts
    data = fb_scraper.get_posts({
        'users': users,
        'max_num_posts_per_user': max_num_posts_per_user,
        'after_date': after_date,
        'before_date': before_date,
        'jump_to': jump_to
    })

    # return
    return data