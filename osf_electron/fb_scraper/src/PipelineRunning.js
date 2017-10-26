import React, { Component } from 'react';
import Log from './Log'
const electron = window.require('electron');
const ipcRenderer  = electron.ipcRenderer;


class PipelineRunning extends Component {

    handleClickStopPipeline = () => {
        ipcRenderer.send('stop-pipeline', {});
    };

    render = () => {
        return (
            <div className="pipeline-running">
               <div className="row">
                   <div className="medium-12 columns">
                        pipeline running: {this.props.electronState.pipelineName}
                   </div>
                    <div className="medium-12 columns">
                        {JSON.stringify(this.props.electronState.pipelineParams)}
                   </div>
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