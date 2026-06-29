# OS Information

- **#16** in the Codedamn Node.js list
- **Difficulty:** Easy
- **Source:** https://codedamn.com/problem/hCTQQRolC-IFSe7gPSbUY
- **Starter repo:** https://github.com/mehulmpt/web-development-labs (branch `lab_1683803646`)

---

In this lab, we will explore how to use the `os` module in Node.js to gather information about the operating system. This is useful when you want to write platform-specific code or gather statistics about your application's environment. Throughout the lab, you will be required to export variables to be tested. We will be using the ESM syntax for all imports and exports.

Some important functions in the `os` module are:

- `os.type()`: returns the operating system name.
- `os.freemem()`: returns the amount of free system memory in bytes.
- `os.totalmem()`: returns the total amount of system memory in bytes.
- `os.uptime()`: returns the system uptime in seconds.

Remember that to use these functions, you need to import the `os` module using the following syntax:
```js
import os from 'os';
```

Feel free to read the [Node.js documentation](https://nodejs.org/dist/latest-v18.x/docs/api/os.html#os) if you need additional information about the `os` module and its functions.
