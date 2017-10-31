import React, { Component } from 'react';
import Log from './Log.jsx'

const electron = window.require('electron');
const ipcRenderer  = electron.ipcRenderer;

class Initializing extends Component {

    constructor(props) {
        super(props);
        this.state = {
            upInterval: null
        };
    }

    componentDidMount() {
        const upInterval = setInterval(this.checkOSFUp.bind(this), 1000);
        this.setState({
            upInterval: upInterval,
            isOsfRunningChecked: false
        });
        ipcRenderer.send('docker-up', {});
    };

    componentWillUnmount() {
        if (this.state.upInterval) {
            clearInterval(this.state.upInterval);
        }
    };

    checkOSFUp() {
        ipcRenderer.send('is-osf-up', {});
    };

    render() {
        return (
            <div className="settings">
                <div className="fadein">
                    <div className="row">
                        <div className="medium-12 columns">
                            OSF is initializing (takes 5-10 minutes the first time).
                        </div>
                    </div>
                    <Log logLines={this.props.logLines} electronState={this.props.electronState}/>
                </div>
            </div>
        );
    }
}

export default Initializing;
