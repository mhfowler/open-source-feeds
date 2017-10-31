import React, { Component } from 'react';
import { Route } from 'react-router-dom'
import PropTypes from 'prop-types';
import DatePicker from 'react-datepicker'
import Loader from 'react-loader'
const electron = window.require('electron');
const ipcRenderer  = electron.ipcRenderer;


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

class FacebookPostsScraper extends Component {

    constructor(props) {
        super(props);
        this.state = {
            fbUsername: '',
            fbPassword: '',
            afterDate: null,
            beforeDate: null,
            showAdvanced: false,
            whichPagesSetting: 'all',
        };
        this.handleClickFetchPosts = this.handleClickFetchPosts.bind(this);
        this.getPostsScraper = this.getPostsScraper.bind(this);
    }

    componentWillMount() {
        this.selectedFriends = new Set();
    };

    componentDidMount() {
      ipcRenderer.send('get-fb-friends', {});
    };

    handleClickFetchPosts() {
        this.props.setElectronState({
            pipelineRunning: true,
            pipelineStatus: 'running'
        });
        this.props.history.push('/pipeline-running');
        let selectedFriends = Array.from(this.selectedFriends);
        ipcRenderer.send('fetch-posts', {
            fbUsername: this.state.fbUsername,
            fbPassword: this.state.fbPassword,
            afterDate: this.state.afterDate,
            beforeDate: this.state.beforeDate,
            whichPagesSetting: this.state.whichPagesSetting,
            selectedFriends: selectedFriends
        });
    };

    getPostsScraper(numFriends, numPagesToScrape) {
        return (
          <div className="fadein">
            <div className="row">
                <div className="medium-12 columns">
                    <div className="select-dates">
                        <label>
                            After Date
                        </label>
                        <DatePicker
                            className="date-picker"
                            selected={this.state.afterDate}
                            onChange={(val) => { this.setState({afterDate: val}) }}
                        />
                    </div>
                </div>
            </div>
            <div className="row">
                <div className="medium-12 columns">
                    <div className="select-dates">
                        <label>
                            Before Date (empty is the same as today)
                        </label>
                        <DatePicker
                            className="date-picker"
                            selected={this.state.beforeDate}
                            onChange={(val) => { this.setState({beforeDate: val}) }}
                        />
                    </div>
                </div>
            </div>
            <FbLogin
                fbUsername={this.state.fbUsername}
                fbPassword={this.state.fbPassword}
                setFbUsername={(ev) => this.setState({fbUsername: ev.target.value})}
                setFbPassword={(ev) => this.setState({fbPassword: ev.target.value})}
            />
            <div className="row">
                <div className="medium-12 columns">
                    <button id="generate-button" onClick={this.handleClickFetchPosts} className="button osf-button" type="submit">Fetch Posts</button>
                </div>
            </div>
            <div className="row select-friends">
                <div className="medium-12 columns">
                    <div>
                        This will search for posts from {numPagesToScrape} pages.
                    </div>
                </div>
            </div>
              {!this.state.showAdvanced &&
              <div className="row advanced">
                  <div className="medium-12 columns">
                      <button onClick={() => {
                          this.setState({showAdvanced: true})
                      }}>
                          Click Here To Show More Settings
                      </button>
                  </div>
              </div>
              }
              {this.state.showAdvanced &&
                <div>
                    <div className="row advanced">
                        <strong className="medium-12 columns">
                            Which Pages To Scrape
                        </strong>
                    </div>
                    <div className="row advanced">
                        <div className="medium-12 columns">
                              <div className="friends-option">
                                  <input
                                    type="radio"
                                    className="which-pages-input"
                                    name="which-pages-input"
                                    checked={this.state.whichPagesSetting === 'all'}
                                    onChange={() => this.setState({whichPagesSetting: 'all'})}
                                  />
                                <label>All Friends</label>
                              </div>
                             <div className="friends-option">
                                <input
                                    type="radio"
                                    className="which-pages-input"
                                    name="which-pages-input"
                                    checked={this.state.whichPagesSetting === 'manual'}
                                    onChange={() => this.setState({whichPagesSetting: 'manual'})}
                                  />
                                <label>Manually Select</label>
                              </div>
                        </div>
                    </div>
                    {this.state.whichPagesSetting === 'manual' &&
                    <div className="row">
                        <strong className="medium-12 columns manual-select">
                            Manually Select Friends
                        </strong>
                        <div className="medium-12 columns friends-list">
                            {this.props.electronState.fbFriendsRequest.friends.map((friend) => {
                                return (
                                    <div className="select-friend">
                                        <input
                                            type="checkbox"
                                            onChange={() => {
                                                const selectedFriends = this.selectedFriends;
                                                if (selectedFriends.has(friend)) {
                                                    selectedFriends.delete(friend);
                                                } else {
                                                    selectedFriends.add(friend);
                                                }
                                            }}
                                        />
                                        <label>{friend}</label>
                                    </div>
                                )
                            })

                            }
                        </div>
                    </div>
                    }
                </div>
              }
        </div>
        )
    };

    render() {

        let numFriends = 0;
        let isLoaded = false;
        if (this.props.electronState && this.props.electronState.fbFriendsRequest && this.props.electronState.fbFriendsRequest.loaded) {
            numFriends = this.props.electronState.fbFriendsRequest.friends.length;
            isLoaded = true;
        }
        let numPagesToScrape = 0;
        if (this.state.whichPagesSetting === 'all') {
            numPagesToScrape = numFriends;
        }
        else {
            numPagesToScrape = this.selectedFriends.size;
        }

        return (
            <div className="fb-posts-scraper">
                <Loader loaded={isLoaded}>
                    {numFriends === 0
                        ?   <div className="row">
                                <div className="medium-12 columns">
                                    You must load friends before loading posts.
                                </div>
                            </div>
                        : this.getPostsScraper(numFriends, numPagesToScrape)
                    }
                </Loader>
            </div>
        );
    }
}


class FacebookScraper extends Component {

    constructor(props) {
        super(props);
        this.state = {
            fbUsername: '',
            fbPassword: ''
        };
    }

    componentDidMount() {
        console.log(this.props)
    };

    render() {
        return (
            <div className="facebook-scraper">
                <Route path="/fb/friends" exact render={(routerProps) => (<FacebookFriendsScraper handleClickFetchFriends={this.handleClickFetchFriends} {...this.props} {...routerProps} />)}/>
                <Route path="/fb/posts" exact render={(routerProps) => (<FacebookPostsScraper handleClickFetchPosts={this.handleClickFetchPosts} {...this.props} {...routerProps} />)}/>
            </div>
        );
    }
}

FacebookScraper.propTypes = {
    log: PropTypes.func
};

export default FacebookScraper;
