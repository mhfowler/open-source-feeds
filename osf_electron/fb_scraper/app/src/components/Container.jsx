import React, { Component } from 'react';
import { Route, withRouter } from 'react-router-dom'
import FacebookScraper from './facebook/FacebookScraper.jsx'
import FacebookNavLinks from './facebook/FacebookNavLinks.jsx'
import Settings from './Settings.jsx'
import Initializing from './Initializing.jsx'
import Home from './Home.jsx'
import PipelineRunning from './PipelineRunning.jsx'
import PipelineFinished from './PipelineFinished.jsx'
import NotImplemented from './NotImplemented.jsx'
import PipelineStopped from './PipelineStopped.jsx'
import NavLink from './shared/NavLink.jsx'
import 'react-datepicker/dist/react-datepicker.css'

const electron = window.require('electron');
const ipcRenderer  = electron.ipcRenderer;


class Container extends Component {

    constructor(props) {
        super(props);
        this.state =  {
            log: [],
            electronState: {},
            showNav: true,
        };

        this.log = this.log.bind(this);
        this.setElectronState = this.setElectronState.bind(this);
    }

  static get contextTypes() {
    return {
        notify: React.PropTypes.func.isRequired,
        router: React.PropTypes.object,
    }
  }

    log(msg) {
        let logLines = this.state.log;
        logLines.unshift(msg);
        if (logLines.length > 10) {
            logLines = logLines.splice(0, 10)
        }
        this.setState({
            log: logLines
        });
    };

    setElectronState(newState) {
        let electronState = this.state.electronState;
        const newElectronState = Object.assign(electronState, newState);
        this.setState({
            electronState: newElectronState
        }, () => ipcRenderer.send('react-set-electron-state', newState));
    };

    componentDidUpdate(prevProps, prevState) {
        const pathName = this.props.location.pathname;
        if (pathName !== '/pipeline-running') {
            if (this.state.electronState.pipelineStatus === 'running') {
                this.context.router.history.push('/pipeline-running');
            }
        }
        if (pathName === '/pipeline-running') {
            if (this.state.electronState.pipelineStatus === 'finished') {
                this.context.router.history.push('/pipeline-finished');
            } else if (this.state.electronState.pipelineStatus === 'stopped') {
                this.context.router.history.push('/pipeline-stopped');
            }
        } else if (pathName === '/') {
            if (this.state.electronState.isOsfRunning) {
                this.context.router.history.push('/home');
            }
        }
    };

    componentDidMount() {
        this.log('++ component did mount');
        ipcRenderer.send('test-event', {});
        this.setElectronState({
            reactIsLoaded: true,
        });

        ipcRenderer.on('print-message', (event, data) => {
            this.log(data);
        });

        ipcRenderer.on('redirect', (event, data) => {
            this.context.router.history.push(data.path);
        });

        ipcRenderer.on('set-electron-state', (event, data) => {
            this.setState({
                electronState: data
            })
        });
    };

    handleClickNavToggle() {
        if (this.state.showNav) {
            this.setState({showNav: false});
        } else {
            this.setState({showNav: true});
        }
    };

  render() {

    const childrenProps = {
        log: this.log,
        logLines: this.state.log,
        electronState: this.state.electronState,
        setElectronState: this.setElectronState
    };

    const pathName = this.props.location.pathname;
    let showNav = false;
    if (!this.state.electronState.pipelineRunning && pathName !== '/') {
        showNav = true;
    }

    return (
        <div className="body-container">

          <header className="main-header">
          </header>
            <div className="navtoggle row">
                <div className="medium-12 columns">
                    <div className="navtoggle" onClick={this.handleClickNavToggle}>
                </div>
            </div>

            </div>
            {showNav &&
            <div className="navbar">
                <div className="row">
                    <div className="medium-12 columns navlinks">
                        <NavLink path='/fb' title='Facebook'/>
                        <NavLink path='/instagram' title='Instagram'/>
                        <NavLink path='/settings' title='Settings'/>
                    </div>
                </div>
                <Route path="/fb" render={(props) => (<FacebookNavLinks {...childrenProps} {...props} />)}/>
            </div>
            }
          <div className="body-wrapper">
              <Route path="/" exact render={(props) => (<Initializing {...childrenProps} {...props} />)}/>
              <Route path="/home" exact render={(props) => (<Home {...childrenProps} {...props} />)}/>
              <Route path="/fb" render={(props) => (<FacebookScraper {...childrenProps} {...props} />)}/>
              <Route path="/instagram" render={(props) => (<NotImplemented/>)}/>
              <Route path="/settings" exact render={(props) => (<Settings {...childrenProps} {...props} />)}/>
              <Route path="/pipeline-running" exact render={(props) => (<PipelineRunning {...childrenProps} {...props} />)}/>
              <Route path="/pipeline-stopped" exact render={(props) => (<PipelineStopped {...childrenProps} {...props} />)}/>
              <Route path="/pipeline-finished" exact render={(props) => (<PipelineFinished {...childrenProps} {...props} />)}/>
          </div>
        </div>
    )
  }
}

const RouterContainer = withRouter(props => <Container {...props}/>);

export default RouterContainer;