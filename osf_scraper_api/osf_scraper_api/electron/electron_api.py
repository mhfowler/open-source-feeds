import time

from flask import make_response, jsonify, Blueprint, request, abort

from osf_scraper_api.electron.fb_posts import scrape_fb_posts_job, fb_posts_post_process
from osf_scraper_api.electron.screenshot import screenshot_job, screenshots_post_process
from osf_scraper_api.electron.utils import save_current_pipeline, load_current_pipeline
from osf_scraper_api.electron.make_pdf import make_pdf_job
from osf_scraper_api.electron.fb_friends import scrape_fb_friends
from osf_scraper_api.settings import TEMPLATE_DIR
from osf_scraper_api.utilities.log_helper import _log
from osf_scraper_api.utilities.osf_helper import paginate_list, load_last_uptime
from osf_scraper_api.utilities.rq_helper import enqueue_job, restart_failed_jobs
from osf_scraper_api.settings import NUMBER_OF_POST_SWEEPS


def get_electron_api_blueprint():
    electron_blueprint = Blueprint('electron_blueprint', __name__, template_folder=TEMPLATE_DIR)

    @electron_blueprint.route('/api/electron/fb_friends/', methods=['POST'])
    def fb_friends_endpoint():
        _log('++ received request to friends endpoint')
        params = request.get_json()

        required_fields = [
            'fb_username',
            'fb_password',
        ]
        for req_field in required_fields:
            if req_field not in params.keys():
                abort(make_response(jsonify({'message': '{} field is required.'.format(req_field)}), 422))

        enqueue_job(scrape_fb_friends,
            fb_username=params['fb_username'],
            fb_password=params['fb_password'],
            timeout=108000
        )
        return make_response(jsonify({
            'message': 'fb_friend job enqueued'
        }), 200)

    @electron_blueprint.route('/api/electron/fb_posts/', methods=['POST'])
    def fb_posts_endpoint():
        _log('++ received request to posts endpoint')
        params = request.get_json()

        required_fields = [
            'users',
            'fb_username',
            'fb_password',
        ]
        for req_field in required_fields:
            if req_field not in params.keys():
                abort(make_response(jsonify({'message': '{} field is required.'.format(req_field)}), 422))

        users = params['users']
        page_size = 50
        pages = paginate_list(mylist=users, page_size=page_size)
        job_ids = []
        for sweep_number in range(0, NUMBER_OF_POST_SWEEPS):
            _log('++ enqueing {num_users} users in {num_jobs} jobs, #{sweep_number}'.format(
                num_users=len(users),
                num_jobs=len(pages),
                sweep_number=sweep_number
            ))
            for index, page in enumerate(pages):
                _log('++ enqueing {} job'.format(index))
                job = enqueue_job(scrape_fb_posts_job,
                    users=page,
                    params=params,
                    fb_username=params['fb_username'],
                    fb_password=params['fb_password'],
                    timeout=5000
                )
                job_ids.append(job.id)
        # save which job_ids are in this stage
        save_current_pipeline(
            pipeline_name='fb_posts',
            pipeline_status='running'
        )
        # finally return 'OK' response
        return make_response(jsonify({
            'message': 'fb_posts job enqueued'
        }), 200)

    @electron_blueprint.route('/api/electron/check_pipeline/', methods=['GET'])
    def check_job_stage_endpoint():
        _log('++ received request to pipeline endpoint')
        pipeline_dict = load_current_pipeline()
        if not pipeline_dict:
            _log('++ no pipeline found')
            return make_response(jsonify({
                'message': 'no pipeline found'
            }), 200)
        pipeline_name = pipeline_dict['pipeline_name']
        restart_failed_jobs()
        time.sleep(2)
        # check how recently docker was restarted, if < 3 minutes... then don't advance stage
        last_uptime = load_last_uptime()
        now = int(time.time())
        total_uptime_seconds = now - last_uptime
        if (total_uptime_seconds < 60*3):
            _log('++ skipping pipeline check due to recent restart')
            return make_response(jsonify({
                'message': 'ok'
            }), 200)
        _log('++ checking whether pipeline is complete')
        if pipeline_name == 'posts':
            _log('++ checking whether posts pipeline is complete')
            fb_posts_post_process()
        elif pipeline_name == 'screenshots':
            _log('++ checking whether screenshots pipeline is complete')
            screenshots_post_process()
        else:
            raise Exception('++ invalid pipeline: {}'.format(pipeline_name))
        return make_response(jsonify({
            'message': 'ok'
        }), 200)

    @electron_blueprint.route('/api/electron/fb_screenshots/', methods=['POST'])
    def fb_screenshots_endpoint():
        params = request.get_json()
        input_folder = params['input_folder']
        fb_username = params['fb_username']
        fb_password = params['fb_password']

        enqueue_job(screenshot_job,
            input_folder=input_folder,
            fb_username=fb_username,
            fb_password=fb_password,
            timeout = 3600
        )
        return make_response(jsonify({
            'message': 'fb_screenshot job enqueued'
        }), 200)

    @electron_blueprint.route('/api/electron/pdf/', methods=['POST'])
    def make_pdf_endpoint():
        params = request.get_json()
        bottom_crop_pix = params.get('bottom_crop_pix', 5)
        not_chronological = params.get('not_chronological', False)
        _log('++ enqueing make_pdf_job')
        enqueue_job(make_pdf_job,
                    bottom_crop_pix=bottom_crop_pix,
                    not_chronological=not_chronological,
                    timeout=432000)
        return make_response(jsonify({
            'message': 'pdf job enqueued'
        }), 200)

    return electron_blueprint
