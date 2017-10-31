import React, { Component } from 'react';
import Log from './Log.jsx'
const electron = window.require('electron');
const ipcRenderer  = electron.ipcRenderer;


class PipelineRunning extends Component {

    constructor(props) {
        super(props);
        this.handleClickStopPipeline = this.handleClickStopPipeline.bind(this);
    }

    handleClickStopPipeline() {
        ipcRenderer.send('stop-pipeline', {});
    };

    render() {
        let showProgress = false;
        if (this.props.electronState.pipelineNumTotal && this.props.electronState.pipelineNumTotal !== 0) {
            showProgress = true;
        }
        return (
            <div className="pipeline-running">
               <div className="row">
                   <div className="medium-12 columns">
                       <strong>pipeline running: {this.props.electronState.pipelineName}</strong>
                   </div>
                   {showProgress &&
                   <div className="medium-12 columns">
                        processed {this.props.electronState.pipelineNumProcessed} of {this.props.electronState.pipelineNumTotal}
                   </div>}
                </div>
                <div className="row">
                    <div className="medium-12 columns">
                        <button onClick={this.handleClickStopPipeline} className="button osf-button">Stop Pipeline</button>
                    </div>
                </div>
                <Log logLines={this.props.logLines} electronState={this.props.electronState}/>
            </div>
        )
    }
}

export default PipelineRunning;