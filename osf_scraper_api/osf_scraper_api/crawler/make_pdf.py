import random
import tempfile
import os
import json
import datetime

from fpdf import FPDF
from PIL import Image

from osf_scraper_api.utilities.log_helper import _log, _capture_exception
from osf_scraper_api.utilities.osf_helper import get_fb_scraper
from osf_scraper_api.utilities.fs_helper import file_exists, load_dict, save_file, save_dict
from osf_scraper_api.utilities.s3_helper import s3_download_file, get_s3_link, get_s3_bucket, s3_upload_file
from osf_scraper_api.utilities.email_helper import send_email
from osf_scraper_api.settings import ENV_DICT
from osf_scraper_api.crawler.utils import fetch_friends_of_user, \
    get_posts_folder, get_user_from_user_file
from osf_scraper_api.crawler.utils import get_screenshot_output_key_from_post


def get_final_posts_path(fb_username):
    return 'final/{}.json'.format(fb_username)


def aggregate_posts_job(fb_username, fb_password):
    _log('++ starting aggregate_posts_job for {}'.format(fb_username))
    fb_scraper = get_fb_scraper(fb_username=fb_username, fb_password=fb_password)
    user = fb_scraper.get_currently_logged_in_user()
    fb_scraper.quit_driver()
    friends = fetch_friends_of_user(user)

    # get all extant user_files
    input_folder = get_posts_folder()
    user_files = ['{}/{}.json'.format(input_folder, user) for user in friends]
    all_posts = []
    _log('++ loading posts for {} users'.format(len(user_files)))
    for index, user_file in enumerate(user_files):
        try:
            if not file_exists(user_file):
                continue
            user = get_user_from_user_file(user_file=user_file, input_folder=input_folder)
            data_dict = load_dict(user_file)
            user_posts = data_dict['posts'][user]
            for post in user_posts:
                output_key = get_screenshot_output_key_from_post(user=user, post=post)
                post['screenshot_path'] = output_key
            all_posts.extend(user_posts)
            if ENV_DICT.get('TEST_SAMPLE_SIZE'):
                if len(all_posts) > 100:
                    break
        except Exception as e:
            _capture_exception(e)
            _log('++ failed to load posts for user: {}'.format(user_file))
        if not index % 10:
            _log('++ loading posts {}/{}'.format(index, len(user_files)))

    # filter down to just posts without a link
    _log('++ found {} total posts'.format(len(all_posts)))

    def filter_fun(post):
        content = post.get('content')
        if content.get('link'):
            return False
        else:
            return True
    all_posts = filter(filter_fun, all_posts)

    if ENV_DICT.get('TEST_SAMPLE_SIZE'):
        all_posts = random.sample(all_posts, min(ENV_DICT.get('TEST_SAMPLE_SIZE'), len(all_posts)))

    _log('++ filtered down to {} posts without links'.format(len(all_posts)))

    # filter down to just posts which have a screenshot
    final_posts = []
    for index, post in enumerate(all_posts):
        try:
            output_key = post['screenshot_path']
            if file_exists(output_key):
                final_posts.append(post)
            if not index % 10:
                _log('++ {}/{}'.format(index, len(all_posts)))
        except Exception as e:
            _capture_exception(e)

    # upload final posts to file
    final_path = get_final_posts_path(fb_username)
    data_path = '/srv/data'
    data_json = json.dumps(final_posts)
    local_path = os.path.join(data_path, '{}.json'.format(fb_username))
    _log('++ writing final posts to local file {}'.format(local_path))
    with open(local_path, 'w') as f:
        f.write(data_json)
    _log('++ uploading local file to s3 to {}'.format(final_path))
    for i in range(0, 3):
        _log('++ uploading final posts to {} attempt {}'.format(final_path, i))
        try:
            s3_upload_file(
                source_file_path=local_path,
                destination=final_path
            )
            _log('++ job complete, successful upload to {}'.format(final_path))
            break
        except Exception as e:
            _capture_exception(e)
            continue


def make_pdf_job(fb_username, image_file_dir=None):
    _log('++ starting make_pdf_job for {}'.format(fb_username))
    final_posts_path = get_final_posts_path(fb_username)
    final_posts = load_dict(final_posts_path)
    posts_folder = get_posts_folder()

    # finally make the pdf
    _log('++ making pdf with {} posts'.format(len(final_posts)))

    # folder for downloading images
    downloads_directory = '/tmp/downloads/'
    if not os.path.exists(downloads_directory):
        os.makedirs(downloads_directory)

    # different ways of specifying image_file_dir
    using_temp_directory = False
    if not image_file_dir:
        if ENV_DICT.get('IMAGE_FILE_DIR'):
            image_file_dir = ENV_DICT.get('IMAGE_FILE_DIR')
            _log('++ using image_file_dir from environ {}'.format(image_file_dir))
        else:
            using_temp_directory = True
            image_file_dir = tempfile.mkdtemp(prefix=downloads_directory)
            _log('++ creating temp directory {}'.format(image_file_dir))
    else:
        _log('++ using image_file_dir from kwarg {}'.format(image_file_dir))

    if not os.path.exists(image_file_dir):
        os.makedirs(image_file_dir)

     # download images that haven't already been downloaded
    try:
        num_final_posts = len(final_posts)
        _log('++ about to download {} posts'.format(num_final_posts))
        for index, post in enumerate(final_posts):
            s3_key = post['screenshot_path']
            local_name = s3_key.replace(posts_folder, '')
            local_name = local_name.replace('screenshots/', '')
            local_path = os.path.join(image_file_dir, local_name)
            post['local_path'] = local_path
            try:
                if not os.path.isfile(local_path):
                    s3_download_file(s3_path=s3_key, local_path=local_path)
            except Exception as e:
                _capture_exception(e)
                _log("++ couldn't download file {}".format(s3_key))
            if not index % 20:
                _log('++ downloading {}/{}'.format(index, num_final_posts))

        # now create pdf
        cutoff_date = datetime.datetime(month=11, day=8, year=2016, hour=20)
        def filter_fun(p):
            try:
                d = datetime.datetime.fromtimestamp(int(p['date']))
                if d > cutoff_date:
                    return True
                else:
                    return False
            except:
                return False

        final_posts = filter(filter_fun, final_posts)
        _log('++ filtered down to {} posts'.format(len(final_posts)))
        # final_posts.sort(key=lambda p: p['date'])
        # final_posts = final_posts[:100]
        image_files = [p['local_path'] for p in final_posts]
        pdf_path = os.path.join(image_file_dir, 'output-{}.pdf'.format(fb_username))
        pdf = create_pdf(image_files=image_files, output_path=pdf_path)

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
            to_email='maxhfowler@gmail.com',
            subject='Facebook Statuses From The Week After November 9, 2016',
            template_path='emails/whats_on_your_mind_result.html',
            template_vars={'pdf_link': pdf_link}
        )
    finally:
        if using_temp_directory:
            # remove temp dir
            _log('++ clearing temp directory')
            os.system('rm -r {}'.format(image_file_dir))
        else:
            _log('++ keeping temp files in {}'.format(image_file_dir))

    # log
    _log('++ job complete')


def create_pdf(image_files, output_path):
    pdf = FPDF(unit='pt')
    page_h = pdf.h
    current_h = 0
    pdf.add_page()
    num_image_files = len(image_files)
    for index, local_path in enumerate(image_files):
        try:
            im = Image.open(local_path)
            w_ratio = pdf.w / im.width
            h_ratio = pdf.h / im.height
            if h_ratio > w_ratio:
                w = pdf.w - 200
                ratio = w / im.width
                h = im.height * ratio
                x = (pdf.w - w) / 2.0
                y = 100
            else:
                h = pdf.h - 100
                ratio = h / im.height
                w = im.width * ratio
                x = (pdf.w - w) / 2.0
                y = 50
            if current_h + h + 50 > (page_h - 50):
                pdf.add_page()
                current_h = 0
            y = current_h + 50
            x = (pdf.w - w) / 2.0
            pdf.image(name=local_path, x=x, y=y, w=w, h=h)
            current_h = y + h
        except Exception as e:
            _capture_exception(e)
        if not index % 50:
            _log('++ combining {}/{}'.format(index, num_image_files))

    _log('++ writing pdf to {}'.format(output_path))
    pdf.output(output_path, "F")
    return pdf


def create_scrambled_pdf(image_files, output_path):
    pdf = FPDF(unit='pt')
    page_h = pdf.h
    current_h = 0
    pdf.add_page()
    num_image_files = len(image_files)
    for index, local_path in enumerate(image_files):
        try:
            im = Image.open(local_path)
            w_ratio = pdf.w / im.width
            h_ratio = pdf.h / im.height
            if h_ratio > w_ratio:
                w = pdf.w - 200
                ratio = w / im.width
                h = im.height * ratio
                x = (pdf.w - w) / 2.0
                y = 100
            else:
                h = pdf.h - 100
                ratio = h / im.height
                w = im.width * ratio
                x = (pdf.w - w) / 2.0
                y = 50
            if current_h + h + 50 > (page_h - 50):
                pdf.add_page()
                current_h = 0
            y = random.randint(0, int(0.75*pdf.h))
            x = random.randint(0, int(0.75*pdf.w))
            pdf.image(name=local_path, x=x, y=y, w=w, h=h)
            if random.random() > 0.9:
                pdf.add_page()
        except Exception as e:
            _capture_exception(e)
        if not index % 50:
            _log('++ combining {}/{}'.format(index, num_image_files))

    _log('++ writing pdf to {}'.format(output_path))
    pdf.output(output_path, "F")
    return pdf



if __name__ == '__main__':
    from osf_scraper_api.web.app import create_app
    app = create_app()
    with app.app_context():
        input_path = '/tmp/downloads/JWVT4H'
        make_pdf_job(fb_username='maxhfowler@gmail.com', image_file_dir=input_path)