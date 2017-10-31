import React, { Component } from 'react';


class PipelineStopped extends Component {


    render() {
        return (
            <div className="pipeline-running">
               <div className="row">
                   <div className="medium-12 columns">
                        Your pipeline was successfully stopped.
                   </div>
                </div>
            </div>
        )
    }
}

export default PipelineStopped;