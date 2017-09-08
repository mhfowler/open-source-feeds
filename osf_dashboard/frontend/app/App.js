import React, { Component } from 'react'
import { Router, Route, Link, IndexRoute, browserHistory } from 'react-router'
import Loader from 'react-loader'
import NotificationSystem from 'react-notification-system'
import classNames from 'classnames'
import { Home } from './Home'
import { NewNote } from './NewNote'
import RequireAuthenticationContainer from './RequireAuthenticationContainer'
import Login from './Login'
import API from './helpers/API'


class Container extends Component {
  constructor(props) {
    super(props)
    this.state = {
      currentUser: null,
      loaded: false,
    }
    this.refreshReps = this.refreshReps.bind(this)
  }

  static get contextTypes() {
    return { notify: React.PropTypes.func.isRequired }
  }

  componentWillMount() {
    this.fetchCurrentUser()
  }

  fetchCurrentUser = () => {
    return API.getCurrentUser().then(data => {
      this.setState({ currentUser: data, loaded: true })
    })
  }

  logout() {
    window.localStorage.removeItem('cpi_session_token')
    browserHistory.push('/login')
  }

  refreshReps(e) {
    e.preventDefault()
    API.updateReps(() => {
      this.context.notify({
        message: `Representative and Committee data refreshed.`,
        level: 'success'
      })
    })
  }

  render() {
    const isNotLogin = this.props.location.pathname !== '/login'
    const logoutButton = isNotLogin ? <a onClick={this.logout} href=""><button>Sign Out</button></a> : null
    const loggedInAs = isNotLogin && this.state.currentUser ? <a className="logged-in-as">Logged in as {this.state.currentUser.email}</a> : null

    return (
      <Loader loaded={this.state.loaded}>
        <div className="body-container">
          { isNotLogin
          ?<header className="main-header">
            <div className="main-header-logo">
              <Link to="/" className="home-link">home</Link>
            </div>
            <div className="main-header-nav">
              {loggedInAs}
              {logoutButton}
            </div>
          </header>
            : null
          }
          <div className="body-wrapper">
            {React.cloneElement(this.props.children, { fetchCurrentUser: this.fetchCurrentUser })}
          </div>
        </div>
      </Loader>
    )
  }
}

const NotFound = () => <h1>404.. This page is not found!</h1>

class App extends Component {
  static get childContextTypes() {
    return { notify: React.PropTypes.func }
  }

  getChildContext() {
    return {
      notify: this.notify.bind(this),
    }
  }

  notify(notification) {
    this.notifications.addNotification(notification)
  }

  render() {
    return (
      <main>
        <NotificationSystem ref={notifications => { this.notifications = notifications }} style={false} />
        <Router history={browserHistory}>
          <Route path="/" component={Container}>
            <Route path="login" component={Login} />
            <Route component={RequireAuthenticationContainer}>
              <IndexRoute component={Home} />
              <Route path="new" component={NewNote} />
            </Route>
          </Route>
          <Route path="*" component={NotFound} />
        </Router>
      </main>
    )
  }
}

export default App
