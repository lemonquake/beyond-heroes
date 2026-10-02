// Local compatibility shim for game-dev 1.0.2 directory fsync on Windows.
// Suppress EPERM only on a directory handle; file sync errors still propagate.
// This changes no installed files and does not bypass model validation/hashes.
import fs from 'node:fs/promises';
import { pathToFileURL } from 'node:url';
const originalOpen = fs.open.bind(fs);
if (process.platform === 'win32') {
  fs.open = async (...args) => {
    const handle = await originalOpen(...args);
    const originalSync = handle.sync.bind(handle);
    handle.sync = async () => {
      try { return await originalSync(); }
      catch (error) {
        if (error.code === 'EPERM' && (await handle.stat()).isDirectory()) return;
        throw error;
      }
    };
    return handle;
  };
}
const cli = process.argv.splice(2, 1)[0];
if (!cli) throw new Error('Expected the installed game-dev CLI path');
process.argv[1] = cli;
await import(pathToFileURL(cli).href);
