import sys

from osf.scrapers.facebook.fbscrape import FbScraper


def scroll(fb_username, fb_password):
    print '++ initiating scroll'
    while True:
        try:
            fb_scraper = FbScraper(
                fb_username=fb_username,
                fb_password=fb_password,
            )
            try:
                fb_scraper.get_friends_of_user(user='maxhfowler')
                fb_scraper.get_posts_by_user(
                    user='maxhfowler',
                    max_num_posts_per_user=100
                )
            finally:
                fb_scraper.quit_driver()
        except:
            continue


if __name__ == '__main__':
    fb_user = sys.argv[1]
    fb_pass = sys.argv[2]
    scroll(fb_user, fb_pass)