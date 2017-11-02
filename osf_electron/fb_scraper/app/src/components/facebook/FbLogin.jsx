import React from 'react';


const FbLogin = (props) => {
    return (
        <div className="row">
            <div className="medium-12 columns">
                <label>
                    FB Username
                    <span className="input-group">
                    <input
                        value={props.fbUsername}
                        onChange={props.setFbUsername}
                        className="input-group-field" type="text" name="fb-username" placeholder="username@gmail.com"/>
                </span>
                </label>
                <label>
                    FB Password
                    <span className="input-group">
                    <input
                        value={props.fbPassword}
                        onChange={props.setFbPassword}
                        className="input-group-field" type="password" name="fb-password" placeholder="password"/>
                </span>
                </label>
            </div>
        </div>
    )
};



export default FbLogin;
