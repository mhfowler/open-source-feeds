// This file is required by the index.html file and will
// be executed in the renderer process for that window.
// All of the Node.js APIs are available in this process.

const { ipcRenderer } = require('electron');
const $ = require('jquery');

const setApplicationMenu = require('./menu');

const form = document.querySelector('form');
let state = {};


const inputs = {
    fbUsername: form.querySelector('input[name="fb-username"]'),
    fbPassword: form.querySelector('input[name="fb-password"]'),
};


const buttons = {
    generate: document.getElementById('generate-button'),
    regenerate: document.getElementById('regenerate-button'),
    stop: document.getElementById('stop-button'),
    continue: document.getElementById('continue-button'),
    upload: document.getElementById('upload-button'),
    view: document.getElementById('view-button'),
    view2: document.getElementById('view-button2'),
};

function setState(newState) {
    state = Object.assign(state, newState);
    $('.state').html(JSON.stringify(state));
    if (state.status === 'initial') {
        $('.no-docker').hide();
        $('.main-window').show();
        $('.optional').hide();
        $('.generate-button').show();
        $('.osf-explanation').show();
        $('.debug').hide();
    } else if (state.status === 'login failed') {
        $('.no-docker').hide();
        $('.main-window').show();
        $('.optional').hide();
        $('.regenerate-button').show();
        $('.login-failed').show();
        $('.debug').hide();
    } else if (state.status === 'generating') {
        $('.main-window').show();
        $('.optional').hide();
        $('.stop-button').hide();
        $('.success-alert').show();
        $('.debug').show();
    } else if (state.status === 'finished') {
        $('.main-window').show();
        $('.optional').hide();
        $('.stop-button').hide();
        $('.view-button').show();
        $('.upload-button').hide();
        $('.finished').show();
        $('.debug').hide();
    } else if (state.status === 'uploading') {
        $('.main-window').show();
        $('.optional').hide();
        $('.stop-button').hide();
        $('.finished').show();
        $('.uploading').show();
    } else if (state.status === 'uploaded') {
        $('.main-window').show();
        $('.optional').hide();
        $('.uploaded').show();
        $('.debug').hide();
    } else if (state.status === 'stopped') {
        $('.optional').hide();
        $('.generate-button').show();
        $('.debug').empty();
    } else if (state.status === 'noDocker') {
        $('.main-window').hide();
        $('.optional').hide();
        $('.generate-button').show();
        $('.no-docker').show();
    }
}

ipcRenderer.on('did-finish-load', () => {
    setApplicationMenu();
    mainWindow.$ = $;
});

ipcRenderer.on('set-state', (event, newState) => {
    console.log('++ set-state event');
    setState(newState);
});

ipcRenderer.on('debug', (event, msg) => {
    const debug = $('.debug');
    debug.prepend(`<div> ${msg} </div>`);
    const children = debug.children();
    const numChildren = children.length;
    if (numChildren > 20) {
        const firstChild = debug.find(':last-child');
        firstChild.remove();
    }
    $('.uploading').html(`++ uploading (usually takes 2-3 minutes) ${Date.now()}`);
});

ipcRenderer.on('processing-did-fail', (event, error) => {
    console.error(error);
    alert('error');
});

buttons.generate.addEventListener('click', (event) => {
    event.preventDefault();
    ipcRenderer.send('generate', {
        fbUsername: inputs.fbUsername.value,
        fbPassword: inputs.fbPassword.value,
    });
});

buttons.regenerate.addEventListener('click', (event) => {
    event.preventDefault();
    ipcRenderer.send('regenerate', {
        fbUsername: inputs.fbUsername.value,
        fbPassword: inputs.fbPassword.value,
    });
});

buttons.stop.addEventListener('click', (event) => {
    event.preventDefault();
    ipcRenderer.send('stop', {});
});

buttons.continue.addEventListener('click', (event) => {
    event.preventDefault();
    setState({ status: 'initial' });
});

buttons.upload.addEventListener('click', (event) => {
    event.preventDefault();
    $('.debug').empty();
    ipcRenderer.send('upload', {});
});

buttons.view.addEventListener('click', (event) => {
    event.preventDefault();
    ipcRenderer.send('view', {});
});

buttons.view2.addEventListener('click', (event) => {
    event.preventDefault();
    ipcRenderer.send('view', {});
});