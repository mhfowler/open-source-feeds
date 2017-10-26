import React, { Component } from 'react';
const electron = window.require('electron');
const ipcRenderer  = electron.ipcRenderer;


class Home extends Component {

    render = () => {
        return (
             <div className="navbar row">
                <div className="medium-12 columns">
                    Welcome to Open Source Feeds
                </div>
                  <div className="medium-12 columns">
                    ∆∆∆∆∆∆∆∆∆∆∆∆∆∆∆∆∆∆∆∆
                </div>
            </div>
        );
    }
}

export default Home;
