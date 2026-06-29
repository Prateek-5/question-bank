# Inheritance in JavaScript

- **#18** in the Codedamn Node.js list
- **Difficulty:** Medium
- **Source:** https://codedamn.com/problem/4kXdc7TM-cKuzdCjKssKA
- **Starter repo:** https://github.com/mehulmpt/web-development-labs (branch `lab_1682760196`)

---

In this interactive lab, you will develop a basic understanding of classes, inheritance, and methods in JavaScript. The final outcome includes creating two classes, `Person` and `Student`, with the `Student` class extending or inheriting from `Person`. The lab will have you demonstrate JavaScript class syntax, methods, class constructors, and class inheritance concepts, creating a solid foundation in these areas.

### Concepts 

Few concepts you should familiarise yourself with before starting the lab are: 

- **JavaScript Classes**: A class is a type of function, defined with the `class` keyword. It's a blueprint for creating objects.

- **Class Constructors**: The constructor method is a special method for creating and initializing objects in a class.

- **JavaScript Methods**: JavaScript methods are actions that can be performed on objects.

- **Class Inheritance**: Class Inheritance is when a class inherits characteristics from another class.

### Steps 

To successfully complete this lab, you should perform the following steps:

1. Begin by creating a class named `Person`. This will be your parent class. 

2. Within the `Person` class, define a constructor that takes `name` as a parameter. This constructor will set the `name` property of your instances.

3. Next, add a method to your `Person` class. This method, `greeting`, should return a string that uses the `name` property.

4. Now, create a second class, `Student`, that inherits from `Person` (i.e., it should extend the `Person` class).

5. Within the `Student` class, define a constructor that takes two parameters: `name` and `course`. Make sure that your constructor calls the `super()` method with `name` as its argument. This will ensure that your `Student` instances have a `name` property.

6. Lastly, add a method to the `Student` class named `courseDetails`. This method should return a string that includes the `course` property.

### Examples 

Here's a simplified example of a class with a method and a constructor:

```js
class Sample {
   constructor(property) {
      this.property = property;
   }

   method() {
      return `This is my ${this.property}`;
   }
}
```

In this example, `Sample` is a class. `constructor(property)` is a constructor method which sets the `property` of the class, and `method()` is a class method that utilizes this property.

### Hints 

- To create a class in JavaScript, use the `class` keyword followed by the name of the class. 

- The constructor method is a special method for creating and initializing an object created with a class.

- `super()` is used in the context of constructors to call a parent class's constructor. 

- Methods in JavaScript classes are defined without the `function` keyword. 

- Remember to use the `this` keyword when referring to class properties in methods.
