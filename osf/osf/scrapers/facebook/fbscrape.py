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

    def __init__(self, params, log=None):
        self.params = params
        # self.driver = webdriver.Firefox()
        self.driver = webdriver.Remote(
            command_executor='http://selenium:4444/wd/hub',
            desired_capabilities=DesiredCapabilities.FIREFOX.copy()
        )
        self.output = {}
        self.log = log

    def log(self, message):
        if self.log:
            self.log(message)
        else:
            print message

    def get_friends(self, user):
        """
        gets the friends of the given user
        :param user:
        :return:
        """
        url = '{}/{}/friends'.format(BASE_URL, user)
        self.log('++ getting friends for {}'.format(url))
        self.driver.get(url)
        time.sleep(1)
        # scroll the page a few times
        found_end = False
        prev_num_friends = 0
        j = 0
        for i in range(0, 200):
            # self.log('++ scrolling')
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
                self.log('++ found {}'.format(username))
            else:
                self.log('xx: failed on {}'.format(friend_link))

    def get_posts_by_user(self, user):
        """
        fetches posts by a particular user
        :param user:
        :return:
        """
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
        elem.send_keys(self.params['username'])
        elem = self.driver.find_element_by_id("pass")
        elem.send_keys(self.params['password'])
        elem.send_keys(Keys.RETURN)
        time.sleep(3)

    def fb_scrape_posts(self):
        """
        scrapes based on params FbScraper was initialized with
        and writes the found data in the correct place
        :return:
        """

        # log into facebook
        self.fb_login()

        # fetch posts for friends
        friends = self.params['friends']
        friends_posts = {}
        self.output['friends_posts'] = friends_posts
        for friend in friends:
            posts = self.get_posts_by_user(friend)
            # store the posts in a dictionary which will be written to output later
            friends_posts[friend] = posts

        # return output
        return self.output


if __name__ == '__main__':
    print '++ running facebook_scrape.py'

