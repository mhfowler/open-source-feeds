import datetime
import re
import time

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities


BASE_URL = 'https://www.facebook.com'


class FbScraper():
    """
    Wrapper class for scraping facebook
    """

    def __init__(self, fb_username, fb_password, command_executor=None, log=None):
        self.fb_username = fb_username
        self.fb_password = fb_password
        self.logged_in = False
        if command_executor:
            self.driver = webdriver.Remote(
                command_executor=command_executor,
                desired_capabilities=DesiredCapabilities.FIREFOX.copy()
            )
        else:
            self.driver = webdriver.Firefox()
        self.output = {}
        self.log_fun = log

    def log(self, message):
        if self.log_fun:
            self.log_fun(message)
        else:
            print message

    def get_friends(self, user):
        """
        gets the friends of the given user
        :param user:
        :return:
        """
        if not self.logged_in:
            self.fb_login()

        # this is the list we will populate
        usernames = []

        # navigate to friends url
        url = '{}/{}/friends'.format(BASE_URL, user)
        self.log('++ getting friends for {}'.format(url))
        self.driver.get(url)
        time.sleep(1)
        # scroll the page a few times
        found_end = False
        prev_num_friends = 0
        j = 0
        for i in range(0, 200):
            self.log('++ scrolling {}'.format(i))
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)
            friends = self.driver.find_elements_by_css_selector('.fsl a')
            num_friends = len(friends)
            if num_friends == prev_num_friends:
                j += 1
            prev_num_friends = num_friends
            if j > 3:
                break

        friends = self.driver.find_elements_by_css_selector('.fsl a')
        self.log('++ num friends found: {}'.format(len(friends)))
        for friend in friends:
            friend_link = friend.get_attribute('href')
            match = re.match('https\:\/\/www\.facebook\.com/(\S+)\?.*', friend_link)
            if match:
                username = match.group(1)
                usernames.append(username)
                # self.log('++ found {}'.format(username))
            else:
                pass
                # self.log('xx: failed on {}'.format(friend_link))

        # return usernames
        return usernames

    def get_posts_by_user(self, user):
        """
        fetches posts by a particular user
        :param user:
        :return:
        """
        if not self.logged_in:
            self.fb_login()

        # list to store posts in
        to_return = []

        # navigate to the url of the friend
        url = '{}/{}'.format(BASE_URL, user)
        self.log('++ getting posts for {}'.format(url))
        self.driver.get(url)
        time.sleep(4)

        # scroll the page a few times
        for i in range(0, 4):
            self.log('++ scrolling')
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)

        # grab the posts
        posts = self.driver.find_elements_by_css_selector('a._5pcq')
        for post in posts:
            post_link = post.get_attribute('href')
            post_content = post.get_attribute('innerHTML')
            match = re.match('.*data-utime="(\d+)"', post_content)
            if match:
                timestamp = int(match.group(1))
                d = datetime.datetime.fromtimestamp(timestamp)
                # TODO: do some confirmation, post is beyond certain date
                to_return.append({
                    'link': post_link,
                    'date': timestamp
                })
            else:
                pass

        # finally return all the posts as a list
        return to_return

    def fb_login(self):
        """
        logs into facebook
        :return:
        """
        self.log('++ logging into facebook')
        self.driver.get("http://www.facebook.org")
        time.sleep(1)
        assert "Facebook" in self.driver.title
        elem = self.driver.find_element_by_id("email")
        elem.send_keys(self.fb_username)
        elem = self.driver.find_element_by_id("pass")
        elem.send_keys(self.fb_password)
        elem.send_keys(Keys.RETURN)
        time.sleep(3)
        self.logged_in = True

    def get_posts(self, params):
        """
        :param params: a dictionary which can have the following keys
        - users (a list of usernames of which to scrape posts from)
        :return:
        """

        # log into facebook
        if not self.logged_in:
            self.fb_login()

        # fetch posts for each given user
        users = params['users']
        posts = {}
        self.output['posts'] = posts
        for user in users:
            user_posts = self.get_posts_by_user(user)
            # store the posts in a dictionary which will be written to output later
            posts[user] = user_posts

        # return output
        return self.output

    def quit_driver(self):
        self.driver.quit()


if __name__ == '__main__':
    print '++ running fbscrape test'
    from osf_scraper_api.settings import ENV_DICT
    fbscraper = FbScraper(
        fb_username=ENV_DICT['FB_USERNAME'],
        fb_password=ENV_DICT['FB_PASSWORD'],
        command_executor=None)
    import json
    print json.dumps(fbscraper.get_posts({'users': ENV_DICT['FB_FRIENDS']}))

