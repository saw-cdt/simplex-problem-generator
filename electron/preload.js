const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  // Expose safe methods if needed, e.g. for saving the PDF to disk specifically:
  // saveFile: (data) => ipcRenderer.invoke('dialog:saveFile', data)
});
