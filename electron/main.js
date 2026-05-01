const { app, BrowserWindow } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

let mainWindow;
let pythonProcess;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    titleBarStyle: 'hiddenInset',
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false
    }
  });

  const isDev = !app.isPackaged;

  if (isDev) {
    mainWindow.loadURL('http://localhost:5173');
  } else {
    const frontendPath = path.join(__dirname, 'frontend-dist', 'index.html');
    console.log('[Electron] Loading frontend from:', frontendPath);
    mainWindow.loadFile(frontendPath);
    
    mainWindow.webContents.on('did-fail-load', (event, errorCode, errorDescription) => {
      console.error('[Electron] Failed to load:', errorCode, errorDescription);
    });
    
    mainWindow.webContents.on('did-finish-load', () => {
      console.log('[Electron] Frontend loaded successfully');
    });
  }

  mainWindow.on('closed', function () {
    mainWindow = null;
  });
}

function startPythonBackend() {
  const isDev = !app.isPackaged;
  
  let pythonPath;
  let args = [];
  let cwdPath;

  if (isDev) {
    pythonPath = path.join(__dirname, '..', 'backend', 'venv', 'bin', 'python');
    args = ['-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', '8000'];
    cwdPath = path.join(__dirname, '..', 'backend');
    runUvicorn();
  } else {
    // Production: use system Python (dependencies already installed)
    pythonPath = '/Library/Frameworks/Python.framework/Versions/3.14/bin/python3';
    if (!require('fs').existsSync(pythonPath)) {
      pythonPath = '/usr/bin/python3';
    }
    
    // Backend is in app folder inside asar
    cwdPath = path.join(__dirname, 'app');
    args = ['-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', '8000'];
    
    console.log('[Electron] Using Python:', pythonPath);
    runUvicorn();
  }
  
  function runUvicorn() {
    console.log('[Electron] Starting backend:', pythonPath);
    console.log('[Electron] CWD:', cwdPath);
    
    try {
      pythonProcess = spawn(pythonPath, args, {
        cwd: cwdPath,
        env: { ...process.env, PYTHONPATH: cwdPath },
        stdio: ['ignore', 'pipe', 'pipe']
      });

      pythonProcess.stdout.on('data', (data) => {
        console.log(`[FastAPI]: ${data}`);
      });

      pythonProcess.stderr.on('data', (data) => {
        console.error(`[FastAPI]: ${data}`);
      });

      pythonProcess.on('error', (err) => {
        console.error('[FastAPI] Failed:', err);
      });
    } catch (err) {
      console.error('[Electron] Exception:', err);
    }
  }
}

app.on('ready', () => {
  console.log('[Electron] App ready, starting...');
  startPythonBackend();
  
  // Wait for backend to start before loading window
  setTimeout(() => {
    createWindow();
  }, 3000);
});

app.on('will-quit', () => {
  if (pythonProcess) {
    pythonProcess.kill();
  }
});

app.on('window-all-closed', function () {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', function () {
  if (mainWindow === null) {
    createWindow();
  }
});
