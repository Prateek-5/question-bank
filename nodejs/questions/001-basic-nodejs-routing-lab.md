# Basic Node.js Routing Lab

- **#1** in the Codedamn Node.js list
- **Difficulty:** Easy
- **Source:** https://codedamn.com/problem/R_0wxYfNwCrwymJ3YKzmu
- **Starter repo:** https://github.com/mehulmpt/web-development-labs (branch `lab_1683278540`)

---

In this lab, you will learn how to create and manage basic routing in a Node.js application. We will use the native `http` module to create an HTTP server and handle different routes based on the requested path.

### Steps

1. Your code contains two files `index.js` and `routes.js`, a `router` function has already been declared for you in `routes.js` file, you have to write the mentioned logic in the `router` function. 

2. To write the logic of the function take a look at the stubs (comments in code) to help you understand the desired outcome. You have to send different text responsed based on the path the request was invoked from. 

* If the `req.url` is equal to `/hello`, your server should send the text `Hello, World!` with the status code `200` 
* If the `req.url` is equal to `/bye`, you server should send the text `Goodbye, World!` with the status code `200`
* If the `req.url` does not match any of the above conditions it should send the text `Not found` with the status code `404` 

To send a valid Text via a HTTP server, you would have to additionally set the status code & `Content-Type` header in the response. Here is a sample code 
```js
function router(req, res) {
	res.writeHead(404, { 'Content-Type': 'text/plain' })
	res.end('Not found')
}
```

In the above function, we're returning the response with the status code `404` and the text `Not found` 

3. You have to import the `router` function in the `index.js` file and use this function to create a basic HTTP server. 

4. You can create a simple HTTP Server using `http.createServer(yourfunction)` method. Where you would replace the `yourfunction` with `router` in this scenario. 

5. The HTTP Server created should listen for requests on port `1337`. Use the `.listen()` method on the created HTTP server.

You can verify if the HTTP server is working as expected by visiting the `hello` and `bye` route in the browser preview that is visible to you on the right side of your screen


> Use ES modules for importing and exporting files. The `package.json` already has the property of `type` set to `module`
