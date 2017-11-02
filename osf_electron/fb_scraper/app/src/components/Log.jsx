import React from 'react';
import { withRouter } from 'react-router-dom';

const BaseLog = (props) => {
    return (
        <div className="row">
            <div className="medium-12 columns">
                <div className="log">
                    {/*<div>*/}
                        {/*{props.location.pathname}*/}
                    {/*</div>*/}
                    {/*<div>*/}
                        {/*{JSON.stringify(props.electronState)}*/}
                    {/*</div>*/}
                    {props.logLines.map((line) => {
                        return (
                            <div>{line}</div>
                        )
                    })}
                </div>
            </div>
        </div>
    );
};

const Log = withRouter(props => <BaseLog {...props}/>);


export default Log;
