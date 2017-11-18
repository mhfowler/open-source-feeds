import sys
import time

from osf.scrapers.facebook.fbscrape import FbScraper


def scroll(fb_username, fb_password):
    print '++ initiating'
    restart = False
    while True:
        try:
            print '++ initiating driver'
            fb_scraper = FbScraper(
                fb_username=fb_username,
                fb_password=fb_password,
            )
            restart = False
            while not restart:
                print '++ starting loop'
                try:
                    fb_scraper.get_friends_of_user(user='maxhfowler')
                    fb_scraper.get_posts_by_user(
                        user='maxhfowler',
                        max_num_posts_per_user=100
                    )
                except:
                    restart = True
                    time.sleep(2)
        except:
            print '++ error'
            time.sleep(2)
            continue


if __name__ == '__main__':
    fb_user = sys.argv[1]
    fb_pass = sys.argv[2]
    scroll(fb_user, fb_pass)