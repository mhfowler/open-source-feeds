import random
import tempfile
import os

from fpdf import FPDF
from PIL import Image

from osf_scraper_api.utilities.log_helper import _log, _capture_exception
from osf_scraper_api.utilities.fs_helper import load_dict, save_file
from osf_scraper_api.utilities.s3_helper import s3_download_file
from osf_scraper_api.electron.utils import save_current_pipeline
from osf_scraper_api.settings import ENV_DICT
from osf_scraper_api.electron.utils import fetch_friends_of_user, \
    get_posts_folder, get_user_from_user_file


def make_pdf_job(posts_file, image_file_dir=None, bottom_crop_pix=5):
    _log('++ starting make_pdf job for {}'.format(posts_file))
    save_current_pipeline(
        pipeline_name='make_pdf',
        pipeline_status='processing'
    )

    # loading posts
    final_posts = load_dict(posts_file)

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

    posts_folder = get_posts_folder()
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

    # create pdf
    image_file_names = [p['image_file_name'] for p in final_posts]
    crop_file_dir = os.path.join(image_file_dir, 'cropped')
    if not os.path.exists(crop_file_dir):
        os.makedirs(crop_file_dir)
    pdf_path = os.path.join(image_file_dir, 'output.pdf')
    pdf = create_pdf(
        image_file_dir=image_file_dir,
        image_file_names=image_file_names,
        crop_file_dir=crop_file_dir,
        output_path=pdf_path,
        bottom_crop_pix=bottom_crop_pix
    )

    # output pdf
    _log('++ saving pdf to {}'.format(output_path))
    save_file(source_file_path=pdf_path, destination=output_path)

    _log('++ job complete')


def create_pdf(image_file_dir, crop_file_dir, image_file_names, output_path, bottom_crop_pix=5):
    pdf = FPDF(unit='pt')
    page_h = pdf.h
    current_h = 0

    # create cover page
    cover_title = "Facebook Statuses From The Week After November 8, 2016"
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