## OSF Design Spec

An open source codebase for a server which lets you create and configure feeds which update on a regular
basis on a remote server and can be viewed through the internet. 

There will be two main ways this is used:
- a canonical server running in AWS which users
can simply sign up for through the web. 
- utilities to easily deploy your own server on Ubuntu or Raspberry pi

### Feature Summary

- login, create an account
- integrate different accounts (input modules)
  - twitter, are.na, facbook, instagram
- osf-server hourly ingests/scrapes all posts by accounts you follow
- user can create a new feed
  - using installed osf modules configure feeds
    - each feed module takes in source posts and returns a list of posts
    - one of the modules is osf-meta-module which lets you specify other modules as input and compose them 
  - feed modules also let you specify render module
- you can view feeds (also direct links to feeds which hide all OSF controls and just show the feed)
- you can edit and delete feeds
- admins can install and uninstall modules for their osf-server (input, feed and render)


### OSF Modules

A module system will be built into OSF to allow for extensibility by the community.

The three types of modules are 
- Input Modules
   - e.g. twitter, are.na, facebook, instagram
   - adds posts to source posts (which can be consumed by any feed module)
- Feed Modules
   - takes in source posts and returns feed posts
   - certain feed modules require certain input modules, and also specify which types of posts they can consume (they will ignore posts that they can't handle)
- Render Modules
   - takes in a list of posts and renders them to HTML (different render modules can expect certain types of posts and ignore others)
   
![img](https://i.imgur.com/DemBPxh.jpg)
   
### OSF Design Goals

- The success or failure of any input module does not effect the running of any other input module
- The success or failure of any feed module does not effect the running of any other feed  module
- admins can easily install and uninstall modules
- renderer can render to full page (total control of presentation)


### Post Types

- Input Modules create lists of posts
- Feed Modules create lists of posts
- Render Modules take posts and render HTML

In a list of posts, each post has a type
- input modules say what types of posts they produce 
- feed modules say what types of posts they can accept
- render modules say what types of posts they can accept


### Deployment

OSF v2 is designed to run on Ubuntu (in the cloud)
or on Raspberry Pi for a self-hosted server. 

I will self-host a canonical cloud version 
which only has integrations installed 
which authenticate through oAuth
(such as twitter). If you want to run a server 
which uses a scraper as a source, you
can host your own server on raspberry pi 
and install the Facebook module. 


Raspberry Pi Image
- flag to self-update (OSF & modules)
- can update WIFI credentials on sim card
- if disconnected from internet for > 1 hour, reboot
- feeds viewable through public internet after login using ngrok

Ansible recipe to deploy to Ubuntu 16
- optionally this deployment is a single machine or fleet of machines (web servers and workers)


### Users "Create Feed" and "Add Input"

Users don't need to worry about the implementation of feeds
or about installing and uninstalling modules (only admins self-hosting
OSF servers need to know about this).

Users only use OSF to do two things
- Create a feed
- Add an input

When they create a feed, the list of options of feed types 
they are given is based on what feed modules are installed on that server. 

Similarly, when they add an input, the list of available inputs,
is based on what input modules are installed on that server 
(for the canonical version it will just be input modules which use OAuth, 
such as twitter and are.na).

A feed module can include an interface for how to 
tune that particular feed using sliders and knobs,
or it can hardcode constants. A feed module can even
be an instantiation of a different customizable 
feed module with a particular parameterization of variables
(e.g. someone could make a general twitter feed module,
which gets used by another feed module which is more specific).

 

### Weird Feed Ideas

- Random Twitter Scraper
  - chooses accounts randomly and scrapes them, different everytime
- Random Image Scraper
  - chooses images randomly from Imgur, kind of like reading tea leaves
- Random Instagram Explorer 
  - based on certain parameters, randomly explores instagram
- Internet Collage 7.1 Feed
  - requires Random Image Scraper as input
  - combines images into a weird collage that fills the entire page 
  
  
### Liking, Sharing, Retweeting (Input Module Actions)

Input modules can also supply actions which can be used by renderers.

e.g. Twitter  input modules provides
- like action
- retweet action
- reply action

These actions can be embedded into the UI wherever the renderer wants.

Render Modules can required Input Modules, or change
how it renders the page based on what Input Modules are available
(e.g. if you don't have a twitter integration, don't show re-tweet action on posts). 




### Questions

- how to handle installing and running OSF modules?
  - osf install module-name (which in backend does something similar to pip installing a python package into a osf-modules folder,
  or using some other python plugin manager such as yaspy)
    - for each installed module, call certain functions 
    of that module at the necessary time based on shared type.
    E.g. module.ingest, module.generate_feed, passing
    the resources the module needs
    - each module should get a read-only db connection
    to the databases of other modules and osf, as 
    well as a read and write db-connection for its own database
    - module functions will be given a max timeout, and 
    their databases will be given a max size, that way
    the functioning of a particular module can't impede
    the functioning of other modules 
  - is there a way for modules to run code which isn't just python?
  but still provide read and write resources to modules as necessary?
  - should I just make db connection available to all modules,
  or is there a way to also provide it with python packages
  with model definitions that it needs (for OSF models,
  and models of other modules)
  - how to make posts and actions available to renderers?
    - provide renderer with posts http endpoint (which takes page as a paramater, to allow for 
  loading on scroll)
    - provide renderer with action http endpoint (which calls correspondent function of input
    module based on body of post)