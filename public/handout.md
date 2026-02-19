# CMSC 12 - Fundamentals of Programming 2  
## First Programming Exam
### Problem: Inventory & Order Tracking System in Java (OOP + Custom Exceptions)

**REQUIRED: JAVA 25**
In this exam, you will design and implement a **basic inventory and order tracking system** in **Java**, organized into **multiple classes** with clear responsibilities. You must apply object-oriented principles such as **encapsulation**, **separation of concerns**, and **exception-based validation**.

---

## System Overview

Your system must represent:

- **Products**
- **Orders**
- A **Store** that manages multiple products and multiple orders (provided with minimal edits needed)

The system should provide the following features:

1. Create a store record (**name** and **opening date**)
2. Define two maximum limits when creating the store:
   - Maximum number of products, **P**
   - Maximum number of orders, **O**
3. Store up to **P** product records and up to **O** order records
4. Add products
5. Restock products (increase quantity)
6. Update a product’s:
   - name
   - price
7. Search products by name
8. Create orders (reduces stock if possible)
9. Cancel orders (restores stock)
10. Display store credentials, product listings, and order listings
11. Compute **order age in days** based on order date

You will implement this program in Java by writing **six classes**:

1. `Product` class  
2. `Order` class  
3. `Store` class  
4. `InvalidProductDataException` class  
5. `StoreCapacityExceededException` class  
6. `RecordNotFoundException` class

> You may add more helper classes/methods if needed, but the required class names and required method names must be followed.
> The `StoreConsole` class will be provided to you.

---

## Part 0: The StoreConsole Class

Access the `StoreConsole` class by:
```bash
  wget -O StoreConsole.class http://{LOCAL SERVER}:8080/public/StoreConsole.class
```
This will download the `StoreConsole` class in your project directory.

---

## Part 1: User-Defined Exceptions (Very Important)

You must create and use **three custom exception classes**. Each must:

- Extend `Exception`
- Provide a constructor that accepts an error message

### Required Custom Exceptions

1. `InvalidProductDataException`  
   Thrown when:
   - Product name is empty or null
   - Price is negative
   - Quantity is negative
   - Restock/deduct amount is invalid
   - Order contains invalid amount/date/id/name

2. `StoreCapacityExceededException`  
   Thrown when:
   - Adding a product exceeds product capacity
   - Creating an order exceeds order capacity

3. `RecordNotFoundException`  
   Thrown when:
   - Updating a non-existent product
   - Accessing an invalid index (product/order)
   - Canceling a non-existent order
   - Creating an order for a non-existent product

Some cases may be forgotten, please refer to the succeeding parts.

You can test your User-defined exceptions by:
**You have max 3 test for this part**

```bash
  javac InvalidProductDataException.java StoreCapacityExceededException.java RecordNotFoundException.java
  curl.exe -F "args=-p1" -F "files=@InvalidProductDataException.class" -F "files=@StoreCapacityExceededException.class" -F "files=@RecordNotFoundException.class" http://{LOCAL SERVER}:8080/submit
```

---

## Input and Validation Rules

- Dates must use `LocalDate`
- Date format: `YYYY-MM-DD`
- Names must not be empty
- Prices must be non-negative
- Quantities must be non-negative
- Capacities must be positive
- Order amounts must be positive
- Order date must not be in the future

---

## Part 2: The Product Class

Each `Product` object represents an item the store can sell.

### Required Instance Variables

`Product` must have the following private instance variables:

- `name` of type `String`
- `price` of type `double`
- `quantity` of type `int`

> **Encapsulation is required.** No direct field access outside the class.

### Constructor Requirements

The constructor must accept **three parameters**:

- `name`
- `price`
- `quantity`

It must:
- Initialize all fields
- Validate all inputs
- Throw a user-defined exception if:
  - `name` is `null` or empty
  - `price` is negative
  - `quantity` is negative

### Required Methods

Provide proper getters and setters for all variables:

- `public String getName()`
- `public double getPrice()`
- `public int getQuantity()`

- `public void setName(String name)`  
- `public void setPrice(double price)`  
- `public void setQuantity(int quantity)`

**Setters must validate input** and throw a user-defined exception on invalid values.

Also include:

- `public void restock(int amount)`
  - Adds to quantity
  - Throws exception if `amount <= 0`

- `public boolean deductStock(int amount)`
  - Deducts if enough quantity exists
  - Returns `true` if deducted, `false` otherwise  
  - Throws exception if `amount <= 0`

You can test your `Product` class by:
**You have max 3 test for this part**

```bash
  javac Product.java
  curl.exe -F "args=-p2" -F "files=@Product.class" http://{LOCAL SERVER}:8080/submit
```

---

## Part 3: The Order Class

Each `Order` represents a purchase request for a product.

### Required Instance Variables (private)

- `orderId` of type `String`
- `productName` of type `String`
- `amount` of type `int`
- `orderDate` of type `LocalDate`

### Constructor Requirements

The constructor must accept **four parameters**:

- `orderId`
- `productName`
- `amount`
- `orderDate`

It must:
- Initialize all fields
- Validate all inputs
- Throw a user-defined exception if:
  - `orderId` is `null` or empty
  - `productName` is `null` or empty
  - `amount` is not positive
  - `orderDate` is `null` or in the future

### Required Methods

Provide getters and setters (with validation):

- `public String getOrderId()`
- `public String getProductName()`
- `public int getAmount()`
- `public LocalDate getOrderDate()`

Also include:

- `public int getOrderAgeInDays()`
  - Returns only **full completed days** since `orderDate` until today
  - Hint: use toEpochDay() method of LocalDate to compare, then cast the output to `int`.

You can test your `Order` class by:
**You have max 3 test for this part**

```bash
  javac Product.java Order.java
  curl.exe -F "args=-p3" -F "files=@Product.class" -F "files=@Order.class" http://{LOCAL SERVER}:8080/submit
```

---

## Part 4: The Store Class

The `Store` stores store credentials and manages collections of products and orders.

> The `Store` class is already with little update needed. You just need to check if all requirements here are implemented.

Access the `Store` class by:
```bash
  wget -O Store.java http://{LOCAL SERVER}:8080/public/Store.java
```
This will download the `Store` java file in your project directory.

---

### Required Instance Variables (private)

- `name` of type `String`
- `openingDate` of type `LocalDate`

- `products` an array of type `Product`
- `productSize` of type `int` (current number of products stored)
- `productCapacity` of type `int` (maximum number of products)

- `orders` an array of type `Order`
- `orderSize` of type `int` (current number of orders stored)
- `orderCapacity` of type `int` (maximum number of orders)

### Constructor Requirements

The constructor must accept **four parameters**:

- `name`
- `openingDate`
- `productCapacity`
- `orderCapacity`

It must:
- Initialize all fields
- Allocate arrays using capacities
- Set initial sizes to 0
- Validate inputs and throw a user-defined exception if:
  - `name` is `null` or empty
  - `openingDate` is `null` or in the future
  - `productCapacity` is not positive
  - `orderCapacity` is not positive

### Required Getter Methods

- `public String getName()`
- `public LocalDate getOpeningDate()`

- `public Product[] getProducts()`
- `public int getProductSize()`
- `public int getProductCapacity()`

- `public Order[] getOrders()`
- `public int getOrderSize()`
- `public int getOrderCapacity()`

### Required Core Methods

#### Product Operations

1. **addProduct**
   - Signature: `public boolean addProduct(Product product)`
   - Adds product to the array
   - Returns `true` if successful
   - Throws `StoreCapacityExceededException` if product capacity is reached
   - Throws `InvalidProductDataException` if product is `null`

2. **updateProduct**
   - Signature: `public boolean updateProduct(Product target, Product replacement)`
   - Replaces target product
   - Returns `true` if replaced
   - Throws `RecordNotFoundException` if target not found
   - Throws `InvalidProductDataException` if target or replacement is `null`

3. **searchProductByName**
   - Signature: `public Product searchProductByName(String name)`
   - Case-insensitive comparison using `equalsIgnoreCase()`
   - Returns first match or `null` if not found

4. **getProductAt**
   - Signature: `public Product getProductAt(int index)`
   - Returns product if index valid
   - Throws `RecordNotFoundException` if index out of range

#### Order Operations

5. **createOrder**
   - Signature: `public boolean createOrder(Order order)`
   - Must:
     - Check if order is null → throw `InvalidProductDataException`
     - Check if order capacity is reached → throw `StoreCapacityExceededException`
     - Find the product by `order.getProductName()`
       - If not found → throw `RecordNotFoundException`
     - Deduct stock using `deductStock(order.getAmount())`
       - If insufficient stock → throw `InvalidProductDataException` (or a message via the same exception class)
     - Add the order to orders array
   - Returns `true` if created

6. **cancelOrder**
   - Signature: `public boolean cancelOrder(String orderId)`
   - Must:
     - Check if orderId is null or empty → throw `InvalidProductDataException`
     - Find order by `orderId` (case-insensitive is optional)
     - If not found → throw `RecordNotFoundException`
     - Restore stock to the related product (restock amount)
     - Remove the order from the orders array (shift items to fill gap)
   - Returns `true` if canceled

7. **searchOrderById**
   - Signature: `public Order searchOrderById(String orderId)`
   - Returns first match or `null`

8. **getOrderAt**
   - Signature: `public Order getOrderAt(int index)`
   - Throws `RecordNotFoundException` if index out of range

You can test your `Store` class by:
**You have max 3 test for this part**

```bash
  javac Store.java Order.java Product.java
  curl.exe -F "args=-p4" -F "files=@Product.class" -F "files=@Order.class" -F "files=@Store.class" http://{LOCAL SERVER}:8080/submit
```

---

## Test Everything!

Assuming you have successfully compiled the previous parts.

```bash
  java StoreConsole
```

Below will be a sample output.

---

## Sample Output (Illustrative)

```bash
Inventory & Order System: Java Version

Enter store name: ByteMart
Enter opening date (YYYY-MM-DD): 2018-07-01
Enter max products: 2
Enter max orders: 3

Store created successfully.

Store Menu
(A) Add product
(R) Restock product
(U) Update product
(L) List products
(O) Create order
(X) Cancel order
(F) Find product by name
(I) Store info
(Q) Quit
A

Enter product name: USB Cable
Enter price: 199.50
Enter quantity: 10
Product successfully added.

O
Enter order id: ORD-1001
Enter product name: USB Cable
Enter amount: 3
Enter order date (YYYY-MM-DD): 2026-02-10
Order created successfully.

O
Enter order id: ORD-1002
Enter product name: USB Cable
Enter amount: 999

Error: InvalidProductDataException -- insufficient stock.

Q
Program terminated.
```

---

## Deliverables

Submit the following `.java` files:

- `Product.java`
- `Order.java`
- `Store.java`
- `InvalidProductDataException.java`
- `StoreCapacityExceededException.java`
- `RecordNotFoundException.java`

Use the command below and replace **YOUR_STUDENT_NUMBER** with your actual student number. If you have not completed some of the files yet, simply remove the corresponding line for each missing file from the command.

```bash
  curl.exe -s `
  -F "student=YOUR_STUDENT_NUMBER" `
  -F "files=@Product.java" `
  -F "files=@Order.java" `
  -F "files=@Store.java" `
  -F "files=@InvalidProductDataException.java" `
  -F "files=@StoreCapacityExceededException.java" `
  -F "files=@RecordNotFoundException.java" `
  http://{LOCAL SERVER}:8080/submit-all


```
**Inform your instructor once you have submitted to validate your submission.**

---

## Notes

- Follow encapsulation strictly (private fields, validated setters)
- Prefer shifting array elements after deletions to avoid gaps
- Do not use advanced collections (e.g., `ArrayList`).