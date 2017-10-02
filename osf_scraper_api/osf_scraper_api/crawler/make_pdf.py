import random
import tempfile
import os

from fpdf import FPDF

from osf_scraper_api.utilities.log_helper import _log, _capture_exception
from osf_scraper_api.utilities.osf_helper import get_fb_scraper
from osf_scraper_api.utilities.fs_helper import file_exists, load_dict, save_file
from osf_scraper_api.utilities.s3_helper import s3_download_file, get_s3_link
from osf_scraper_api.utilities.email_helper import send_email
from osf_scraper_api.settings import ENV_DICT
from osf_scraper_api.crawler.utils import fetch_friends_of_user, \
    get_posts_folder, get_user_from_user_file
from osf_scraper_api.crawler.utils import get_screenshot_output_key_from_post


def make_pdf_job(fb_username, fb_password):
    fb_scraper = get_fb_scraper(fb_username=fb_username, fb_password=fb_password)
    user = fb_scraper.get_currently_logged_in_user()
    fb_scraper.quit_driver()
    friends = fetch_friends_of_user(user)

    # get all extant user_files
    input_folder = get_posts_folder()
    user_files = ['{}/{}.json'.format(input_folder, user) for user in friends]
    # user_files = []
    # for index, user in enumerate(friends):
    #     user_file = '{}/{}.json'.format(input_folder, user)
    #     # if file exists, append it to list to process
    #     if file_exists(user_file):
    #         user_files.append(user_file)
    #         if ENV_DICT.get('TEST_SAMPLE_SIZE'):
    #             if len(user_files) > ENV_DICT.get('TEST_SAMPLE_SIZE'):
    #                 _log('++ truncating list of users to be < TEST_SAMPLE_SIZE')
    #                 break
    #     if not index % 10:
    #         _log('++ loading {}/{}'.format(index, len(friends)))
    all_posts = []
    _log('++ loading posts for {} users'.format(len(user_files)))
    for index, user_file in enumerate(user_files):
        if not file_exists(user_file):
            continue
        try:
            user = get_user_from_user_file(user_file=user_file, input_folder=input_folder)
            data_dict = load_dict(user_file)
            user_posts = data_dict['posts'][user]
            for post in user_posts:
                output_key = get_screenshot_output_key_from_post(user=user, post=post)
                post['screenshot_path'] = output_key
            all_posts.extend(user_posts)
        except Exception as e:
            _capture_exception(e)
            _log('++ failed to load posts for user: {}'.format(user))
        if not index % 10:
            _log('++ loading posts {}/{}'.format(index, len(user_files)))

    if ENV_DICT.get('TEST_SAMPLE_SIZE'):
        all_posts = random.sample(all_posts, min(ENV_DICT.get('TEST_SAMPLE_SIZE'), len(all_posts)))
    # filter down to just posts without a link
    _log('++ found {} total posts'.format(len(all_posts)))

    def filter_fun(post):
        content = post.get('content')
        if content.get('link'):
            return False
        else:
            return True
    all_posts = filter(filter_fun, all_posts)

    _log('++ filtered down to {} posts without links'.format(len(all_posts)))

    # filter down to just posts which have a screenshot
    final_posts = []
    for index, post in enumerate(all_posts):
        output_key = post['screenshot_path']
        if file_exists(output_key):
            final_posts.append(post)
        if not index % 10:
            _log('++ {}/{}'.format(index, len(all_posts)))

    # finally make the pdf
    _log('++ making pdf with {} posts'.format(len(final_posts)))

    # download images to folder
    temp_path = tempfile.mkdtemp()
    posts_folder = get_posts_folder()
    num_final_posts = len(final_posts)
    _log('++ about to download {} posts'.format(num_final_posts))
    for index, post in enumerate(final_posts):
        s3_key = post['screenshot_path']
        local_name = s3_key.replace(posts_folder, '')
        local_name = local_name.replace('screenshots/', '')
        local_path = os.path.join(temp_path, local_name)
        post['local_path'] = local_path
        try:
            s3_download_file(s3_path=s3_key, local_path=local_path)
        except Exception as e:
            _capture_exception(e)
            _log("++ couldn't download file {}".format(s3_key))
        if not index % 10:
            _log('++ downloading {}/{}'.format(index, num_final_posts))

    # now create pdf
    pdf = FPDF()
    for index, post in enumerate(final_posts):
        try:
            local_path = post['local_path']
            pdf.add_page()
            pdf.image(name=local_path)
        except Exception as e:
            _capture_exception(e)
        if not index % 10:
            _log('++ combining {}/{}'.format(index, num_final_posts))
    pdf_path = os.path.join(temp_path, 'output.pdf')
    _log('++ writing pdf')
    pdf.output(pdf_path, "F")

    # upload pdf
    _log('++ uploading pdf')
    pdf_s3_path = 'pdfs/{}-{}'.format(
        random.randint(0, 1000000),
        fb_username + '.pdf'
    )
    save_file(source_file_path=pdf_path, destination=pdf_s3_path)

    # send final email
    _log('++ sending results to {}'.format(fb_username))
    pdf_link = get_s3_link(pdf_s3_path)
    send_email(
        to_email=fb_username,
        subject='Facebook Statuses From The Week After November 9, 2016',
        template_path='emails/whats_on_your_mind_result.html',
        template_vars={'pdf_link': pdf_link}
    )

    # remove temp dir
    _log('++ clearing temp directory')
    os.system('rm -r {}'.format(temp_path))

    # log
    _log('++ job complete')


if __name__ == '__main__':
    from osf_scraper_api.web.app import create_app
    app = create_app()
    with app.app_context():
        make_pdf_job(
            fb_username='',
            fb_password=''
        )