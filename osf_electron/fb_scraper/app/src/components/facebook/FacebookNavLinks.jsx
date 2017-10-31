import React, { Component } from 'react';
import NavLink from '../shared/NavLink.jsx'


class FacebookNavLinks extends Component {

    render() {
        return (
            <div className="navbar row">
                <div className="medium-12 columns navlinks">
                    <NavLink path='/fb/friends' title='Friends'/>
                    <NavLink path='/fb/posts' title='Posts'/>
                </div>
            </div>
        )
    }
}

export default FacebookNavLinks;