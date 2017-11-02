import React, { Component } from 'react';
import Log from './Log.jsx'
import Loader from 'react-loader'

const electron = window.require('electron');
const ipcRenderer  = electron.ipcRenderer;

class Settings extends Component {


    constructor(props) {
        super(props);
        this.state = {
            upInterval: null
        };
        this.handleTurnOffDocker = this.handleTurnOffDocker.bind(this);
        this.handleTurnOnDocker = this.handleTurnOnDocker.bind(this);
        this.handleClearCache = this.handleClearCache.bind(this);
    }


    componentDidMount() {
        const upInterval = setInterval(this.checkOSFUp.bind(this), 1000);
        this.setState({
            upInterval: upInterval,
            isOsfRunningChecked: false
        });
    };

    componentWillUnmount() {
        if (this.state.upInterval) {
            clearInterval(this.state.upInterval);
        }
    };

    checkOSFUp() {
        ipcRenderer.send('is-osf-up', {});
    };

    handleTurnOnDocker() {
        this.props.setElectronState({
            dockerShouldBeUp: true
        });
        ipcRenderer.send('docker-up', {});
    };

    handleTurnOffDocker() {
        this.props.setElectronState({
            dockerShouldBeUp: false
        });
        ipcRenderer.send('docker-down', {});
    };

    handleClearCache() {
        ipcRenderer.send('clear-cache', {});
    };

    render() {
        return (
            <div className="settings">
                <Loader loaded={this.props.electronState.isOsfRunningChecked}>
                    <div className="fadein">
                        <div className="row">
                            <div className="medium-12 columns">
                                <button onClick={this.handleClearCache} className="button osf-button" type="submit">Reset OSF</button>
                            </div>
                            {!this.props.electronState.isOsfRunning && !this.props.electronState.dockerShouldBeUp &&
                            <div className="medium-12 columns">
                                <button onClick={this.handleTurnOnDocker} className="button osf-button" type="submit">Turn Docker On</button>
                            </div>}
                            {this.props.electronState.isOsfRunning && this.props.electronState.dockerShouldBeUp &&
                            <div className="medium-12 columns">
                                <button onClick={this.handleTurnOffDocker} className="button osf-button" type="submit">Turn Docker Off</button>
                            </div>}
                        </div>
                        <div className="row">
                            <div className="medium-12 columns">
                                {!this.props.electronState.isOsfRunning && this.props.electronState.dockerShouldBeUp &&
                                    <div className="osf-starting">OSF is starting</div>
                                }
                                {this.props.electronState.isOsfRunning && !this.props.electronState.dockerShouldBeUp &&
                                    <div className="osf-shutting-down">OSF is shutting down</div>
                                }
                                {this.props.electronState.isOsfRunning && this.props.electronState.dockerShouldBeUp &&
                                    <div className="osf-running">OSF is running {this.props.electronState.heartbeat}</div>
                                }
                                {!this.props.electronState.isOsfRunning && !this.props.electronState.dockerShouldBeUp &&
                                    <div className="osf-not-running">OSF is not running</div>
                                }
                            </div>
                        </div>
                        <Log logLines={this.props.logLines} electronState={this.props.electronState}/>
                    </div>
                </Loader>
            </div>
        );
    }
}

export default Settings;
