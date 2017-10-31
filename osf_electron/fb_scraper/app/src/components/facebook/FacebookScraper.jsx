import React, { Component } from 'react';
import { Route } from 'react-router-dom'
import PropTypes from 'prop-types';
import FacebookFriendsScraper from './FacebookFriendsScraper.jsx'
import FacebookPostsScraper from './FacebookPostsScraper.jsx'
import FacebookScreenshotsScraper from './FacebookScreenshotsScraper.jsx'


class FacebookScraper extends Component {

    constructor(props) {
        super(props);
        this.state = {
            fbUsername: '',
            fbPassword: ''
        };
    }

    render() {
        return (
            <div className="facebook-scraper">
                <Route path="/fb/friends" exact render={(routerProps) => (<FacebookFriendsScraper {...this.props} {...routerProps} />)}/>
                <Route path="/fb/posts" exact render={(routerProps) => (<FacebookPostsScraper {...this.props} {...routerProps} />)}/>
                <Route path="/fb/screenshots" exact render={(routerProps) => (<FacebookScreenshotsScraper {...this.props} {...routerProps} />)}/>
            </div>
        );
    }
}

FacebookScraper.propTypes = {
    log: PropTypes.func
};

export default FacebookScraper;
