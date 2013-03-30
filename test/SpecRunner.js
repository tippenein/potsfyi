require.config({
  baseUrl: "../static/js/lib/",
  //urlArgs: 'cb=' + Math.random(),  // avoid browser caching issues
  paths: {
    jquery: 'jquery',
    underscore: 'underscore-1.4.2',
    backbone: 'backbone-0.9.2',
    'backbone.localStorage': 'backbone.localStorage',
    jasmine: 'jasmine',
    'jasmine-html': 'jasmine-html',
    spec: '../../test/spec/'
  },
  shim: {
    underscore: {
      exports: "_"
    },
    backbone: {
      deps: ['underscore', 'jquery'],
      exports: 'Backbone'
    },
    'backbone.localStorage': {
      deps: ['backbone'],
      exports: 'Backbone'
    },
    jasmine: {
      exports: 'jasmine'
    },
    'jasmine-html': {
      deps: ['jasmine'],
      exports: 'jasmine'
    }
  }
});


window.store = "TestStore"; // override local storage store name for testing

require(['underscore', 'jquery', 'jasmine-html'], function(_, $, jasmine){

  var jasmineEnv = jasmine.getEnv();
  jasmineEnv.updateInterval = 1000;

  var htmlReporter = new jasmine.HtmlReporter();

  jasmineEnv.addReporter(htmlReporter);

  jasmineEnv.specFilter = function(spec) {
    return htmlReporter.specFilter(spec);
  };

  var specs = [];

  specs.push('spec/models/TestSpec');
  specs.push('spec/views/TestViewSpec');


  $(function(){
    require(specs, function(){
      jasmineEnv.execute();
    });
  });

});
