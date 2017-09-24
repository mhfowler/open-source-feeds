import tempfile
import os

from osf_scraper_api.utilities.log_helper import _log, _log_image
from osf.scrapers.facebook import FbScraper
from osf_scraper_api.settings import SELENIUM_URL
from osf_scraper_api.utilities.fs_helper import save_dict, file_exists
from osf_scraper_api.utilities.fs_helper import save_file


def screenshot_posts(posts, fb_username, fb_password):

    fb_scraper = FbScraper(
        fb_username=fb_username,
        fb_password=fb_password,
        command_executor=SELENIUM_URL,
        log=_log,
        log_image=_log_image,
    )

    for post in posts:
        output_path = post['screenshot_path']
        _log('++ saving screenshot of post: {}'.format(post['link']))
        f = tempfile.NamedTemporaryFile(delete=False)
        f.close()
        temp_path = f.name + '.png'
        fb_scraper.screenshot_post(post=post, output_path=temp_path)
        image_url = save_file(source_file_path=temp_path, destination=output_path)
        os.unlink(f.name)
        os.unlink(temp_path)
        _log('++ successfuly uploaded to: {}'.format(image_url))
