# JavaScript Arrow Functions

- **#59** in the Codedamn Node.js list
- **Difficulty:** Easy
- **Source:** https://codedamn.com/problem/QtepUY4JRgaW2j-iy3ipC
- **Starter repo:** https://github.com/mehulmpt/web-development-labs (branch `lab_1683581947`)

---

Welcome to this practical arrow functions lab where you will explore and learn about JavaScript arrow functions, their creation, and how to export them. 

*Arrow functions*, introduced with [ES6](http://es6-features.org/#Constants) , are a new way to write JavaScript functions. They are excellent when working with functional programming styles. What makes them interesting is their brevity and the fact that they don't create their own `this` context. 

### Arrow Functions Notations

*Expression Syntax*: If your function takes a single parameter and returns a single expression, you can write it in its shortest form like `(param) => expression`

*Multiline Syntax*: If your function code is too extensive, you need brackets and a return statement: 
```javascript
(param1, param2) => {
  // Function body
  return result;
}
```

*No Parameter*: If your function doesn't have any parameters, you need to include an empty set of parentheses:
```javascript
() => {
  // Function body
  return result;
}
```

### This Binding In Arrow Functions
Arrow functions do not have their own `this` value. The value of `this` inside an arrow function remains the same throughout the lifecycle of the function and is always bound to the value of `this` in the closest non-arrow parent function.

Arrow functions are a simplified syntax for writing function expressions in JavaScript, introduced with ES6. They are not just syntactically different; arrow functions come with an added advantage: they bound the `this` keyword to the surrounding (lexical) context.


Now that the lesson is complete, let's just create a simple Arrow Function 

### Steps 

1. Declare a constant `greet` and assign an arrow function that takes `name` as a parameter.
2. Make the function return a string greeting, embedding `name` variable within it. The format of the output string should be as mentioned below to pass the tests. For Example, if the name is `Sam` then the output would be 
```
Hello, Sam!
``` 
3. If the `greet` function recevies a non-string input, the function should return `undefined`. The `greet` function should also return `undefined` if the length of the string is less than or equal to zero. 
4. Finally, export your `greet` function with `export default greet;` to make it available for the tests.

> This Lab uses ESM Imports, make sure to use `default export` instead of `module.exports` 

That's it, you've completed all the tasks to pass this lab! Kudos 🎉
