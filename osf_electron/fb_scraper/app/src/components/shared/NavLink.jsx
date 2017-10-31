import React  from 'react';
import classNames from 'classnames'
import { withRouter } from 'react-router-dom'

const NavLink = (props) => {
    return (
        <div className={classNames({ 'navlink': true, 'selected': props.location.pathname.startsWith(props.path) })} onClick={() => {props.history.push(props.path)}}>{props.title}</div>
    )
};

const RouterNavLink = withRouter(props => <NavLink {...props}/>);

export default RouterNavLink;
