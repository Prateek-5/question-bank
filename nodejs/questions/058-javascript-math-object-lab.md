# JavaScript Math Object Lab

- **#58** in the Codedamn Node.js list
- **Difficulty:** Easy
- **Source:** https://codedamn.com/problem/sJuBtPemiWmWVbQClaxcR
- **Starter repo:** https://github.com/mehulmpt/web-development-labs (branch `lab_1683285872`)

---

In this lab, the primary objective is to understand and implement functions that perform geometric calculations related to circles. Specifically, participants will be tasked with creating two functions: `calcCircumference` and `calcArea`. Each function leverages the mathematical constant π (Pi), reflecting the relationship between the diameter (or radius) of a circle and its circumference and area respectively.

### Function Objectives:

1. **`calcCircumference(radius)`**:
    - This function should calculate the circumference of a circle.
    - The formula to calculate circumference `C` is `C = 2πr`, where `r` is the radius of the circle.
    - The function takes one argument, `radius`, which represents the radius of the circle.
    - It returns the calculated circumference as a numeric value.

2. **`calcArea(radius)`**:
    - This function should calculate the area of a circle.
    - The formula to calculate area `A` is `A = πr^2`, where `r` is the radius of the circle.
    - Similar to `calcCircumference`, this function takes one argument, `radius`.
    - It returns the calculated area as a numeric value.

### Steps to Implement:

1. **Write the Function `calcCircumference`**: 
    - Start by declaring the function using the keyword `function`.
    - Name the function `calcCircumference` and ensure it accepts one parameter, `radius`.
    - Inside the function, use the `Math.PI` constant to calculate the circumference.
    - Return the result.

2. **Write the Function `calcArea`**:
    - Declare another function named `calcArea`.
    - Accept `radius` as the parameter for this function as well.
    - Calculate the area using `Math.PI` &  `Math.pow` functions.
    - Return the result of the calculation.

3. **Export the Functions**:
    - Both functions should be individually exportable and usable in other modules.
    - Use the ECMAScript module (ESM) syntax for exporting.
    - `calcCircumference()` should be named export using the `export` keyword while `calcArea` function should be a default export using the `export default` keywords.
