import React, { Component } from 'react'
import API from './helpers/API'
import Loader from 'react-loader'
import Select from 'react-select'

// this variable is used to allow for an event to occur X ms after the user finishes typing
var searchTimer
var searchTimerTimeout = 1000

class NewNote extends Component {
  constructor(props) {
    super(props)

    this.onSubmit = this.onSubmit.bind(this)
  }
  static get contextTypes() {
    return { notify: React.PropTypes.func.isRequired }
  }

  componentWillMount() {
    this.setState({
      name: '',
      note: '',
      candidateOptions: [],
      selectedAction: [],
      selectedNames: [],
      actions: [],
      candidateId: null,
      loaded: false,
      noResults: true,
    })
  }

  componentDidMount() {
    this.getCommentActions()
  }

  getCommentActions = () => {
    API.getCommentActions().then(actions => {
      this.setState({
        loaded: true,
        actions: actions
      })
    })
  }

  searchCandidates = (input) => {
    if (input) {
      console.log(`++ searching for: ${input}`)
      return API.searchCandidates({query: input}).then(data => {
        const candidateOptions = data.map(c => ({value: c.entityId, label: c.title}))
        if (!candidateOptions) {
          this.setState({noResults: true})
        } {
          this.setState({noResults: false})
        }
        return {
          options: candidateOptions,
          complete: false
        }
      })
    }
    else {
      return {
        options: []
      }
    }
  }

  onSubmit = (ev) => {
    ev.preventDefault()
    const noteArgs = {
      comments: this.state.note,
      action: this.state.selectedAction,
      candidateId: this.state.selectedNames
    }
    API.newNote(noteArgs).then((response) => {
      if (response.success) {
        this.context.notify({
          message: `Note created`,
          level: 'success',
          autoDismiss: 1,
          onRemove: () => {
            this.setState({
              note: '',
              selectedAction: [],
              selectedNames: []
            })
          }
        })
      }
      else {
        this.context.notify({
          message: `Failed to create note`,
          level: 'error',
          autoDismiss: 1,
          onRemove: () => {
            this.props.router.push(`/${note.id}`)
          }
        })
      }
    })
  }

  onInputChange= (key, ev) => {
    var update = {}
    update[key] = ev.target.value
    this.setState(update)
  }

  onSearchInputChange = (inputVal) => {
    clearTimeout(searchTimer)
    var self = this
    searchTimer = setTimeout(function() {
      self.searchCandidates(inputVal).then((candidates) => {
        console.log('++ updating candidate options')
        self.setState({
          candidateOptions: candidates.options
        })
      })
    }, searchTimerTimeout)
  }

  onNameChange = (val) => {
    let selectedNames= this.state.selectedNames
    if (Array.isArray(val)) {
      selectedNames = val.map(v => v.value)
    } else {
      selectedNames = val.value
    }
    this.setState({
      selectedNames: selectedNames
    })
  }

  onActionChange = (val) => {
    let selectedAction = this.state.selectedAction
    if (Array.isArray(val)) {
      selectedAction = val.map(v => v.value)
    } else {
      selectedAction = val.value
    }
    this.setState({
      selectedAction: selectedAction
    })
  }

  getNameOptions = (input) => {
    clearTimeout(searchTimer)
    var self = this
    var promise = new Promise(function(resolve, reject) {
       searchTimer = setTimeout(function() {
          resolve(self.searchCandidates(input))
       }, searchTimerTimeout)
     })
    return promise
  }

  render = () => {

    const actionOptions = this.state.actions.map(c => ({ value: c, label: c }))
    const candidateOptions = this.state.candidateOptions

    return (
      <Loader loaded={this.state.loaded}>
        <div className="main-wrapper">
          <form onSubmit={this.onSubmit}>
            <fieldset>
              <label>Name</label>
              <Select.Async
                name="name"
                placeholder={'Search Name'}
                value={this.state.selectedNames}
                onChange={this.onNameChange}
                autoload={false}
                loadOptions={this.getNameOptions}
                clearable={false}
                openOnFocus={true}
                noResultsText="No Results Found"
              />
            </fieldset>
            <fieldset>
              <label>Note</label>
              <textarea
                value={this.state.note}
                onChange={this.onInputChange.bind(this, 'note')}
              />
            </fieldset>
            <fieldset>
              <label>Action</label>
              <Select
                name="action"
                placeholder="Action"
                value={this.state.selectedAction}
                onChange={this.onActionChange}
                options={actionOptions}
                clearable={false}
              />
            </fieldset>
            <input type="submit" value="Save" />
          </form>
        </div>
      </Loader>
    )
  }
}

export {
  NewNote
}
