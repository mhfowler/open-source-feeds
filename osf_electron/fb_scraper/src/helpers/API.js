var fetch = require('electron-fetch');

export default {

  isOSFUp: function() {
    return fetch('http://localhost:80/api/is_up/', {
        method: 'GET'
    });
  },

}
