# Working with Child Process in Node.js

- **#2** in the Codedamn Node.js list
- **Difficulty:** Medium
- **Source:** https://codedamn.com/problem/YUS93Qk5qjvFisuewOY5r
- **Starter repo:** https://github.com/mehulmpt/web-development-labs (branch `lab_1683275259`)

---

In this lab, you will learn how to use the `child_process` module in Node.js by implementing two utility functions - `execCommand` and `execFileCommand`. These functions will allow you to execute shell commands and executables directly from your Node.js application.

The `execCommand` function should accept a command string as input and return a promise that resolves with the command output. Similarly, the `execFileCommand` function should accept a filename and an array of arguments and return a promise that resolves with the command output.

### Steps


1. **Importing the Required Module:** Firstly, we need to import the 'child_process' module from Node.js. We can do this by using the 'import' keyword. In this case, we're only importing the 'exec' and 'execFile' functions since those are the only ones we're using.

   Code:
   ```js
   import { exec, execFile } from 'child_process'
   ```

2. **Creating the execCommand Function:** We will encapsulate the functionality of the `exec` function within our 'execCommand' function. The 'exec' function runs a shell command in a child process and returns the output.

   The `execCommand` function should accept a command string as an argument. This command string is the shell command that you want to execute directly from your Node.js code.

   Inside `execCommand`, we will return a Promise which will resolve with the output of the command, or reject with an error if there occurred any while running the command.

   Code:
```js
exec(command, (error, stdout, stderr) => {
	if (error) {
		 // handle error
	} else {
		// return output
	}
})
```

3. **Creating the execFileCommand Function:** The `execFileCommand` function should be similar to the `execCommand` function, but instead of a command string, it should accept a filename (of the executable) and an array of arguments.

   We will use the `execFile` method, which works like the `exec` function, but it executes a file (especially helpful when you want to run executable files) instead of a shell command. 

   Code:
 ```js
 execFile(filename, args, (error, stdout, stderr) => {
	 if (error) {
			 // handle error
	 } else {
			// return the output 
	 }
 })
 ```


At the end of this lab, you should be able to run shell commands and executable files directly from your Node.js application using the created `execCommand` and `execFileCommand` functions.


> Make sure to export the functions for the test cases to verify your functions. You functions should return a promise and not the direct output of the `exec` and `execFile`
