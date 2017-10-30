const electron = require('electron');
// Module to control application life.
const app = electron.app;
const { ipcMain } = require('electron');
// Module to create native browser window.
const BrowserWindow = electron.BrowserWindow;

const path = require('path');
const url = require('url');
const childProcess = require('child_process');
const os = require('os');
const fetch = require('node-fetch');
const fs = require('fs-extra');
const isOnline = require('is-online');

const API_DOMAIN = 'http://localhost:5002';
// const API_DOMAIN = 'http://localhost:80';

// Keep a global reference of the window object, if you don't, the window will
// be closed automatically when the JavaScript object is garbage collected.
let mainWindow;
let sender;

let dockerUpPollInterval;
let dockerUpPollFun;
let pipelinePollInterval;
let ensureDockerUp;
let tailCmd = null;
let tailCmdPid = null;
const homeDir = os.homedir();
const pipelinePath = `${homeDir}/Desktop/osf/data/pipeline.json`;
let electronState = {
    mainWindowLoaded: false,
    electronInitialized: false,
    isDockerUp: false,
    totalMem: 1,
    dockerShouldBeUp: false,
    heartbeat: '',
    pipelineRunning: false,
};


function print(msg) {
    if (sender) {
        sender.send('print-message', msg);
    }
}

function log(msg) {
    print(msg);
}

function setElectronState(newState) {
    electronState = Object.assign(electronState, newState);
    if (sender) {
        sender.send('set-electron-state', electronState);
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
            setElectronState({ status: nextStatus });
        } else if (code === 7) {
            setElectronState({ status: 'noDocker' });
        } else {
            log(`++ bash error: ${code}`);
        }
    });
}

function clearPipelineState() {
   log('++ clearing old pipeline state');
   if (fs.existsSync(pipelinePath)) {
       fs.unlink(pipelinePath);
   }
}

function loadPipelineState() {
    if (fs.existsSync(pipelinePath)) {
        const contents = fs.readFileSync(pipelinePath);
        const data = JSON.parse(contents);
        let pipelineRunning;
        if (data.pipeline_status === 'running') {
            pipelineRunning = true;
        }
        else {
            pipelineRunning = false;
        }
        const pipelineState = {
            pipelineName: data.pipeline_name,
            pipelineStatus: data.pipeline_status,
            pipelineRunning: pipelineRunning,
            pipelineMessage: data.pipeline_message,
            pipelineParams: data.pipeline_params,
        };
        setElectronState(pipelineState)
    } else {
        setElectronState({
            pipelineRunning: false,
            pipelineName: '',
            pipelineStatus: ''
        })
    }
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

ensureDockerUp = () => {
    log('++ ensure docker is up');
    const dockerComposePath = getFilePath('docker-compose.mac.yml');
    const cmd = runCmd('docker_up.sh', [dockerComposePath]);
    cmd.on('close', (code) => {
        if (code === 0) {
            electronState.isDockerUp = true;
        } else {
            log('++ failed to ensure docker is up');
        }
    });
    return cmd;
};

function ensureDockerDown() {
    log('++ running docker down');
    const options = {
        detached: true,
        stdio: 'ignore',
    };
    const dockerComposePath = getFilePath('docker-compose.mac.yml');
    const cmd = runCmd('docker_down.sh', [dockerComposePath], options);

    cmd.on('close', (code) => {
        if (code === 0) {
            electronState.isDockerUp = false;
            log('++ docker_down success');
        }
        else {
            log('++ docker_down failure')
        }
    });
}

dockerUpPollFun = () => {
    log('++ running dockerUpPoll');
    if (electronState.dockerShouldBeUp) {
        ensureDockerUp();
    } else {
        ensureDockerDown();
    }
};

async function isOSFUp() {
    try {
        const resp = await fetch(`${API_DOMAIN}/api/is_up/`, {
            method: 'GET',
        });
        const data = await resp.json();
        if (data.status === 'running') {
            setElectronState({
                isOsfRunning: true,
                heartbeat: Date.now()
            })
        }
        else {
            setElectronState({
                isOsfRunning: false
            })
        }
    } catch (err) {
        console.log(err);
        log('++ osf is down');
        setElectronState({
            isOsfRunning: false
        })
    }
}
ipcMain.on('is-osf-up', function (event) {
    isOSFUp();
});

async function fetchFriends(fbUsername, fbPassword) {
    try {
        fetch(`${API_DOMAIN}/api/electron/fb_friends/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify({
                fb_username: fbUsername,
                fb_password: fbPassword
            }),
        });
    } catch (err) {
        log(err.message);
    }
}
ipcMain.on('fetch-friends', function (event, args) {
    log('++ making request to fetch friends');
    clearPipelineState();
    setElectronState({pipelineRunning: true});
    fetchFriends(args.fbUsername, args.fbPassword);
});

async function fetchPosts(params) {
    const {fbUsername, fbPassword, afterDate, beforeDate, whichPagesSetting, selectedFriends} = params;
    try {
        fetch(`${API_DOMAIN}/api/electron/fb_posts/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify({
                fb_username: fbUsername,
                fb_password: fbPassword,
                after_date: afterDate,
                before_date: beforeDate,
                selected_friends: selectedFriends,
                which_pages_setting: whichPagesSetting,
            }),
        });
    } catch (err) {
        log(err.message);
    }
}
ipcMain.on('fetch-posts', function (event, args) {
    log('++ making request to fetch friends');
    clearPipelineState();
    setElectronState({pipelineRunning: true});
    fetchPosts({
        fbUsername: args.fbUsername,
        fbPassword: args.fbPassword,
        afterDate: args.afterDate,
        beforeDate: args.beforeDate,
        whichPagesSetting: args.whichPagesSetting,
        selectedFriends: args.selectedFriends
    });
});

async function stopPipeline() {
    try {
        fetch(`${API_DOMAIN}/api/electron/stop/`, {
            method: 'GET',
        });
    } catch (err) {
        log(err.message);
    }
}
ipcMain.on('stop-pipeline', function (event, args) {
    log('++ making request to stop current pipeline');
    stopPipeline();
});

async function getFacebookFriends() {
    try {
        const resp = await fetch(`${API_DOMAIN}/api/electron/fb_friends/`, {
            method: 'GET',
        });
        const data = await resp.json();
        setTimeout(() => {
            setElectronState({
               fbFriendsRequest: {
                   loaded: true,
                   friends: data.friends
               }
            });
        }, 200)

    } catch (err) {
    }
}
ipcMain.on('get-fb-friends', function (event, args) {
    log('++ making request to get facebook friends');
    getFacebookFriends()
});

function initializeElectron() {
    if (!electronState.electronInitialized) {
        log('++ initializing electron');
        log(`++ using API: ${API_DOMAIN}`);
        dockerUpPollInterval = setInterval(dockerUpPollFun, 30000);
        pipelinePollInterval = setInterval(loadPipelineState, 1000);
        tailLog();
        const totalMem = String(os.totalmem() / 1000.0 / 1000.0 / 1000.0).slice(0, 4);
        setElectronState({
            electronInitialized: true,
            totalMem: totalMem,
        });
    }
}

function createWindow() {
    // Create the browser window.
    mainWindow = new BrowserWindow({ width: 720, height: 480, titleBarStyle: 'hidden', frame: false });

    // and load the index.html of the app.
    const startUrl = process.env.ELECTRON_START_URL || url.format({
            pathname: path.join(`${__dirname}/../build/index.html`),
            protocol: 'file:',
            slashes: true
        });
    mainWindow.loadURL(startUrl);
    // Open the DevTools.
    mainWindow.webContents.openDevTools();

    // Emitted when the window is closed.
    mainWindow.on('closed', function () {
        // Dereference the window object, usually you would store windows
        // in an array if your app supports multi windows, this is the time
        // when you should delete the corresponding element.
        mainWindow = null
    });

    mainWindow.webContents.on('did-finish-load', () => {
        sender = mainWindow.webContents;
        setElectronState({
            mainWindowLoaded:  true
        });
        initializeElectron();
    });
}

// listeners from React
ipcMain.on('test-event', function (event) {
    sender = event.sender;
    print('++ test event');
});

ipcMain.on('docker-up', function (event) {
    sender = event.sender;
    ensureDockerUp();
});

ipcMain.on('docker-down', function (event) {
    sender = event.sender;
    ensureDockerDown();
});


ipcMain.on('react-set-electron-state', function (event, data) {
    sender = event.sender;
    setElectronState(data);
});

// This method will be called when Electron has finished
// initialization and is ready to create browser windows.
// Some APIs can only be used after this event occurs.
app.on('ready', createWindow);

// Quit when all windows are closed.
app.on('window-all-closed', function () {
    // On OS X it is common for applications and their menu bar
    // to stay active until the user quits explicitly with Cmd + Q
    if (process.platform !== 'darwin') {
        app.quit()
    }
});

app.on('activate', function () {
    // On OS X it's common to re-create a window in the app when the
    // dock icon is clicked and there are no other windows open.
    if (mainWindow === null) {
        createWindow()
    }
});

// In this file you can include the rest of your app's specific main process
// code. You can also put them in separate files and require them here.
