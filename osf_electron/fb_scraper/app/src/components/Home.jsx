import React, { Component } from 'react';
const electron = window.require('electron');
const ipcRenderer  = electron.ipcRenderer;


class Home extends Component {

    render() {
        return (
             <div className="navbar row">
                <div className="medium-12 columns">
                    OSF is running, use the links above to navigate.
                </div>
            </div>
        );
    }
}

export default Home;
