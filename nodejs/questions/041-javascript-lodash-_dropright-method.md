# JavaScript: Lodash - _.dropRight() method

- **#41** in the Codedamn Node.js list
- **Difficulty:** Easy
- **Source:** https://codedamn.com/problem/l9C0wJRxE77H71Ea5SmUA
- **Starter repo:** https://github.com/mehulmpt/web-development-labs (branch `lab_1683713571`)

---

In this lab, you'll explore the `_.dropRight()` method from the lodash library. This method is used to remove elements from the end of an array, based on the number of elements specified. The original array is not mutated as a result of using this method.

```js
const _ = require('lodash')

const array = [1, 2, 3, 4, 5]

console.log(_.dropRight(array, 2)) // [1, 2, 3]
```

**Task:** Implement the `dropRight` function similar to lodash's `_.dropRight()` method. Use the following function signature: `function dropRight(array, n)`.

> Make sure to export the function to run the test cases on your code. This Lab uses ESM exports
