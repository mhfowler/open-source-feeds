import React, { Component } from 'react'
import { Link } from 'react-router'


class Home extends Component {
  constructor(props) {
    super(props)
    this.state = {
      notes: []
    }
  }

  componentWillMount() {
  }

  render() {

    return (
      <div className="table">
        <div className="table-header">
          <h1>Notes</h1>
          <div className="table-header-buttons">
            <Link className="button" to="/new">New Note</Link>
          </div>
        </div>
        <table>
          <tbody>
            <tr>
              <th>#</th>
              <th>Title</th>
              <th>Description</th>
              <th>Date Created</th>
            </tr>
          </tbody>
        </table>
      </div>
    )
  }
}

export {
  Home
}
