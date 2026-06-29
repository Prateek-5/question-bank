# Revocable Proxies in JavaScript

- **#33** in the Codedamn Node.js list
- **Difficulty:** Easy
- **Source:** https://codedamn.com/problem/gSz8DzZFMusG6EjlTq7xZ
- **Starter repo:** https://github.com/mehulmpt/web-development-labs (branch `lab_1683276536`)

---

In this lab, you'll create a function called `createRevocableProxy()` which should create and return a revocable proxy object from the given original object. A revocable proxy can be revoked by calling a revoke function, which will disable the use of the proxy. This works using the `Proxy.revocable()` method in JavaScript, which returns an object with properties `proxy` and `revoke`. Your task is to create the `createRevocableProxy()` function and test it.
