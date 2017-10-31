import React, {Component} from 'react'
import {} from './styles/global.css'
import {} from './styles/foundation.css'
import {} from './styles/styles.css'
import {} from './styles/App.css'
import { HashRouter } from 'react-router-dom'
import NotificationSystem from 'react-notification-system'
import Container from './components/Container.jsx'


const logos = [
    require('./assets/electron.png'),
    require('./assets/react.png'),
    require('./assets/webpack.png')
];


class RouterApp extends Component {
    static get childContextTypes() {
        return {
            notify: React.PropTypes.func
        }

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
                <HashRouter>
                    <Container/>
                </HashRouter>
            </main>
        );
    }
}


export default RouterApp;
