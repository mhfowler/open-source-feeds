import React, { Component } from 'react';
import DatePicker from 'react-datepicker'
import Loader from 'react-loader'
import FbLogin from './FbLogin.jsx';
const electron = window.require('electron');
const ipcRenderer  = electron.ipcRenderer;


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
            downloadImages: false,
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
            selectedFriends: selectedFriends,
            downloadImages:  this.state.downloadImages,
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
                      <div className="friends-option">
                          <input
                            type="checkbox"
                            className="download-images-input"
                            name="download-images-input"
                            checked={this.state.downloadImages}
                            onChange={() => {
                                if (this.state.downloadImages) {
                                    this.setState({downloadImages: false})
                                } else {
                                    this.setState({downloadImages: true})
                                }
                            }}
                          />
                        <label>Download Images</label>
                      </div>
                </div>
              </div>
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

export default FacebookPostsScraper;