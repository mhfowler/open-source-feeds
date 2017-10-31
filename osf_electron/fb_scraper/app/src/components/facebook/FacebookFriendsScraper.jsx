import React, { Component } from 'react';
import Loader from 'react-loader';
import FbLogin from './FbLogin.jsx';
const electron = window.require('electron');
const ipcRenderer  = electron.ipcRenderer;


class FacebookFriendsScraper extends Component {

    constructor(props) {
        super(props);
        this.state = {
            fbUsername: '',
            fbPassword: ''
        };
        this.handleClickFetchFriends = this.handleClickFetchFriends.bind(this);
    }

    componentDidMount() {
      ipcRenderer.send('get-fb-friends', {});
    };

    handleClickFetchFriends() {
        this.props.setElectronState({
            pipelineRunning: true,
            pipelineStatus: 'running'
        });
        this.props.history.push('/pipeline-running');
        ipcRenderer.send('fetch-friends', {fbUsername: this.state.fbUsername, fbPassword: this.state.fbPassword});
    };

    render() {

        let numFriends = 0;
        let isLoaded = false;
        if (this.props.electronState && this.props.electronState.fbFriendsRequest && this.props.electronState.fbFriendsRequest.loaded) {
            numFriends = this.props.electronState.fbFriendsRequest.friends.length;
            isLoaded = true;
        }

        return (
            <div className='fb-friends-scraper'>
                <Loader loaded={isLoaded}>
                    <div className="fadein">
                        <FbLogin
                            fbUsername={this.state.fbUsername}
                            fbPassword={this.state.fbPassword}
                            setFbUsername={(ev) => this.setState({fbUsername: ev.target.value})}
                            setFbPassword={(ev) => this.setState({fbPassword: ev.target.value})}
                        />
                         <div className="row">
                            <div className="medium-12 columns">
                                <button id="generate-button" onClick={this.handleClickFetchFriends} className="button osf-button" type="submit">Fetch Friends</button>
                            </div>
                        </div>
                        {numFriends !== 0 && <div className="loaded-friends row">
                            <div className="medium-12 columns">
                                {numFriends} friends are currently saved in ~/Desktop/osf/data/friends/current.json
                            </div>
                        </div>}
                    </div>
                </Loader>
            </div>
        );
    }
}

export default FacebookFriendsScraper;
