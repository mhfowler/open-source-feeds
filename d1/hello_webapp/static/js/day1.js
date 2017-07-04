


$(document).ready(function() {

  $('.login').click(function(e) {
    console.log('++ logging in');
    e.preventDefault();
    FB.login(function(response){
      console.log('++ logged in');
      console.log(response);
      console.log(response.authResponse.accessToken);
      // Handle the response object, like in statusChangeCallback() in our demo
      // code.
    }, {scope: 'user_posts,user_friends'});
  })

});

