(() => {
  var __defProp = Object.defineProperty;
  var __export = (target, all) => {
    for (var name in all)
      __defProp(target, name, { get: all[name], enumerable: true });
  };

  // sample.module.css
  var sample_exports = {};
  __export(sample_exports, {
    default: () => sample_default,
    myclass: () => myclass
  });
  var myclass = "sample_myclass";
  var sample_default = {
    myclass
  };

  // sample.js
  window.classes = sample_exports;
})();
