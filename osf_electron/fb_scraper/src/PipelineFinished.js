import React, { Component } from 'react';


class PipelineFinished extends Component {

    render = () => {
        return (
            <div className="pipeline-finished">
                 <div className="row">
                       <div className="medium-12 columns">
                           <p>
                                pipeline finished: {this.props.electronState.pipelineName}
                           </p>
                           <p>
                               Your data is stored in {this.props.electronState.pipelineMessage}
                           </p>
                       </div>
                </div>
            </div>
        )
    }
}

export default PipelineFinished;