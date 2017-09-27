from osf_scraper_api.utilities.osf_helper import get_fb_scraper


def scrape_fb_friends(fb_username, fb_password, users):

    # initialize fb_scraper
    fb_scraper = get_fb_scraper(fb_username=fb_username, fb_password=fb_password)

    # scrape friends
    data = fb_scraper.get_friends(users=users)

    # return
    return data