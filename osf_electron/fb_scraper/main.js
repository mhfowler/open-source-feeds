const electron = require('electron');
// Module to control application life.
const app = electron.app;
const { ipcMain, powerSaveBlocker } = require('electron');
// Module to create native browser window.
const BrowserWindow = electron.BrowserWindow;
const {Menu} = require('electron')

const path = require('path');
const url = require('url');
const childProcess = require('child_process');
const os = require('os');
const fetch = require('node-fetch');
const fs = require('fs-extra');
const isOnline = require('is-online');
const Tail = require('tail').Tail;

// Let electron reloads by itself when webpack watches changes in ./app/
if (process.env.OSF_RELOAD) {
    require('electron-reload')(__dirname);
}

let API_DOMAIN;
if (process.env.OSF_DEV) {
    API_DOMAIN = 'http://localhost:5002';
} else {
    API_DOMAIN = 'http://localhost:80';
}

// Keep a global reference of the window object, if you don't, the window will
// be closed automatically when the JavaScript object is garbage collected.
let mainWindow;
let sender;

let dockerUpPollInterval;
let dockerUpPollFun;
let powerSaveBlockerId;
let pipelinePollInterval;
let ensureDockerUp;
let dockerIsStarting = false;
let dockerBeganStartingTime;
let tail = null;
const assetsPath = path.resolve(__dirname, 'assetts');
const homeDir = os.homedir();
const pipelinePath = `${homeDir}/Desktop/osf/data/pipeline.json`;
const osfDir = `${homeDir}/Desktop/osf`;
const dataDir = `${homeDir}/Desktop/osf/data`;
const logPath = `${homeDir}/Desktop/osf/data/log.txt`;
let electronState = {
    mainWindowLoaded: false,
    electronInitialized: false,
    isDockerUp: false,
    totalMem: 1,
    dockerShouldBeUp: true,
    heartbeat: '',
    pipelineRunning: false,
    dockerWasInitializedAtLeastOnce: false
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
    const fPath = path.resolve(__dirname, 'assetts', fName);
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
            pipelineNumProcessed: data.num_processed,
            pipelineNumTotal: data.num_total
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
    if (!fs.existsSync(logPath)) {
        log('++ creating log file');
        if (!fs.existsSync(osfDir)){
            fs.mkdirSync(osfDir);
        }
        if (!fs.existsSync(dataDir)){
            fs.mkdirSync(dataDir);
        }
        fs.closeSync(fs.openSync(logPath, 'a'));
    }
    if (!tail) {
        log('++ restarting tail');
        tail = new Tail(logPath, {follow: true});

        tail.on("line", function (data) {
            log(data);
        });

        tail.on("error", function (error) {
            log('++ tail closed');
            tail = null;
            setTimeout(() => {
                tailLog();
            }, 1000);
        });
    } else {
        tail.unwatch();
        tail.watch();
    }
}

function clearCache() {
    log('++ clearing OSF cache');
    let dockerDownCmd = ensureDockerDown();
    dockerDownCmd.on('close', (code) => {
        const cmd = runCmd('clear_cache.sh', []);

        cmd.on('close', (code) => {
            if (code === 0) {
                log('++ clear_cache success');
                ensureDockerUp();
            }
            else {
                log('++ clear_cache failure')
            }
        });
    });
}
ipcMain.on('clear-cache', function (event) {
    clearCache();
});

function clearLog() {
    const homeDir = os.homedir();
    const logPath = `${homeDir}/Desktop/osf/data/log.txt`;
    if (fs.existsSync(logPath)) {
        fs.unlink(logPath);
    }
}

ensureDockerUp = () => {
    const now = new Date().getTime() / 1000;
    let shouldStart = false;
    if (dockerBeganStartingTime) {
        const delta = now - dockerBeganStartingTime;
        let maxDelta = 1500;
        if (electronState.dockerWasInitializedAtLeastOnce) {
            maxDelta = 60;
        }
        if (delta > maxDelta) {
            shouldStart = true;
        }
    } else {
        shouldStart = true;
    }
    if (shouldStart) {
        dockerBeganStartingTime = new Date().getTime() / 1000;
        dockerIsStarting = true;
        log('++ ensure docker is up');
        let dockerComposePath;
        if (process.env.OSF_DEV) {
            dockerComposePath = getFilePath('docker-compose.dev.yml');
        } else {
            dockerComposePath = getFilePath('docker-compose.mac.yml');
        }
        const cmd = runCmd('docker_up.sh', [dockerComposePath]);
        cmd.stdout.on('data', (data) => {
            log(`++ ${data}`);
        });
        cmd.stderr.on('data', (data) => {
            log(`++ ${data}`);
        });
        cmd.on('close', (code) => {
            dockerIsStarting = false;
            if (code === 0) {
                electronState.isDockerUp = true;
                if (!electronState.dockerWasInitializedAtLeastOnce) {
                    electronState.dockerWasInitializedAtLeastOnce = true;
                    tailLog();
                }
            } else {
                log('++ failed to ensure docker is up');
                setTimeout(ensureDockerUp, 1000);
            }
        });
        return cmd;
    } else {
        log('++ waiting for docker-compose to start');
    }
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
        dockerBeganStartingTime = null;
        if (code === 0) {
            electronState.isDockerUp = false;
            log('++ docker_down success');
        }
        else {
            log('++ docker_down success');
        }
    });
    return cmd;
}

dockerUpPollFun = () => {
    log('++ running dockerUpPoll');
    if (electronState.dockerShouldBeUp) {
        ensureDockerUp();
    } else {
        ensureDockerDown();
    }
    // ensure computer doesn't go to sleep
    if (!powerSaveBlockerId) {
        // log('++ initializing psb');
        powerSaveBlockerId = powerSaveBlocker.start('prevent-app-suspension');
    } else if (!powerSaveBlocker.isStarted(powerSaveBlockerId)) {
        // log('++ re-initializing psb');
        powerSaveBlockerId = powerSaveBlocker.start('prevent-app-suspension');
    } else {
        // log('++ psb is running');
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
                heartbeat: Date.now(),
                isOsfRunningChecked: true,
            })
        }
        else {
            setElectronState({
                isOsfRunning: false,
                isOsfRunningChecked: true,
            })
        }
    } catch (err) {
        setElectronState({
            isOsfRunning: false,
            isOsfRunningChecked: true,
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
    setElectronState({pipelineRunning: true, pipelineStatus: 'running'});
    fetchFriends(args.fbUsername, args.fbPassword);
});

async function fetchPosts(params) {
    const {fbUsername, fbPassword, afterDate,
        beforeDate, whichPagesSetting, selectedFriends, downloadImages} = params;
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
                download_images: downloadImages
            }),
        });
    } catch (err) {
        log(err.message);
    }
}
ipcMain.on('fetch-posts', function (event, args) {
    log('++ making request to fetch friends');
    clearPipelineState();
    setElectronState({pipelineRunning: true, pipelineStatus: 'running'});
    fetchPosts({
        fbUsername: args.fbUsername,
        fbPassword: args.fbPassword,
        afterDate: args.afterDate,
        beforeDate: args.beforeDate,
        whichPagesSetting: args.whichPagesSetting,
        selectedFriends: args.selectedFriends,
        downloadImages: args.downloadImages,
    });
});

async function generatePDF(params) {
    const {fbUsername, fbPassword, inputDatas, screenshotPosts, chronological} = params;
    try {
        fetch(`${API_DOMAIN}/api/electron/pdf/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify({
                fb_username: fbUsername,
                fb_password: fbPassword,
                input_datas: inputDatas,
                screenshot_posts: screenshotPosts,
                chronological: chronological,
            }),
        });
    } catch (err) {
        log(err.message);
    }
}
ipcMain.on('generate-pdf', function (event, args) {
    log('++ making request to generate pdf');
    clearPipelineState();
    setElectronState({pipelineRunning: true, pipelineStatus: 'running'});
    generatePDF({
        fbUsername: args.fbUsername,
        fbPassword: args.fbPassword,
        inputDatas: args.inputDatas,
        screenshotPosts: args.screenshotPosts,
        chronological: args.chronological,
    });
});

async function stopPipeline() {
    try {
        await fetch(`${API_DOMAIN}/api/electron/stop/`, {
            method: 'GET',
        });
        ensureDockerDown();
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
        log(`++ assets path: ${assetsPath}`);
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

function setApplicationMenu() {
        // Create the Application's main menu
    var template = [{
        label: "Application",
        submenu: [
            { label: "About Application", selector: "orderFrontStandardAboutPanel:" },
            { type: "separator" },
            { label: "Quit", accelerator: "Command+Q", click: function() { app.quit(); }}
        ]}, {
        label: "Edit",
        submenu: [
            { label: "Undo", accelerator: "CmdOrCtrl+Z", selector: "undo:" },
            { label: "Redo", accelerator: "Shift+CmdOrCtrl+Z", selector: "redo:" },
            { type: "separator" },
            { label: "Cut", accelerator: "CmdOrCtrl+X", selector: "cut:" },
            { label: "Copy", accelerator: "CmdOrCtrl+C", selector: "copy:" },
            { label: "Paste", accelerator: "CmdOrCtrl+V", selector: "paste:" },
            { label: "Select All", accelerator: "CmdOrCtrl+A", selector: "selectAll:" }
        ]}
    ];

    Menu.setApplicationMenu(Menu.buildFromTemplate(template));
}

function createWindow() {
    // Create the browser window.
    mainWindow = new BrowserWindow({ width: 720, height: 480, titleBarStyle: 'hidden', frame: false });

    // and load the index.html of the app.
    mainWindow.loadURL(`file://${__dirname}/app/index.html`);
    // mainWindow.loadURL(`file://${__dirname}/index.html`);

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
        if (!process.env.OSF_RELOAD) {
            setApplicationMenu();
        }
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

app.on('quit', () => {
    ensureDockerDown();
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
