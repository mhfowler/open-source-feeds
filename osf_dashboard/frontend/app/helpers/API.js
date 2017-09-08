import { browserHistory } from 'react-router'
import Raven from 'raven-js'

function redirectToLogin() {
  window.localStorage.removeItem('cpi_session_token')
  browserHistory.push({
    pathname: '/login',
    state: {
      unauthorized: true
    }
  })
}

function get(endpoint, cb = data => data, onErr = Raven.captureException.bind(Raven)) {
  const sessionToken = window.localStorage.getItem('cpi_session_token')

  return fetch(endpoint, {
    headers: new window.Headers({
      Accept: 'application/json',
      'Content-Type': 'application/json',
      'X-ACCESS-TOKEN': sessionToken,
    }),
  })
  .then(resp => {
    if (resp.status === 401) {
      throw new Error('unauthorized')
    }
    return resp
  })
  .then(resp => resp.json())
  .then(cb)
  .catch(err => {
    if (err.message === 'unauthorized') {
      redirectToLogin()
      return
    }
    onErr(err)
  })
}

function post(endpoint, data = {}, cb = data => data, onErr = Raven.captureException.bind(Raven)) {
  const sessionToken = window.localStorage.getItem('cpi_session_token')

  return fetch(endpoint, {
    headers: new window.Headers({
      Accept: 'application/json',
      'Content-Type': 'application/json',
      'X-ACCESS-TOKEN': sessionToken,
    }),
    method: 'post',
    body: JSON.stringify(data),
  })
  .then(resp => {
    if (resp.status === 401) {
      throw new Error('unauthorized')
    }
    return resp
  })
  .then(resp => resp.json())
  .then(cb)
  .catch(err => {
    if (err.message === 'unauthorized') {
      redirectToLogin()
      return
    }
    onErr(err)
  })
}

export default {

  getCurrentUser: function(cb = response => response) {
    return get('/api/currentUser/').then(data => cb(data.currentUser))
  },

  newNote: function(params) {
    /* example query:
     * {
     *  action: 'Left a message',
     *  comments: 'this is the contents of the note',
     *  candidate_id: 1343242
     * }
     */
    return post('/api/note/', params).then(data => {
      return data
    })
  },

  searchCandidates: function(params) {
    return post('/api/search/candidates/', params).then(data => {
      return data.candidates
    })
  },

  getCommentActions: function(params) {
    return get('/api/comment-actions/', params).then(data => {
      return data.actions
    })
  },

  login: function(username, password, cb, onErr) {
    const data = {
      auth_type: 'email',
      email: username,
      password: password
    }
    return post('/api/auth/', data).then((data) => {
      if (data.success) {
        window.localStorage.setItem('cpi_session_token', data.token)
        return cb()
      }
      else {
        return onErr()
      }
    })
    .catch(onErr)
  },

}
