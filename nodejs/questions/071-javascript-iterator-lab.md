# JavaScript Iterator Lab

- **#71** in the Codedamn Node.js list
- **Difficulty:** Medium
- **Source:** https://codedamn.com/problem/B2Gw42c9KTbfONf0OWyYJ
- **Starter repo:** https://github.com/mehulmpt/web-development-labs (branch `lab_1683272096`)

---

In this lab, you'll develop a deeper understanding of iterators in JavaScript by creating two fundamental functions: `range` and `mapIterator`. These functions are essential for array manipulation, allowing you to generate and transform arrays effectively. Remember to export each function using `export default` so they can be imported and utilized in other files.

### Challenges

1. **Creating and Exporting the Range Function**:
   - Task: Write a function named `range` that takes two arguments, `start` (inclusive) and `end` (inclusive), and returns an array of numbers ranging from `start` to `end`.
   - Key Logic: Initialize an empty array, use a loop to add numbers from `start` to `end` to this array, and then return the array.
   - Export: Ensure to export this function as the default export from its file.
   - Examples to Test: 
     - `range(1, 3)` should return `[1, 2, 3]`.
     - `range(5, 8)` should return `[5, 6, 7, 8]`.

2. **Creating and Exporting the MapIterator Function**:
   - Task: Develop a function named `mapIterator` that takes an array and a callback function as arguments, returning a new array with elements transformed by the callback.
   - Key Logic: Start with an empty array, iterate over the input array, apply the callback function to each element, and add the result to the new array.
   - Export: Export this function as the default export from its file.
   - Examples to Test:
     - Using `mapIterator` on `[1, 2, 3]` with a callback that doubles the number should return `[2, 4, 6]`.
     - Applying `mapIterator` to `[2, 4, 6]` with a callback that adds 5 to each number should result in `[7, 9, 11]`.

3. **Applying the created Range and MapIterator Functions**

- Import both `range` and `mapIterator` functions in the `index.js` file 
- Create and export a variabe named `myRange` that holds the value of `range(1,10)` 
- Create a function `timesTwo` that takes in a value `n` and returns `2n` 
- Create and export a variable named `doubledRange` which stores the return value of `mapIterator` with the arguments `myRange` and `timesTwo`

All the best!
