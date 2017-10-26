import React, { Component } from 'react';
import { Route } from 'react-router-dom'
import PropTypes from 'prop-types';
import DatePicker from 'react-datepicker'
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

    state = {
        fbUsername: '',
        fbPassword: ''
    };

    handleClickFetchFriends = () => {
        ipcRenderer.send('fetch-friends', {fbUsername: this.state.fbUsername, fbPassword: this.state.fbPassword});
    };

    render = () => {
        return (
            <div className='fb-friends-scraper'>
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
            </div>
        );
    }
}

class FacebookPostsScraper extends Component {

    state = {
        fbUsername: '',
        fbPassword: '',
        afterDate: null,
        beforeDate: null,
    };

    handleClickFetchPosts = () => {
        ipcRenderer.send('fetch-posts', {
            fbUsername: this.state.fbUsername,
            fbPassword: this.state.fbPassword,
            afterDate: this.state.afterDate,
            beforeDate: this.state.beforeDate
        });
    };

    render = () => {
        return (
            <div className="fb-posts-scraper">
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
                <div className="row">
                    <div className="medium-2 columns">
                        {/*<div className="select-friends">*/}
                            {/*select friends*/}
                        {/*</div>*/}
                    </div>
                </div>
            </div>
        );
    }
}


class FacebookScraper extends Component {

    state = {
        fbUsername: '',
        fbPassword: ''
    };

    componentDidMount = () => {
        console.log(this.props)
    };

    render = () => {
        return (
            <div className="facebook-scraper">
                <Route path="/fb/friends" exact render={(props) => (<FacebookFriendsScraper handleClickFetchFriends={this.handleClickFetchFriends} {...props} />)}/>
                <Route path="/fb/posts" exact render={(props) => (<FacebookPostsScraper handleClickFetchPosts={this.handleClickFetchPosts} {...props} />)}/>
            </div>
        );
    }
}

FacebookScraper.propTypes = {
    log: PropTypes.func
};

export default FacebookScraper;
