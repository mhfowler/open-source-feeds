import React, { Component } from 'react'
import API from './helpers/API'
// import Select from 'react-select'
import Autosuggest from 'react-autosuggest';


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
      action: '',
      suggestions: [],
      candidateOptions: [],
    })
  }

  // searchCandidates() {
  //   return API.searchCandidates({query: this.state.name}).then(data => {
  //     const candidateOptions = data.map(c => ({ value: c.entityId, label: c.title }))
  //     this.setState({ candidateOptions: candidateOptions})
  //   })
  // }

  onSubmit(ev) {
    ev.preventDefault()
    API.newNote(this.state, note => {
      this.context.notify({
        message: `Note created`,
        level: 'success',
        autoDismiss: 1,
        onRemove: () => {
          this.props.router.push(`/${note.id}`)
        }
      })
    })
  }

  onInputChange(key, ev) {
    var update = {}
    update[key] = ev.target.value
    this.setState(update)
  }

  // Teach Autosuggest how to calculate suggestions for any given input value.
  getSuggestions = async (value) => {
    const candidates = await API.searchCandidates({query: value})
    return candidates
  }

  // When suggestion is clicked, Autosuggest needs to populate the input element
  // based on the clicked suggestion. Teach Autosuggest how to calculate the
  // input value for every given suggestion.
  getSuggestionValue = (suggestion) => suggestion.title

  // Use your imagination to render suggestions.
  renderSuggestion = (suggestion) => (
    <div>
      {suggestion.title}
    </div>
  )

  // Autosuggest will call this function every time you need to update suggestions.
  // You already implemented this logic above, so just use it.
  onSuggestionsFetchRequested = ({ value }) => {
    this.setState({
      suggestions: this.getSuggestions(value)
    });
  };

  // Autosuggest will call this function every time you need to clear suggestions.
  onSuggestionsClearRequested = () => {
    this.setState({
      suggestions: []
    });
  };

  render() {

    // Autosuggest will pass through all these props to the input element.
    const inputProps = {
      placeholder: 'Type a candidate name',
      value: this.state.name,
      onChange: this.onInputChange.bind(this, 'name')
    }

    return <div className="main-wrapper">
      <form onSubmit={this.onSubmit}>
        <Autosuggest
          suggestions={this.state.suggestions}
          onSuggestionsFetchRequested={this.onSuggestionsFetchRequested}
          onSuggestionsClearRequested={this.onSuggestionsClearRequested}
          getSuggestionValue={this.getSuggestionValue}
          renderSuggestion={this.renderSuggestion}
          inputProps={inputProps}
        />
        <fieldset>
          <label>Note</label>
          <textarea
            value={this.state.note}
            onChange={this.onInputChange.bind(this, 'note')}
          />
        </fieldset>
        <fieldset>
          <label>Action</label>
          <input
            type="text"
            value={this.state.action}
            onChange={this.onInputChange.bind(this, 'action')} />
        </fieldset>
        <input type="submit" value="Save" />
      </form>
    </div>
  }
}

export {
  NewNote
}
