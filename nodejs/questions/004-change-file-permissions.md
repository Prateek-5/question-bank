# Change File Permissions

- **#4** in the Codedamn Node.js list
- **Difficulty:** Easy
- **Source:** https://codedamn.com/problem/SuJf2LnfarGeCGIKJOWxC
- **Starter repo:** https://github.com/mehulmpt/web-development-labs (branch `lab_1683710794`)

---

In this lab, your task is to create a Node.js function, `changeFileMode`, that modifies the access permissions, or "mode", of a file. The function will take in two parameters: the file path and the new mode (an octal number representing the new file permissions). The function should be written in an asynchronous style using the `fs.chmod()` method from Node.js's File System (fs) module.

## Concepts:

1. `fs.chmod()` method: This is a function provided by Node.js's File System module, used to asynchronously change the permissions of a file identified by its path. It takes a file path and an octal number representing the new file mode as arguments.

2. Asynchronous programming in Node.js: Asynchronous programming allows you to perform operations without blocking the flow of execution in your program. In our case, while we're changing the file mode, other parts of the program could also be executing.

3. Importing and exporting with ESM: The use of `import fs from 'fs/promises';` is an example of ESM (ES Modules) syntax in Node.js used for importing and exporting modules. Here, we are importing the 'promises' part of the fs module, which contains methods that return promises.

4. Basic Error Handling: The `try...catch` block is used to capture and handle any errors that occur when invoking the `fs.chmod()` function.

## Steps:

1. Begin by importing the `fs/promises` package from Node.js's file system module.

2. Define an exported async function `changeFileMode()` which takes two arguments: a file path and a new mode.

3. Within this function, first include a condition to check if the file path input or new mode is not provided. If true, then return an error message indicating 'Invalid arguments'.

4. Next, encapsulate your `fs.chmod()` method inside a `try...catch()` block. The `try` part attempts to change the file mode, while the `catch` part handles any errors that may occur during the execution of the `try` part.

5. If successful, the function should asynchronously change the file mode; if not, it should throw an error.

Remember, the 'mode' is provided in an octal format (base-8 numeral system). Common chmod values include:

- `400` (Owner Read)
- `200` (Owner Write)
- `100` (Owner Execute)
- `040` (Group Read)
- `020` (Group Write)
- `010` (Group Execute)
- `004` (Others Read)
- `002` (Others Write)
- `001` (Others Execute)

By summing the above values, we can have combinations like `600` (Owner can Read and Write), `644` (Owner can Read & Write, Group and Others can Read), `755` (Owner can Read, Write & Execute, Group and Others can Read & Execute), and others.
