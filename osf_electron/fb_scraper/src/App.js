import React, { Component } from 'react';
import { HashRouter, withRouter } from 'react-router-dom'
import './App.css';
import './foundation.css';
import './styles.css';
import NotificationSystem from 'react-notification-system'
import FacebookScraper from './facebook/FacebookScraper'
import Settings from './Settings'
import Container from './Container'
const electron = window.require('electron');
const fs = require('fs');
const ipcRenderer  = electron.ipcRenderer;


class RouterApp extends Component {
    static get childContextTypes() {
        return {
            notify: React.PropTypes.func
        }
    }

    getChildContext() {
        return {
            notify: this.notify.bind(this),
        }
    }

    notify(notification) {
        this.notifications.addNotification(notification)
    }

    render() {
        return (
            <main>
                <NotificationSystem ref={notifications => { this.notifications = notifications }} style={false} />
                <HashRouter>
                    <Container/>
                </HashRouter>
            </main>
        );
    }
}


export default RouterApp;
