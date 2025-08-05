import {
  _extends,
  _objectWithoutPropertiesLoose
} from "./chunk-H3QGJKSP.js";
import {
  require_react_is
} from "./chunk-K7E3GE6C.js";
import {
  require_react
} from "./chunk-65KY755N.js";
import {
  __commonJS,
  __toESM
} from "./chunk-V4OQ3NZ2.js";

// node_modules/hoist-non-react-statics/dist/hoist-non-react-statics.cjs.js
var require_hoist_non_react_statics_cjs = __commonJS({
  "node_modules/hoist-non-react-statics/dist/hoist-non-react-statics.cjs.js"(exports, module) {
    "use strict";
    var reactIs = require_react_is();
    var REACT_STATICS = {
      childContextTypes: true,
      contextType: true,
      contextTypes: true,
      defaultProps: true,
      displayName: true,
      getDefaultProps: true,
      getDerivedStateFromError: true,
      getDerivedStateFromProps: true,
      mixins: true,
      propTypes: true,
      type: true
    };
    var KNOWN_STATICS = {
      name: true,
      length: true,
      prototype: true,
      caller: true,
      callee: true,
      arguments: true,
      arity: true
    };
    var FORWARD_REF_STATICS = {
      "$$typeof": true,
      render: true,
      defaultProps: true,
      displayName: true,
      propTypes: true
    };
    var MEMO_STATICS = {
      "$$typeof": true,
      compare: true,
      defaultProps: true,
      displayName: true,
      propTypes: true,
      type: true
    };
    var TYPE_STATICS = {};
    TYPE_STATICS[reactIs.ForwardRef] = FORWARD_REF_STATICS;
    TYPE_STATICS[reactIs.Memo] = MEMO_STATICS;
    function getStatics(component) {
      if (reactIs.isMemo(component)) {
        return MEMO_STATICS;
      }
      return TYPE_STATICS[component["$$typeof"]] || REACT_STATICS;
    }
    var defineProperty = Object.defineProperty;
    var getOwnPropertyNames = Object.getOwnPropertyNames;
    var getOwnPropertySymbols = Object.getOwnPropertySymbols;
    var getOwnPropertyDescriptor = Object.getOwnPropertyDescriptor;
    var getPrototypeOf = Object.getPrototypeOf;
    var objectPrototype = Object.prototype;
    function hoistNonReactStatics2(targetComponent, sourceComponent, blacklist) {
      if (typeof sourceComponent !== "string") {
        if (objectPrototype) {
          var inheritedComponent = getPrototypeOf(sourceComponent);
          if (inheritedComponent && inheritedComponent !== objectPrototype) {
            hoistNonReactStatics2(targetComponent, inheritedComponent, blacklist);
          }
        }
        var keys = getOwnPropertyNames(sourceComponent);
        if (getOwnPropertySymbols) {
          keys = keys.concat(getOwnPropertySymbols(sourceComponent));
        }
        var targetStatics = getStatics(targetComponent);
        var sourceStatics = getStatics(sourceComponent);
        for (var i = 0; i < keys.length; ++i) {
          var key = keys[i];
          if (!KNOWN_STATICS[key] && !(blacklist && blacklist[key]) && !(sourceStatics && sourceStatics[key]) && !(targetStatics && targetStatics[key])) {
            var descriptor = getOwnPropertyDescriptor(sourceComponent, key);
            try {
              defineProperty(targetComponent, key, descriptor);
            } catch (e) {
            }
          }
        }
      }
      return targetComponent;
    }
    module.exports = hoistNonReactStatics2;
  }
});

// node_modules/@tanem/react-nprogress/dist/react-nprogress.esm.js
var React = __toESM(require_react());
var import_react = __toESM(require_react());
var import_hoist_non_react_statics = __toESM(require_hoist_non_react_statics_cjs());
var clamp = function clamp2(num, lower, upper) {
  num = num <= upper ? num : upper;
  num = num >= lower ? num : lower;
  return num;
};
var createQueue = function createQueue2() {
  var isRunning = false;
  var pending = [];
  var _next = function next() {
    isRunning = true;
    var cb = pending.shift();
    if (cb) {
      return cb(_next);
    }
    isRunning = false;
  };
  var clear = function clear2() {
    isRunning = false;
    pending = [];
  };
  var enqueue = function enqueue2(cb) {
    pending.push(cb);
    if (!isRunning && pending.length === 1) {
      _next();
    }
  };
  return {
    clear,
    enqueue
  };
};
var createTimeout = function createTimeout2() {
  var handle;
  var cancel = function cancel2() {
    if (handle) {
      window.cancelAnimationFrame(handle);
    }
  };
  var schedule = function schedule2(callback, delay) {
    var deltaTime;
    var start;
    var _frame = function frame(time) {
      start = start || time;
      deltaTime = time - start;
      if (deltaTime > delay) {
        callback();
        return;
      }
      handle = window.requestAnimationFrame(_frame);
    };
    handle = window.requestAnimationFrame(_frame);
  };
  return {
    cancel,
    schedule
  };
};
var increment = function increment2(progress) {
  var amount = 0;
  if (progress >= 0 && progress < 0.2) {
    amount = 0.1;
  } else if (progress >= 0.2 && progress < 0.5) {
    amount = 0.04;
  } else if (progress >= 0.5 && progress < 0.8) {
    amount = 0.02;
  } else if (progress >= 0.8 && progress < 0.99) {
    amount = 5e-3;
  }
  return clamp(progress + amount, 0, 0.994);
};
var useEffectOnce = function useEffectOnce2(effect) {
  (0, import_react.useEffect)(effect, []);
};
var incrementParameter = function incrementParameter2(num) {
  return ++num % 1e6;
};
var useUpdate = function useUpdate2() {
  var _useState = (0, import_react.useState)(0), setState = _useState[1];
  return (0, import_react.useCallback)(function() {
    return setState(incrementParameter);
  }, []);
};
var useGetSetState = function useGetSetState2(initialState2) {
  if (initialState2 === void 0) {
    initialState2 = {};
  }
  var update = useUpdate();
  var state = (0, import_react.useRef)(_extends({}, initialState2));
  var get = (0, import_react.useCallback)(function() {
    return state.current;
  }, []);
  var set = (0, import_react.useCallback)(function(patch) {
    if (!patch) {
      return;
    }
    Object.assign(state.current, patch);
    update();
  }, []);
  return [get, set];
};
var useFirstMountState = function useFirstMountState2() {
  var isFirst = (0, import_react.useRef)(true);
  if (isFirst.current) {
    isFirst.current = false;
    return true;
  }
  return isFirst.current;
};
var useUpdateEffect = function useUpdateEffect2(effect, deps) {
  var isFirstMount = useFirstMountState();
  (0, import_react.useEffect)(function() {
    if (!isFirstMount) {
      return effect();
    }
  }, deps);
};
var noop = function noop2() {
  return void 0;
};
var initialState = {
  isFinished: true,
  progress: 0,
  sideEffect: noop
};
var useNProgress = function useNProgress2(_temp) {
  var _ref = _temp === void 0 ? {} : _temp, _ref$animationDuratio = _ref.animationDuration, animationDuration = _ref$animationDuratio === void 0 ? 200 : _ref$animationDuratio, _ref$incrementDuratio = _ref.incrementDuration, incrementDuration = _ref$incrementDuratio === void 0 ? 800 : _ref$incrementDuratio, _ref$isAnimating = _ref.isAnimating, isAnimating = _ref$isAnimating === void 0 ? false : _ref$isAnimating, _ref$minimum = _ref.minimum, minimum = _ref$minimum === void 0 ? 0.08 : _ref$minimum;
  var _useGetSetState = useGetSetState(initialState), get = _useGetSetState[0], setState = _useGetSetState[1];
  var queue = (0, import_react.useRef)(null);
  var timeout = (0, import_react.useRef)(null);
  useEffectOnce(function() {
    queue.current = createQueue();
    timeout.current = createTimeout();
  });
  var cleanup = (0, import_react.useCallback)(function() {
    var _timeout$current, _queue$current;
    (_timeout$current = timeout.current) == null || _timeout$current.cancel();
    (_queue$current = queue.current) == null || _queue$current.clear();
  }, []);
  var set = (0, import_react.useCallback)(function(n) {
    var _queue$current4;
    n = clamp(n, minimum, 1);
    if (n === 1) {
      var _queue$current2, _queue$current3;
      cleanup();
      (_queue$current2 = queue.current) == null || _queue$current2.enqueue(function(next) {
        setState({
          progress: n,
          sideEffect: function sideEffect2() {
            var _timeout$current2;
            return (_timeout$current2 = timeout.current) == null ? void 0 : _timeout$current2.schedule(next, animationDuration);
          }
        });
      });
      (_queue$current3 = queue.current) == null || _queue$current3.enqueue(function() {
        setState({
          isFinished: true,
          sideEffect: cleanup
        });
      });
      return;
    }
    (_queue$current4 = queue.current) == null || _queue$current4.enqueue(function(next) {
      setState({
        isFinished: false,
        progress: n,
        sideEffect: function sideEffect2() {
          var _timeout$current3;
          return (_timeout$current3 = timeout.current) == null ? void 0 : _timeout$current3.schedule(next, animationDuration);
        }
      });
    });
  }, [animationDuration, cleanup, minimum, queue, setState, timeout]);
  var trickle = (0, import_react.useCallback)(function() {
    set(increment(get().progress));
  }, [get, set]);
  var start = (0, import_react.useCallback)(function() {
    var _work = function work() {
      var _queue$current5;
      trickle();
      (_queue$current5 = queue.current) == null || _queue$current5.enqueue(function(next) {
        var _timeout$current4;
        (_timeout$current4 = timeout.current) == null || _timeout$current4.schedule(function() {
          _work();
          next();
        }, incrementDuration);
      });
    };
    _work();
  }, [incrementDuration, queue, timeout, trickle]);
  var savedTrickle = (0, import_react.useRef)(noop);
  var sideEffect = get().sideEffect;
  (0, import_react.useEffect)(function() {
    savedTrickle.current = trickle;
  });
  useEffectOnce(function() {
    if (isAnimating) {
      start();
    }
    return cleanup;
  });
  useUpdateEffect(function() {
    get().sideEffect();
  }, [get, sideEffect]);
  useUpdateEffect(function() {
    if (!isAnimating) {
      set(1);
    } else {
      setState(_extends({}, initialState, {
        sideEffect: start
      }));
    }
  }, [isAnimating, set, setState, start]);
  return {
    animationDuration,
    isFinished: get().isFinished,
    progress: get().progress
  };
};
var _excluded = ["children"];
var NProgress = function NProgress2(_ref) {
  var children = _ref.children, restProps = _objectWithoutPropertiesLoose(_ref, _excluded);
  var renderProps = useNProgress(restProps);
  return children(renderProps);
};
function withNProgress(BaseComponent) {
  var WithNProgress = function WithNProgress2(props) {
    var hookProps = useNProgress(props);
    return React.createElement(BaseComponent, _extends({}, props, hookProps));
  };
  (0, import_hoist_non_react_statics.default)(WithNProgress, BaseComponent);
  return WithNProgress;
}
export {
  NProgress,
  useNProgress,
  withNProgress
};
//# sourceMappingURL=@tanem_react-nprogress.js.map
