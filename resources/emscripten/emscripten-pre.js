// Note: The `Module` context is already initialized as an
// empty object by emscripten even before the pre script
Module = { ...Module,
  preRun: [onPreRun],
  postRun: [],

  print: (...args) => {
    console.log(...args);
  },

  printErr: (...args) => {
    console.error(...args);
  },

  canvas: (() => {
    const canvas = document.getElementById('canvas');

    // See http://www.khronos.org/registry/webgl/specs/latest/1.0/#5.15.2
    canvas.addEventListener('webglcontextlost', event => {
      event.preventDefault();
    }, false);

    canvas.addEventListener('webglcontextrestored', () => {
      Module.api.resetCanvas();
    });

    return canvas;
  })(),

  setStatus: text => {
    if (!Module.setStatus.last) Module.setStatus.last = {
      time: Date.now(),
      text: ''
    };

    if (text !== Module.setStatus.text) {
      document.getElementById('status').innerHTML = text;
    }
  },

  totalDependencies: 0,

  monitorRunDependencies: left => {
    Module.totalDependencies = Math.max(Module.totalDependencies, left);
    Module.setStatus(left ? `Preparing... (${Module.totalDependencies - left}/${Module.totalDependencies})` : 'Downloading game data...');
  }
};

/**
 * Parses the current location query to setup a specific game
 */
function parseArgs () {
  const items = window.location.search.substr(1).split("&");
  let result = [];

  // Store saves in subdirectory `Save`
  result.push("--save-path");
  result.push("Save");

  for (let i = 0; i < items.length; i++) {
    const tmp = items[i].split("=");

    if (tmp[0] === "project-path" || tmp[0] === "save-path") {
      // Filter arguments that are set by us
      continue;
    }

    // Filesystem is not ready when processing arguments, store path to game
    if (tmp[0] === "game" && tmp.length > 1) {
      Module.game = tmp[1];
      continue;
    }

    result.push("--" + tmp[0]);

    if (tmp.length > 1) {
      const arg = decodeURI(tmp[1]);
      // Split except if it's a string
      if (arg.length > 0) {
        if (arg.startsWith('"') && arg.endsWith('"')) {
          result.push(arg.slice(1, -1));
        } else {
          result = [...result, ...arg.split(" ")];
        }
      }
    }
  }

  return result;
}

function onPreRun () {
  // Retrieve save directory from persistent storage before using it
  FS.mkdir("Save");
  FS.mount(Module.saveFs, {}, 'Save');

  // For preserving the configuration. Shared across website
  FS.mkdir("/home/web_user/.config");
  FS.mount(IDBFS, {}, '/home/web_user/.config');

  const runtimeDependency = 'rpg-runtime-filesystem-ready';
  Module.runtimeFileSystemReady = false;
  addRunDependency(runtimeDependency);
  FS.syncfs(true, function(err) {
    if (err) {
      Module.runtimeFileSystemError = String(err);
      abort('runtime filesystem initialization failed');
    }
    try {
      for (const entry of Module.runtimeRestoreFiles || []) {
        const separator = entry.path.lastIndexOf('/');
        if (separator > 0) FS.mkdirTree(entry.path.slice(0, separator));
        FS.writeFile(entry.path, entry.bytes);
      }
    } catch (writeError) {
      Module.runtimeFileSystemError = String(writeError);
      abort('runtime filesystem payload initialization failed');
    }
    Module.runtimeFileSystemReady = true;
    removeRunDependency(runtimeDependency);
  });
}

Module.setStatus('Downloading...');
Module.arguments = ["easyrpg-player", ...parseArgs()];

if (Module.runtimeEngineMode) {
  Module.arguments.push("--engine", Module.runtimeEngineMode);
}
if (Module.runtimeRestoreSlot) {
  Module.arguments.push("--load-game-id", String(Module.runtimeRestoreSlot));
}

if (Module.game === undefined) {
  Module.game = "";
} else {
  Module.arguments.push("--game", Module.game);
  Module.game = Module.game.toLowerCase();
}

// Catch all errors occuring inside the window
window.addEventListener('error', (event) => {
  // workaround chrome bug: See https://github.com/EasyRPG/Player/issues/2806
  const errorMessage = typeof event.error?.message === 'string' ? event.error.message : '';
  if (errorMessage.includes("side-effect in debug-evaluate") && event.defaultPrevented) {
    return;
  }

  Module.setStatus('Exception thrown, see JavaScript console…');
  Module.setStatus = text => {
    if (text) Module.printErr(`[post-exception status] ${text}`);
  };
});
