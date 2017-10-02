import os
import time
import subprocess

from osf_scraper_api.utilities.log_helper import _log
from osf_scraper_api.settings import ENV_DICT


def restart_selenium():
    ssh_cmd = ENV_DICT.get("HOST_SSH_COMMAND")
    if not ssh_cmd:
        _log('++ HOST_SSH_COMMAND not set, not restarting selenium')
        return
    else:
        _log('++ restarting selenium')
        try:
            cmd = '{ssh_cmd} "BUILD_ENV=staging /usr/local/bin/docker-compose -f /srv/docker-compose.yml restart selenium"'.format(
                ssh_cmd=ssh_cmd
            )
            subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True)
            _log('++ restarted selenium, sleeping for 5')
            time.sleep(5)
        except subprocess.CalledProcessError as e:
            _log('++ failed to restart selenium: {}'.format(e.output))
            raise e


if __name__ == '__main__':
    restart_selenium()