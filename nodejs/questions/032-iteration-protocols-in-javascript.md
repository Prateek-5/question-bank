# Iteration Protocols in JavaScript

- **#32** in the Codedamn Node.js list
- **Difficulty:** Easy
- **Source:** https://codedamn.com/problem/lieAN8XqzZNg9cNbmYCeU
- **Starter repo:** https://github.com/mehulmpt/web-development-labs (branch `lab_1683276008`)

---

# Iteration Protocols in JavaScript

In this lab, you'll be creating an iterator and iterable for a range of numbers. JavaScript has two iteration protocols: iterable and iterator. This lab will introduce you to both iterable and iterator, and you will implement the Range class as an iterable.

**An Iterable** is an object that can be iterated using a 'for..of' loop. To make an object iterable, it must implement the `Symbol.iterator` method, which returns an iterator.

**An Iterator** is an object that keeps track of its current position in an iterable. It has a `next()` method that returns the next value in the sequence, and a `done` property that indicates whether the end of the iterable has been reached.

In this lab, you will create a Range class that defines a range of numbers (start and end). The Range class will implement the iterable protocol so that a range of numbers can be iterated using a 'for..of' loop. You'll also write tests to demonstrate the Range class iterator works properly.
