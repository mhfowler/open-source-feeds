import datetime
import re
import time
import tempfile
import os

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

from osf.scrapers.facebook.screenshot import save_post

BASE_URL = 'https://www.facebook.com'


class Post:
    """
    wrapper for searching and interacting with facebook post element as retrieved by selenium
    """
    def __init__(self, selenium_element):
        self.element = selenium_element
        link_divs = self.element.find_elements_by_css_selector('a._5pcq')
        if link_divs:
            self.link_div = link_divs[0]
        else:
            self.link_div = None

    def is_valid(self):
        return self.link_div is not None

    def get_element(self):
        return self.element

    def get_timestamp(self):
        post_content = self.link_div.get_attribute('innerHTML')
        match = re.match('.*data-utime="(\d+)"', post_content)
        if match:
            timestamp = int(match.group(1))
            return timestamp
        else:
            return None

    def get_link(self):
        self.link = self.link_div.get_attribute('href')
        return self.link

    def get_content(self):

        # store whatever we can get in here
        content = {}

        # try to get author
        author_div = self.element.find_elements_by_css_selector('.fwb')
        if author_div:
            author_div = author_div[0]
            author_a = author_div.find_elements_by_css_selector('a')
            if author_a:
                author_a = author_a[0]
                author_href = author_a.get_attribute('href')
                match = re.match('https://www.facebook.com/([^?]+)\??.*', author_href)
                if match:
                    author = match.group(1)
                else:
                    author = author_href
                content['author'] = author

        # try to get post_type
        post_type_divs = self.element.find_elements_by_css_selector('._5x46 .fcg')
        if post_type_divs:
            for div in post_type_divs:
                caption = div.text
                match = re.match('.*added \d+ new photos.*', caption)
                if match:
                    content['post_type'] = 'added photos'
                    break
                match = re.match('.*added a new photo.*', caption)
                if match:
                    content['post_type'] = 'added photos'
                    break
                match = re.match('.* shared .*', caption)
                if match:
                    content['post_type'] = 'shared'
                    break
                check_in_icon = div.find_elements_by_css_selector('._51mq')
                if check_in_icon:
                    content['post_type'] = 'check in'
                    break

        # try to get text of post
        user_text_div = self.element.find_elements_by_css_selector('.userContent')
        if user_text_div:
            user_text_div = user_text_div[0]
            user_text = user_text_div.text
            content['text'] = user_text

        # look for non-text-div
        non_text_div = self.element.find_elements_by_css_selector('._3x-2')
        if non_text_div:
            non_text_div = non_text_div[0]
            children = non_text_div.find_elements_by_css_selector('*')
            if len(children) > 1:
                content['not_just_text'] = True

        # look for see-more-link
        see_more_links = self.element.find_elements_by_css_selector('a.see_more_link')
        if see_more_links:
            content['see_more'] = True

        # try to find article
        article_div = self.element.find_elements_by_css_selector('._52c6')
        if article_div:
            article = article_div[0]
            link = article.get_attribute('href')
            content['link'] = link

        # try to get images
        image_divs = self.element.find_elements_by_css_selector('._4-eo')
        if image_divs:
            image_links = []
            for image_div in image_divs:
                image_link = image_div.get_attribute('href')
                image_links.append(image_link)
            if image_links:
                content['images'] = image_links

        # try to get events
        event_divs = self.element.find_elements_by_css_selector('._fw-')
        if event_divs:
            event_div = event_divs[0]
            event = {}
            event_title_div = event_div.find_elements_by_css_selector('._fwx')
            if event_title_div:
                event_title_div = event_title_div[0]
                event['event_title'] = event_title_div.text
                event_a = event_title_div.find_elements_by_css_selector('a')
                if event_a:
                    event_a = event_a[0]
                    event_link = event_a.get_attribute('href')
                    event['event_link'] = event_link
            event_info_div = event_div.find_elements_by_css_selector('._fwy')
            if event_info_div:
                event_info_div = event_info_div[0]
                event['event_info'] = event_info_div.text
            content['event'] = event

        # return any content we found
        return content


class FbScraper():
    """
    Wrapper class for scraping facebook
    """

    def __init__(self,
                 fb_username,
                 fb_password,
                 command_executor=None,
                 driver=None,
                 which_driver=None,
                 log=None,
                 log_image=None,
                 proxy=None,
                 dpr=1):
        self.fb_username = fb_username
        self.fb_password = fb_password
        self.logged_in = False
        self.dpr = dpr  # device pixel ratio
        self.output = {}
        self.log_fun = log
        self.log_image_fun = log_image
        self.driver_has_quit = False
        self.num_initializations = 0
        self.command_executor = command_executor
        self.proxy = proxy
        self.which_driver = which_driver
        if not (which_driver or driver or command_executor):
            self.which_driver = 'chrome'
        self.initialize_driver(driver=driver)

    def initialize_driver(self, driver=None):
        if self.command_executor:
            chrome_options = Options()
            chrome_options.add_argument("--disable-notifications")
            if self.proxy:
                chrome_options.add_argument('--proxy-server=%s' % self.proxy)
            self.driver = webdriver.Remote(
                command_executor=self.command_executor,
                desired_capabilities=chrome_options.to_capabilities()
            )
        else:
            if self.which_driver == 'phantomjs':
                dcap = dict(DesiredCapabilities.PHANTOMJS)
                dcap["phantomjs.page.settings.userAgent"] = (
                    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/53 "
                    "(KHTML, like Gecko) Chrome/15.0.87"
                )
                driver = webdriver.PhantomJS(desired_capabilities=dcap)
                driver.set_window_size(1400, 1000)
                self.driver = driver
            elif self.which_driver == 'chrome':
                chrome_options = Options()
                chrome_options.add_argument("--disable-notifications")
                if self.proxy:
                    chrome_options.add_argument('--proxy-server=%s' % self.proxy)
                self.driver = webdriver.Chrome(chrome_options=chrome_options)
            # otherwise use the driver passed in
            else:
                self.driver = driver
        # set page load timeout
        self.driver.set_page_load_timeout(time_to_wait=240)

    def re_initialize_driver(self):
        try:
            self.driver.quit()
        except:
            pass
        sleep_time = 2 * (self.num_initializations + 1)
        self.log('++ sleeping for {}'.format(sleep_time))
        time.sleep(sleep_time)
        self.num_initializations += 1
        self.logged_in = False
        self.driver_has_quit = False
        self.initialize_driver()

    def log(self, message):
        if self.log_fun:
            self.log_fun(message)
        else:
            print message

    def log_image(self, image_path):
        if self.log_image_fun:
            self.log_image_fun(image_path)

    def close_dialogs(self):
        """
        clicks away from notifications that may be blocking the screen
        :return:
        """
        notifications = self.driver.find_elements_by_css_selector('.layerCancel._4jy0')
        if notifications:
            for notification in notifications:
                notification.click()
                time.sleep(4)

    def screenshot_post(self, post, output_path):
        if not self.logged_in:
            self.fb_login()
        return save_post(post=post, driver=self.driver, output_path=output_path, dpr=self.dpr, log=self.log)

    def get_currently_logged_in_user(self):
        if not self.logged_in:
            self.fb_login()
        url = '{}/profile'.format(BASE_URL)
        self.driver.get(url)
        time.sleep(1)
        current_url = self.driver.current_url
        match = re.match('https://www.facebook.com/(.*)', current_url)
        user = match.group(1)
        if user.endswith('/'):
            user = user[:-1]
        return user

    def get_friends(self, users):
        """
        for each user, in list of users, get all of their friends
        :param users: list of strings of usernames
        :return:
        """
        output = {}
        for user in users:
            u_output = self.get_friends_of_user(user)
            output[user] = u_output
        return output

    def get_friends_of_user(self, user):
        """
        gets the friends of the given user
        :param user:
        :return:
        """
        if not self.logged_in:
            self.fb_login()
        self.close_dialogs()

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
            time.sleep(1.5)
            friends = self.driver.find_elements_by_css_selector('.fsl a')
            num_friends = len(friends)
            if num_friends == prev_num_friends:
                j += 1
            else:
                j = 0
            prev_num_friends = num_friends
            if j > 7:
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

    def log_screenshot(self):
        f, f_path = tempfile.mkstemp()
        self.driver.get_screenshot_as_file(f_path)
        self.log_image(image_path=f_path)
        os.unlink(f_path)

    def get_posts_by_user(self,
                          user,
                          after_date=None,
                          before_date=None,
                          jump_to=None,
                          max_num_posts_per_user=None):
        """
        fetches posts by a particular user
        :param user:
        :return:
        """
        if not self.logged_in:
            self.fb_login()
        self.close_dialogs()

        # convert before_date and after_date to timestamp
        if after_date:
            after_timestamp = time.mktime(after_date.timetuple())
        else:
            after_timestamp = None
        if before_date:
            before_timestamp = time.mktime(before_date.timetuple())
        else:
            before_timestamp = None

        # navigate to the url of the friend
        url = '{}/{}'.format(BASE_URL, user)
        self.log('++ navigating to url `{}`'.format(url))
        self.driver.get(url)
        time.sleep(4)

        # jump_to, optional arg to use facebook sticky header to jump to time period
        if jump_to:
            try:
                for i in range(0, 1):
                    self.log('++ scrolling')
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(1)
                timeline_nav = self.driver.find_element_by_css_selector('.fbTimelineStickyHeader')
                if timeline_nav:
                    year = jump_to.year
                    month = jump_to.month
                    if year:
                        selector = '.uiSelectorButton.uiButton.uiButtonOverlay'
                        recent_nav = timeline_nav.find_elements_by_css_selector(selector)
                        for elt in recent_nav:
                            if elt.text == 'Recent':
                                elt.click()
                                time.sleep(2)
                        # xpath_selector = "//*[contains(text(), 'Recent')]"
                        # recent_nav = timeline_nav.find_element_by_xpath(xpath_selector)
                        # recent_nav.click()
                        # time.sleep(2)
                        selector = '[data-key="year_{}"]'.format(year)
                        year_select = timeline_nav.find_elements_by_css_selector(selector)
                        if year_select:
                            year_select = year_select[0]
                            year_select.click()
                            time.sleep(2)
                    if month:
                        selector = '.uiSelectorButton.uiButton.uiButtonOverlay'
                        all_posts_nav = timeline_nav.find_elements_by_css_selector(selector)
                        for elt in all_posts_nav:
                            if elt.text == 'All Posts':
                                elt.click()
                                time.sleep(2)
                        selector = '[data-key="month_{}_{}"]'.format(year, month)
                        month_select = timeline_nav.find_elements_by_css_selector(selector)
                        if month_select:
                            month_select = month_select[0]
                            month_select.click()
                            time.sleep(2)
                            self.log('++ successfully jumped to: {}'.format(jump_to))
            except:
                self.log('++ failed to jump to date: {}'.format(jump_to))
                self.log_screenshot()

        # scroll the page and scrape posts
        posts = {}
        finished = False
        num_consecutive_searches_without_posts = 0
        num_searches = 0
        max_num_searches = 200
        stop_search_reason = None
        already_clicked_elts = set([])
        # keep looping until we reach a finished condition
        # (no new posts, > than oldest date, or > max_num_searches)
        while not finished and (num_searches < max_num_searches):

            # increment search counter
            num_searches += 1

            # scroll down the page a few times
            for i in range(0, 4):
                # scroll
                self.log('++ scrolling')
                # # scroll in small chunks
                # TODO: figure out how to click continue reading links
                # scroll_destination = self.driver.execute_script("return document.body.scrollHeight")
                # for s in range(0, 4):
                #     # try to click "continue reading" links before scrolling further
                #     see_more_links = self.driver.find_elements_by_css_selector('a.see_more_link')
                #     for elt in see_more_links:
                #         if elt not in already_clicked_elts:
                #             already_clicked_elts.add(elt)
                #             is_visible = elt.is_displayed()
                #             if is_visible:
                #                 try:
                #                     elt.click()
                #                     time.sleep(1)
                #                 except Exception as e:
                #                     continue
                #     s_height = int(scroll_destination) - ((4-s)*100)
                #     self.driver.execute_script("window.scrollTo(0, {}{});".format(s_height))
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1)

            # grab the posts
            # found_posts = self.driver.find_elements_by_css_selector('a._5pcq')
            found_sel_posts = self.driver.find_elements_by_css_selector('div.fbUserContent, div.fbUserContent, div.fbUserStory, div.userContentWrapper')
            found_posts = [Post(x) for x in found_sel_posts]
            # filter out malformed posts
            valid_posts = filter(lambda p: p.is_valid(), found_posts)

            # only consider new posts
            new_posts = filter(lambda p: p.get_link() not in posts, valid_posts)

            # if no new posts, increment counter
            if not new_posts:
                num_consecutive_searches_without_posts += 1
                # if there have been 3 searches in a row without any new posts, then break the loop
                if num_consecutive_searches_without_posts >= 5:
                    finished = True
                    stop_search_reason = '++ stopping search due to too many searches without finding any posts'
            else:
                self.log('++ found {} posts'.format(len(new_posts)))

            # calculate how many posts
            num_posts_already = len(posts.keys())

            # if max_num_posts_per_user, check if we have exceeded the limit
            if max_num_posts_per_user:
                num_posts_remaining = max_num_posts_per_user - num_posts_already
                if len(new_posts) > num_posts_remaining:
                    # end the for loop
                    finished = True
                    # and truncate new_posts
                    new_posts = new_posts[:num_posts_remaining]
                    stop_search_reason = '++ stopping search due to max_num_posts_per_user'

            # iterate through new posts and parse and save them
            for post in new_posts:
                post_link = post.get_link()
                timestamp = post.get_timestamp()
                if timestamp:
                    # if we found a post older than the given date, then stop downloading
                    if after_timestamp and timestamp < after_timestamp:
                        stop_search_reason = '++ stopping search due to after_date'
                        finished = True
                    # otherwise add the post to the list of found posts
                    else:
                        if post_link not in posts:
                            posts[post_link] = {
                                'link': post_link,
                                'date': timestamp,
                                'content': post.get_content()
                            }
                else:
                    pass

        if stop_search_reason:
            self.log(stop_search_reason)

        # convert dictionary of posts to a list
        to_return = []
        for post_link, post in posts.items():
            to_return.append(post)

        # add the page this was scraped from to each post
        for post in to_return:
            post['page'] = user

        # if there is before_date, then filter the posts
        if before_date:
            to_return = filter(lambda post: post['date'] <= before_timestamp, to_return)

        # return the list of posts
        self.log('++ returned {} total posts for {}'.format(len(to_return), user))
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
        self.assert_logged_in()
        self.log('++ successfully logged in')
        self.logged_in = True

    def assert_logged_in(self):
        # self.log_screenshot()
        elements = self.driver.find_elements_by_css_selector('._1k67')
        if not len(elements):
            raise Exception('++ failed to assert that driver is logged in')

    def get_posts(self, params):
        """
        :param params: a dictionary which can have the following keys
        - users (a list of usernames of which to scrape posts from)
        :return:
        """

        # log into facebook
        if not self.logged_in:
            self.fb_login()
        self.close_dialogs()

        # fetch posts for each given user
        users = params['users']
        posts = []
        self.output = posts
        for user in users:
            self.log('++ getting posts for user: {}'.format(user))
            user_posts = self.get_posts_by_user(user,
                                                after_date=params.get('after_date'),
                                                before_date=params.get('before_date'),
                                                jump_to=params.get('jump_to'),
                                                max_num_posts_per_user=params.get('max_num_posts_per_user')
                                                )
            # add the posts to the list
            posts.extend(user_posts)

        # return output
        return self.output

    def quit_driver(self):
        if not self.driver_has_quit:
            self.log('++ quitting driver')
            self.driver.quit()
            self.driver_has_quit = True


if __name__ == '__main__':
    print '++ running fbscrape test'
    from osf_scraper_api.settings import ENV_DICT
    fbscraper = FbScraper(
        fb_username=ENV_DICT['FB_USERNAME'],
        fb_password=ENV_DICT['FB_PASSWORD'],
        command_executor=None)
    import json
    output = fbscraper.get_posts({
        'users': ['maxhfowler'],
        # 'jump_to': datetime.datetime(year=2016, month=9, day=1),
        'max_num_posts_per_user': 15,
    })
    print json.dumps(output)

