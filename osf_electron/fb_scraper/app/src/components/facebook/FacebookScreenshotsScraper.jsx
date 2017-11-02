import React, { Component } from 'react';
import PropTypes from 'prop-types';
import FbLogin from './FbLogin.jsx'
import Dropzone from 'react-dropzone'
import Log from '../Log.jsx'
const electron = window.require('electron');
const ipcRenderer  = electron.ipcRenderer;


class FacebookScreenshotsScraper extends Component {

    constructor(props) {
        super(props);
        this.state = {
            fbUsername: '',
            fbPassword: '',
            screenshotPosts: false,
            chronological: true,
        };
        this.handleClickGeneratePDF= this.handleClickGeneratePDF.bind(this);
        this.onDropFiles = this.onDropFiles.bind(this);
    }

    componentWillMount() {
        this.inputDatas = [];
        this.acceptedFiles = [];
    }

   onDropFiles(acceptedFiles, rejectedFiles) {
        this.props.log('++ drop Files');
        for (let i = 0; i < acceptedFiles.length; i++) {
            this.props.log(`++ ${i}`);
            const f = acceptedFiles[i];
            this.acceptedFiles.push(f.name);
            const reader = new FileReader();
            reader.onload = () => {
                const fileText = reader.result;
                // do whatever you want with the file content
                this.inputDatas.push(fileText);
            };
            reader.onabort = () => this.props.log('++ file reading was aborted');
            reader.onerror = () => this.props.log('++ file reading has failed');
            reader.readAsText(f);
        }
    }

    handleClickGeneratePDF() {
        this.props.setElectronState({
            pipelineRunning: true,
            pipelineStatus: 'running'
        });
        this.props.history.push('/pipeline-running');
        ipcRenderer.send('generate-pdf', {
            fbUsername: this.state.fbUsername,
            fbPassword: this.state.fbPassword,
            inputDatas: this.inputDatas,
            screenshotPosts: this.state.screenshotPosts,

            chronological: this.state.chronological,
        });
    };

    render() {

        return (
            <div className='fb-friends-scraper'>
                <div className="fadein">
                    <div className="row">
                        <div className="medium-12 columns">
                            <div className="select-posts">
                                <label>
                                    Select Post Files (created by osf)
                                </label>
                                <Dropzone
                                    multiple={true}
                                    className="file-picker"
                                    onDrop={this.onDropFiles}>
                                    Drop .json files here
                                </Dropzone>
                            </div>
                        </div>
                    </div>
                      <div className="row selected-files">
                            <div className="medium-12 columns">
                                {(this.acceptedFiles.length > 0) &&
                                    <label >
                                        Selected Files
                                    </label>
                                }
                                {this.acceptedFiles.map((fName) => {
                                    return (
                                        <div>
                                            {fName}
                                        </div>
                                    )
                                })}
                            </div>
                      </div>
                    <FbLogin
                        fbUsername={this.state.fbUsername}
                        fbPassword={this.state.fbPassword}
                        setFbUsername={(ev) => this.setState({fbUsername: ev.target.value})}
                        setFbPassword={(ev) => this.setState({fbPassword: ev.target.value})}
                    />
                    <div className="row advanced">
                        <div className="medium-12 columns">
                              <div className="friends-option">
                                  <input
                                    type="checkbox"
                                    className="which-pages-input"
                                    name="which-pages-input"
                                    checked={this.state.screenshotPosts}
                                    onChange={() => {
                                        if (this.state.screenshotPosts) {
                                            this.setState({screenshotPosts: false})
                                        } else {
                                            this.setState({screenshotPosts: true})
                                        }
                                    }}
                                  />
                                <label>Screenshot Posts</label>
                              </div>
                        </div>
                          <div className="medium-12 columns">
                              <div className="friends-option">
                                  <input
                                    type="checkbox"
                                    className="which-pages-input"
                                    name="which-pages-input"
                                    checked={this.state.chronological}
                                    onChange={() => {
                                        if (this.state.chronological) {
                                            this.setState({chronological: false})
                                        } else {
                                            this.setState({chronological: true})
                                        }
                                    }}
                                  />
                                <label>Chronological</label>
                              </div>
                    </div>
                    </div>

                     <div className="row">
                        <div className="medium-12 columns">
                            <button id="generate-button" onClick={this.handleClickGeneratePDF} className="button osf-button" type="submit">Generate PDF</button>
                        </div>
                    </div>
                    <Log logLines={this.props.logLines} electronState={this.props.electronState}/>
                </div>
            </div>
        );
    }
}

FacebookScreenshotsScraper.propTypes = {
    log: PropTypes.func
};

export default FacebookScreenshotsScraper;
