const { app, BrowserWindow, ipcMain } = require('electron');
const childProcess = require('child_process');
const os = require('os');
const path = require('path');
const fs = require('fs-extra');
const request = require('request');
const isOnline = require('is-online');

// Keep a global reference of the window object, if you don't, the window will
// be closed automatically when the JavaScript object is garbage collected.
let mainWindow;
const params = {};
let state = {};
let sender;
let jobStatusPollInterval;
let jobStatusPollFun;
let dockerUpPollInterval;
let checkStagePollFun;
let checkStagePollInterval;
let dockerUpPollFun;
let ensureDockerUp;
let tailCmd = null;
let tailCmdPid = null;
let isDockerUp = false;
let initiateJobInterval;
let totalMem = 1;

const homeDir = os.homedir();
const logPath = `${homeDir}/Desktop/osf/data/log.txt`;
function print(msg) {
    if (sender) {
        sender.send('debug', msg);
    }
}

function log(msg) {
    console.log(msg);
    print(msg);
    // fs.appendFile(logPath, msg + '\n');
}


function setState(newState) {
    state = Object.assign(state, newState);
    if (sender) {
        sender.send('set-state', state);
    }
}

function loadJobStatus() {
    const homeDir = os.homedir();
    const dataPath = `${homeDir}/Desktop/osf/data/status.json`;
    if (fs.existsSync(dataPath)) {
        const contents = fs.readFileSync(dataPath);
        return JSON.parse(contents);
    } else {
        return null;
    }
}

function getFilePath(fName) {
    const fPath = path.resolve(__dirname, 'bash', fName);
    return fPath;
}

function runCmd(fName, args, options) {
    const fPath = getFilePath(fName);
    const cArgs = [fPath].concat(args);
    const cmd = childProcess.spawn('/bin/bash', cArgs, options);
    return cmd;
}


function testForDocker(nextStatus) {
    log('++ testing for docker');
    const cmd = runCmd('test_for_docker.sh');

    cmd.stdout.on('data', (data) => {
        log(`++ stdout: ${data}`);
    });

    cmd.stderr.on('data', (data) => {
        log(`++ stderr: ${data}`);
    });

    cmd.on('close', (code) => {
        if (code === 0) {
            log(`++ setting status: ${nextStatus}`);
            setState({ status: nextStatus });
        } else if (code === 7) {
            setState({ status: 'noDocker' });
        } else {
            log(`++ bash error: ${code}`);
        }
    });
}

function printenv() {
    log('++ printenv');
    const cmd = runCmd('printenv.sh');

    cmd.stdout.on('data', (data) => {
        log(`++ stdout: ${data}`);
    });

    cmd.stderr.on('data', (data) => {
        log(`++ stderr: ${data}`);
    });
}

function tailLog() {
    const homeDir = os.homedir();
    const logPath = `${homeDir}/Desktop/osf/data/log.txt`;
    if (!tailCmd) {
        log('++ restarting tail cmd');
        tailCmd = runCmd('tail_log.sh', [logPath]);
        tailCmdPid = tailCmd.pid;
        const closurePid = tailCmdPid;
        const closureLog = (data, cPid) => {
            if (closurePid === cPid) {
                print(`${data}`);
            }
        };
        tailCmd.stdout.on('data', (data) => {
            closureLog(data, tailCmdPid);
        });

        tailCmd.on('close', () => {
            tailCmd = null;
            log('++ tail closed');
        });
    }
}

function clearLog() {
    const homeDir = os.homedir();
    const logPath = `${homeDir}/Desktop/osf/data/log.txt`;
    if (fs.existsSync(logPath)) {
        fs.unlink(logPath);
    }
}

function checkStageAndRestartFailedJobs() {
    if (isDockerUp) {
        log('++ making request to check stage');
        request({
            url: 'http://localhost:80/api/crawler/check_stage/',
            method: 'GET',
        }, (error, response) => {
            if (!error && response.statusCode === 200) {
                log('++ check stage request success');
            } else {
                log('++ docker is currently down, but will attempt to restart within 5 minutes');
            }
        });
    }
}

function initializeStateFromJobStatus() {
    const data = loadJobStatus();
    let nextStatus = 'initial';
    if (data) {
        log(`++ initializeStateFromJobStatus: ${JSON.stringify(data)}`);
        if (data.status === 'downloading posts' || data.status === 'make pdf') {
            log(JSON.stringify(data));
            nextStatus = 'generating';
        } else if (data.status === 'finished') {
            nextStatus = 'finished';
        } else if (data.status === 'login failed') {
            nextStatus = 'login failed';
        }
    }
    testForDocker(nextStatus);
}

function createWindow() {
    log('++ create window');
    mainWindow = new BrowserWindow({ width: 720, height: 480, titleBarStyle: 'hidden', frame: false });
    mainWindow.loadURL(`file://${__dirname}/index.html`);
    mainWindow.on('closed', () => {
        // Dereference the window object, usually you would store windows
        // in an array if your app supports multi windows, this is the time
        // when you should delete the corresponding element.
        mainWindow = null;
    });
    mainWindow.webContents.on('did-finish-load', () => {
        sender = mainWindow.webContents;
        mainWindow.webContents.send('did-finish-load');
        jobStatusPollInterval = setInterval(jobStatusPollFun, 2000);
        dockerUpPollInterval = setInterval(dockerUpPollFun, 300000);
        if (checkStagePollInterval) {
            clearInterval(checkStagePollInterval);
        }
        checkStagePollInterval = setInterval(checkStagePollFun, 60000);
        initializeStateFromJobStatus();
        tailLog();
        totalMem = String(os.totalmem() / 1000.0 / 1000.0 / 1000.0).slice(0, 4);
    });
}

function initiateJob() {
    log('++ waiting for open source feeds to start');
    const initiateJobHelper = () => {
        request({
            url: 'http://localhost:80/api/hello/',
            method: 'GET',
        }, (error, response) => {
            if (!error && response.statusCode === 200) {
                log('++ open source feeds is running');
                request({
                    url: 'http://localhost:80/api/whats_on_your_mind/',
                    method: 'POST',
                    json: true,
                    body: { fb_username: params.fbUsername, fb_password: params.fbPassword },
                }, (err, resp) => {
                    if (!err && resp.statusCode === 200) {
                        log('++ initiate job success');
                        clearInterval(initiateJobInterval);
                    } else {
                        log('++ error initiating job');
                        log(error);
                        log(JSON.stringify(response));
                    }
                });
            } else {
                log('++ waiting for open source feeds to start');
                ensureDockerUp();
            }
        });
    };
    initiateJobInterval = setInterval(initiateJobHelper, 2000);
}

function clearJobStatus() {
    const homeDir = os.homedir();
    const dataPath = `${homeDir}/Desktop/osf/data/status.json`;
    log(`++ clearing job status: ${dataPath}`);
    if (fs.existsSync(dataPath)) {
        fs.unlinkSync(dataPath);
    }
    clearLog();
}

ensureDockerUp = () => {
    log('++ ensure docker is up');
    const dockerComposePath = getFilePath('docker-compose.mac.yml');
    const cmd = runCmd('docker_up.sh', [dockerComposePath]);
    cmd.on('close', (code) => {
        if (code === 0) {
            isDockerUp = true;
        } else {
            log('++ failed to ensure docker is up');
        }
    });
    return cmd;
};

checkStagePollFun = () => {
    checkStageAndRestartFailedJobs();
};

function ensureDockerDown(clearJobStatusFlag) {
    log('++ running docker down');
    const options = {
        detached: true,
        stdio: 'ignore',
    };
    const dockerComposePath = getFilePath('docker-compose.mac.yml');
    const cmd = runCmd('docker_down.sh', [dockerComposePath], options);

    cmd.on('close', (code) => {
        if (code === 0) {
            log('++ docker_down success');
            if (clearJobStatusFlag) {
                clearJobStatus();
            } else {
                log(`++ bash error: ${code}`);
            }
        }
    });
}

jobStatusPollFun = () => {
    const data = loadJobStatus();
    if (data) {
        setState({
            jobStatus: data.status,
            jobMessage: data.message,
        });
        tailLog();
        if (state.status === 'uploading') {
            log('++ uploading');
        } else if ((['uploading', 'finished', 'uploaded'].indexOf(state.status) === -1) && data.status === 'finished') {
            setState({ status: 'finished' });
            // copy pdf from location to desktop
            const homeDir = os.homedir();
            const pdfPath = path.resolve(homeDir, 'Desktop', 'osf', 'data', data.message);
            const outputPath = path.resolve(homeDir, 'Desktop', 'Facebook Statuses From The Week After November 8, 2016.pdf');
            log(`++ copying pdf from ${pdfPath} to ${outputPath}`);
            fs.copySync(pdfPath, outputPath);
            setState({ pdfPath: outputPath });
        } else if (state.status !== 'login failed' && data.status === 'login failed') {
            log('++ login failed');
            setState({
                status: 'login failed',
            });
        } else if (state.status === 'login failed' && data.status !== 'login failed') {
            if (['downloading posts', 'making pdf', 'initializing'].indexOf(data.status) !== -1) {
                setState({ status: 'generating' });
            }
        }
    }
    // const freeMem = String(os.freemem() / 1000.0 / 1000.0 / 1000.0).slice(0, 4);
    // log(`++ free memory: ${freeMem} GB`);
};

dockerUpPollFun = () => {
    const data = loadJobStatus();
    isOnline().then((online) => {
        if (data && online) {
            ensureDockerUp();
        } else if (!online && data && (data.status === 'downloading posts')) {
            log('++ not online, waiting to re-connect to the internet');
            ensureDockerDown();
        }
    });
};

function generateFunction(event, argument) {
    const { fbUsername, fbPassword } = argument;
    params.fbUsername = fbUsername;
    params.fbPassword = fbPassword;
    sender = event.sender;
    setState({ status: 'generating', loadingMessage: Date.now() });
    const cmd = ensureDockerUp();
    cmd.stdout.on('data', (data) => {
        log(`++ ${data}`);
    });

    cmd.stderr.on('data', (data) => {
        log(`++ ${data}`);
    });

    cmd.on('close', (code) => {
        if (code === 0) {
            log('++ start_docker success');
            initiateJob();
            if (tailCmd) {
                tailCmd.kill();
                tailCmd = null;
            }
            tailLog();
        } else if (code === 7) {
            log('++ start_docker failure');
            setState({ status: 'noDocker' });
        } else {
            log(`++ bash error: ${code}`);
        }
    });
}

function initiateHandlers() {
    ipcMain.on('generate', (event, argument) => {
        generateFunction(event, argument);
    });

    ipcMain.on('regenerate', (event, argument) => {
        clearJobStatus();
        generateFunction(event, argument);
    });

    ipcMain.on('stop', (event) => {
        sender = event.sender;
        setState({ status: 'stopped' });
        const homeDir = os.homedir();
        const redisPath = `${homeDir}/Desktop/osf/redis`;
        const cmd = runCmd('stop_job.sh', [redisPath]);
        cmd.on('close', () => {
            ensureDockerDown(true);
        });
    });

    ipcMain.on('upload', () => {
        setState({ status: 'uploading' });
        const dockerUpCmd = ensureDockerUp();
        dockerUpCmd.on('close', () => {
            request({
                url: 'http://localhost:80/api/upload/',
                method: 'POST',
                json: true,
                body: { fb_username: params.fbUsername },
            }, (error, response) => {
                if (!error && response.statusCode === 200) {
                    log('++ upload success');
                    setState({ status: 'uploaded' });
                } else {
                    setState({ status: 'uploaded' });
                    log('++ error uploading');
                }
            });
        });
    });

    ipcMain.on('view', () => {
        const { pdfPath } = state;
        const homeDir = os.homedir();
        const pdfPath2 = path.resolve(homeDir, 'Desktop', 'osf', 'data', state.jobMessage);
        runCmd('view_pdf.sh', [pdfPath || pdfPath2]);
    });
}

// This method will be called when Electron has finished
// initialization and is ready to create browser windows.
// Some APIs can only be used after this event occurs.
app.on('ready', () => {
    createWindow();
    initiateHandlers();
});

app.on('window-all-closed', () => {
    // On OS X it is common for applications and their menu bar
    // to stay active until the user quits explicitly with Cmd + Q
    if (childProcess.platform !== 'darwin') {
        app.quit();
    }
});

app.on('quit', () => {
    ensureDockerDown();
});

app.on('activate', () => {
    // On OS X it's common to re-create a window in the app when the
    // dock icon is clicked and there are no other windows open.
    if (mainWindow === null) {
        createWindow();
    }
});
