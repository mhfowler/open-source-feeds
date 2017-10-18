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
from osf_scraper_api.utilities.s3_helper import s3_download_file, get_s3_link
from osf_scraper_api.utilities.email_helper import send_email
from osf_scraper_api.crawler.utils import save_job_status
from osf_scraper_api.settings import ENV_DICT
from osf_scraper_api.crawler.utils import fetch_friends_of_user, \
    get_posts_folder, get_user_from_user_file, load_job_params, filter_posts
from osf_scraper_api.crawler.utils import get_screenshot_output_key_from_post


def get_final_posts_path(fb_username):
    return 'final/{}.json'.format(fb_username)


def dedup_posts(posts):
    deduped_list = []
    links_found = set([])
    text_found = set([])
    for post in posts:
        link = post['link']
        if link in links_found:
            continue
        text = post['content'].get('text')
        author = post['content'].get('author')
        if author and text and ((author, text) in text_found):
            continue
        # otherwise this is a new post
        links_found.add(link)
        text_found.add((author, text))
        deduped_list.append(post)
    return deduped_list


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
        if not index % 10:
            _log('++ loading posts {}/{}'.format(index, len(user_files)))
        try:
            if not file_exists(user_file):
                continue
            user = get_user_from_user_file(user_file=user_file, input_folder=input_folder)
            data_dict = load_dict(user_file)
            user_posts = data_dict
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

    # filter down to just posts without a link
    _log('++ found {} total posts'.format(len(all_posts)))

    # dedup
    all_posts = dedup_posts(all_posts)
    _log('++ {} posts after dedup'.format(len(all_posts)))

    # filter posts
    all_posts = filter_posts(all_posts)

    # truncate to test group
    if ENV_DICT.get('TEST_SAMPLE_SIZE'):
        all_posts = random.sample(all_posts, min(ENV_DICT.get('TEST_SAMPLE_SIZE'), len(all_posts)))

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
    _log('++ filtered down to {} posts with screenshots'.format(len(final_posts)))

    # upload final posts to file
    final_path = get_final_posts_path(fb_username)
    data_path = '/srv/data'
    data_json = json.dumps(final_posts)
    local_path = os.path.join(data_path, '{}.json'.format(fb_username))
    _log('++ writing final posts to local file {}'.format(local_path))
    with open(local_path, 'w') as f:
        f.write(data_json)
    _log('++ saving local file to s3 to {}'.format(final_path))
    for i in range(0, 3):
        _log('++ saving final posts to {} attempt {}'.format(final_path, i))
        try:
            save_file(
                source_file_path=local_path,
                destination=final_path
            )
            _log('++ job complete, successfully saved to {}'.format(final_path))
            break
        except Exception as e:
            _capture_exception(e)
            continue


def make_pdf_job(fb_username, image_file_dir=None, bottom_crop_pix=5, not_chronological=False):
    _log('++ starting make_pdf_job for {}'.format(fb_username))
    save_job_status(status='making pdf')
    final_posts_path = get_final_posts_path(fb_username)
    final_posts = load_dict(final_posts_path)
    posts_folder = get_posts_folder()

    # finally make the pdf
    _log('++ making pdf with {} posts'.format(len(final_posts)))

    # dedup test
    final_posts = dedup_posts(final_posts)
    _log('++ {} posts after dedup'.format(len(final_posts)))

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

    # filter down for testing
    if ENV_DICT.get('TEST_SAMPLE_SIZE'):
        final_posts = random.sample(final_posts, min(ENV_DICT.get('TEST_SAMPLE_SIZE'), len(final_posts)))

    try:
        num_final_posts = len(final_posts)
        _log('++ num final posts {}'.format(num_final_posts))
        # if using S3, download images that haven't already been downloaded
        if ENV_DICT['FS_BIN_TYPE'] == 'S3':
            _log('++ about to download {} posts'.format(num_final_posts))
            for index, post in enumerate(final_posts):
                s3_key = post['screenshot_path']
                local_name = s3_key.replace(posts_folder, '')
                local_name = local_name.replace('screenshots/', '')
                local_path = os.path.join(image_file_dir, local_name)
                post['image_file_name'] = local_name
                post['local_path'] = local_path
                try:
                    if not os.path.isfile(local_path):
                        s3_download_file(s3_path=s3_key, local_path=local_path)
                except Exception as e:
                    _capture_exception(e)
                    _log("++ couldn't download file {}".format(s3_key))
                if not index % 20:
                    _log('++ downloading {}/{}'.format(index, num_final_posts))
        # otherwise we already have images locally
        else:
            _log('++ pulling images directly from /srv/fs/screenshots')
            for index, post in enumerate(final_posts):
                screenshot_path = post['screenshot_path']
                local_name = screenshot_path.replace(posts_folder, '')
                local_name = local_name.replace('screenshots/', '')
                post['image_file_name'] = local_name
                post['local_path'] = os.path.join(image_file_dir, local_name)

        # now create pdf
        final_posts = filter_posts(final_posts)

        # shuffle posts if not_chronological
        if not_chronological:
            random.shuffle(final_posts)
        else:
            final_posts.sort(key=lambda post: int(post['date']))

        # create pdf
        image_file_names = [p['image_file_name'] for p in final_posts]
        crop_file_dir = os.path.join(image_file_dir, 'cropped')
        if not os.path.exists(crop_file_dir):
            os.makedirs(crop_file_dir)
        pdf_path = os.path.join(image_file_dir, 'output-{}.pdf'.format(fb_username))
        pdf = create_pdf(
            image_file_dir=image_file_dir,
            image_file_names=image_file_names,
            crop_file_dir=crop_file_dir,
            output_path=pdf_path,
            bottom_crop_pix=bottom_crop_pix
        )
        # pdf = create_pdf_by_day(
        #     image_file_dir=image_file_dir,
        #     posts=final_posts,
        #     crop_file_dir=crop_file_dir,
        #     output_path=pdf_path
        # )

        # upload pdf
        pdf_s3_path = 'pdfs/{}-{}'.format(
            random.randint(0, 1000000),
            fb_username + '.pdf'
        )
        _log('++ saving pdf to {}'.format(pdf_path))
        save_file(source_file_path=pdf_path, destination=pdf_s3_path)

        if ENV_DICT['FS_BIN_TYPE'] == 'S3':
            # send final email
            pdf_link = get_s3_link(pdf_s3_path)
            _log('++ view pdf at: {}'.format(pdf_link))
            _log('++ sending results to {}'.format(fb_username))
            send_email(
                to_email=fb_username,
                # to_email='maxhfowler@gmail.com',
                subject='Facebook Statuses From The Week After November 9, 2016',
                template_path='emails/whats_on_your_mind_result.html',
                template_vars={'pdf_link': pdf_link}
            )
        else:
            _log('++ loading initial job params')
            job_params = load_job_params(fb_username=fb_username)
            output_path = job_params.get('output_path')
            if output_path:
                _log('++ copying pdf to output_path: {}'.format(output_path))
                os.system('cp {} {}'.format(pdf_path, output_path))
    finally:
        if using_temp_directory:
            # remove temp dir
            _log('++ clearing temp directory')
            os.system('rm -r {}'.format(image_file_dir))
        else:
            _log('++ keeping temp files in {}'.format(image_file_dir))

    # log
    save_job_status(status='finished', message=pdf_s3_path)
    _log('++ job complete')


def create_pdf(image_file_dir, crop_file_dir, image_file_names, output_path, bottom_crop_pix=5):
    pdf = FPDF(unit='pt')
    page_h = pdf.h
    current_h = 0

    # create cover page
    cover_title = "Facebook Statuses From The Week After November 9, 2016"
    pdf.add_page()
    pdf.set_font('Arial', 'B', 16)
    # pdf.set_x(50)
    # pdf.set_y(50)
    # pdf.cell(w=50, h=50, txt=cover_title, border=0)
    # pdf.text(x=65, y=100, txt=cover_title)
    # pdf.text(x=65, y=pdf.h/2.0, txt=cover_title)
    pdf.text(x=65, y=50, txt=cover_title)
    pdf.add_page()

    # create the rest of the pdf
    num_image_files = len(image_file_names)
    for index, f_name in enumerate(image_file_names):
        local_path = os.path.join(image_file_dir, f_name)
        crop_path = os.path.join(crop_file_dir, f_name)
        try:
            im = Image.open(local_path)
            # crop some pixels off image
            crop_pix = 10
            im = im.crop(
                (
                    crop_pix+1,
                    crop_pix+1,
                    im.width-crop_pix-1,
                    im.height-crop_pix-bottom_crop_pix
                )
            )
            im.save(crop_path)
            im = Image.open(crop_path)
            format = 'left-aligned'
            if format == 'center':
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
                pdf.image(name=crop_path, x=x, y=y, w=w, h=h)
                pdf.set_line_width(1)
                current_h = y + h
            else:
                h = im.height
                w = im.width
                max_height = page_h - 100
                max_width = pdf.w - 150
                if current_h + h + 50 > (page_h - 50):
                    pdf.add_page()
                    current_h = 0
                if im.height > max_height:
                    ratio = max_height / im.height
                    h = im.height * ratio
                    w = im.width * ratio
                elif im.width > max_width:
                    ratio = max_width / im.width
                    h = im.height * ratio
                    w = im.width * ratio
                y = current_h + 50
                x = 50
                pdf.image(name=crop_path, x=x, y=y, w=w, h=h)
                pdf.set_fill_color(255, 255, 255)
                pdf.set_draw_color(255, 255, 255)
                pdf.rect(x=(x+w)-30, y=y, w=30, h=30, style='F')
                current_h = y + h
        except Exception as e:
            _capture_exception(e)
        if not index % 50:
            _log('++ combining {}/{}'.format(index, num_image_files))

    _log('++ writing pdf to {}'.format(output_path))
    pdf.output(output_path, "F")
    return pdf


def create_pdf_by_day(image_file_dir, crop_file_dir, posts, output_path):
    pdf = FPDF(unit='pt')
    page_h = pdf.h
    current_h = 0

    # create cover page
    cover_title = "Table Of Contents"
    pdf.add_page()
    pdf.set_font('Arial', 'B', 16)
    pdf.text(x=65, y=50, txt=cover_title)

    day_links = {}
    for day_index in range(0, 7):
        link = pdf.add_link()
        day_links[day_index] = link
        x = 65
        y = 80+(30*day_index)
        h = 20
        pdf.link(x=65, y=y-h, w=pdf.w, h=h, link=link)
        day = 9 + day_index
        text = 'November {}'.format(day)
        pdf.set_font('Arial', size=14)
        pdf.set_draw_color(0, 0, 255)
        pdf.text(x=x, y=y, txt=text)

    for post in posts:
        post['datetime'] = datetime.datetime.fromtimestamp(post['date'])

    for day_index in range(0, 7):
        day = 9 + day_index
        cover_title = "Facebook Statuses From November {}, 2016".format(day)
        pdf.add_page()
        pdf.set_font('Arial', 'B', 16)
        pdf.text(x=65, y=50, txt=cover_title)
        day_link = day_links[day_index]
        pdf.set_link(link=day_link, page=pdf.page)
        pdf.add_page()
        current_h = 0

        posts_on_day = filter(lambda post: post['datetime'].day == day, posts)
        posts_on_day.sort(key=lambda post: post['date'])
        # create the rest of the pdf
        num_image_files = len(posts_on_day)
        for index, post in enumerate(posts_on_day):
            f_name = post['image_file_name']
            local_path = os.path.join(image_file_dir, f_name)
            crop_path = os.path.join(crop_file_dir, f_name)
            try:
                im = Image.open(local_path)
                # crop some pixels off image
                crop_pix = 10
                im = im.crop(
                    (
                        crop_pix+1,
                        crop_pix+1,
                        im.width-crop_pix-1,
                        im.height-crop_pix-4
                    )
                )
                im.save(crop_path)
                im = Image.open(crop_path)
                h = im.height
                w = im.width
                max_height = page_h - 100
                max_width = pdf.w - 150
                if current_h + h + 50 > (page_h - 50):
                    pdf.add_page()
                    current_h = 0
                if im.height > max_height:
                    ratio = max_height / im.height
                    h = im.height * ratio
                    w = im.width * ratio
                elif im.width > max_width:
                    ratio = max_width / im.width
                    h = im.height * ratio
                    w = im.width * ratio
                y = current_h + 50
                x = 50
                pdf.image(name=crop_path, x=x, y=y, w=w, h=h)
                pdf.set_fill_color(255, 255, 255)
                pdf.set_draw_color(255, 255, 255)
                pdf.rect(x=(x+w)-30, y=y, w=30, h=30, style='F')
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
    output_path = '/Users/maxfowler/Desktop/output.pdf'
    with app.app_context():
        input_path = '/tmp/downloads/JWVT4H'
        image_file_names = os.listdir(input_path)
        image_file_dir = input_path
        # crop_file_dir = '/tmp/downloads/crop'
        # if not os.path.exists(crop_file_dir):
        #     os.makedirs(crop_file_dir)
        # create_pdf(
        #     image_file_names=image_file_names,
        #     image_file_dir=image_file_dir,
        #     crop_file_dir=crop_file_dir,
        #     output_path=output_path
        # )
        # make_pdf_job(fb_username='happyrainbows93@yahoo.com', image_file_dir=image_file_dir)
        make_pdf_job(fb_username='maxhfowler@gmail.com', image_file_dir=image_file_dir)