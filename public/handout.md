**Math 154 \- Computer Programming 2**  
**Second Semester AY 2025 \- 2026**

# Module 5: Principles of OOP

## Laboratory Guide

# Graded Laboratory Exercise 5

## Problem: The 4 pillars of OOP in Banking

In this exercise, your task is to design and implement a Java application that demonstrates the four pillars of Object-Oriented Programming: Abstraction, Encapsulation, Inheritance, and Polymorphism using a real-world banking checkout/payment scenario.

A banking system typically supports multiple payment channels (e.g., cards and wallets). The checkout module should be able to process any payment type without needing to know its concrete class, while still enforcing security rules like masking sensitive details and protecting account balances.

You will implement this program in Java by writing the following classes:

* PaymentMethod (abstract class)  
* Wallet (encapsulation)  
* CardPayment (inherits from PaymentMethod)  
* WalletPayment (inherits from PaymentMethod)  
* Checkout (polymorphism)  
* BankingPaymentTester (provided as .class)

A tester class may be provided to validate correctness, formatting, and method existence.

## Part 1: Abstraction

The PaymentMethod class represents a banking payment channel contract. All payment types must follow the same contract so that the checkout system can treat them uniformly.

### Requirements

Create an abstract class named PaymentMethod with the following:

1. Abstract method  
   * public abstract boolean pay(double amount);  
   * Returns true if the payment succeeds, otherwise false.

2. Masked details method  
   * public String getMaskedDetails()  
   * You may implement it as:  
     * abstract, or  
     * concrete (default behavior), depending on your design.  
   * Must return a safe-to-display identifier (e.g., masked card number or wallet label).

### Banking realism rule

* Never expose full sensitive details (e.g., full card number so use \*\*\*) in getMaskedDetails().

## Part 2: Encapsulation

The Wallet class represents a stored-value balance similar to an e-wallet or digital bank sub-account.

### Instance Variable

* private double balance;

### Required Methods

1. public Wallet()  
   * Initializes balance to 0.

2. public Wallet(double initialBalance)  
   * If initialBalance is negative, it must be rejected using validation logic (see “Rejection rule”).

3. public void deposit(double amount)  
   * Adds to balance.

4. public boolean withdraw(double amount)  
   * Deducts from the balance if possible.  
   * Returns true if the withdrawal succeeds, otherwise false.

5. public double getBalance()  
   * Returns the balance (read-only access).

### Rules

* Reject **negative deposits**  
* Reject withdrawals if:  
  * amount is negative, OR  
  * amount is greater than balance  
* Keep balance **private**; only modify through methods.

### Rejection rule (no exceptions yet)

Since you do not have exception handling yet, you must implement rejections using **while loops**:

* If invalid input is detected, use a while loop to prevent continuing until a valid amount is used.  
* In a real system, this might be done via exceptions or error objects; here, you will enforce it using loops and simple messages.

### Part 3: Inheritance

Create at least **two concrete payment types** that extend PaymentMethod.

## A) CardPayment

Represents a debit/credit card charge.

### Required Fields (private)

* cardNumber (String)  
* cardHolderName (String)

### Required Constructor

* public CardPayment(String cardNumber, String cardHolderName)

### Required Behaviors

1. public boolean pay(double amount)  
   * Reject payment if amount \<= 0 (use validation logic).  
   * If valid, simulate a successful charge and return true.  
   * (In real banking, this would call a gateway; here, you simulate.)

2. public String getMaskedDetails()  
   * Must return a masked card format, such as:  
     * "\*\*\*\* \*\*\*\* \*\*\*\* 1234 (Juan Dela Cruz)"  
   * Only show the **last 4 digits** of the card number.

## B) WalletPayment

Represents payment using a Wallet balance.

### Required Field (private)

* Wallet wallet

### Required Constructor

* public WalletPayment(Wallet wallet)

### Required Behaviors

1. public boolean pay(double amount)  
   * Reject payment if amount \<= 0.  
   * Attempt wallet.withdraw(amount)  
   * Return true if the withdrawal succeeds; otherwise, return false.

2. public String getMaskedDetails()  
   * Must return something safe, like:  
     * "WALLET (Balance Available)" or "WALLET-\*\*\*\*"  
   * Must not reveal internal private fields directly.

### Part 4: Polymorphism

The Checkout class represents a checkout/payment processor that is **agnostic** to payment type.

### Required Method

* public boolean process(PaymentMethod method, double amount)

### Requirements

* Must call: method.pay(amount)  
* Must not use logic like:  
  * if (method instanceof CardPayment) ...  
  * The entire point is to rely on polymorphism.  
* Should return the result of method.pay(amount)

### **Real-world expectation**

In banks, checkout is a “front system” that just sends requests to whatever payment channel is selected. It does not handle channel-specific logic.

## Test with the Main

In your terminal,  download by copy pasting the code below:

| wget \-O BankingPaymentTester.class http://10.0.24.149:8081/public/BankingPaymentTester.class |
| :---- |

Then run the code:

| javac \*.javajava BankingPaymentTester |
| :---- |

## Submission

In your terminal, download the script by copy and pasting the code below:

| wget GLChecker.ps1 http://10.0.24.149:8081/public/GLChecker.ps1 |
| :---- |

Then run by copy and pasting:

| powershell.exe \-ExecutionPolicy Bypass \-File GLChecker.ps1 |
| :---- |

## Grading Process

The program output for this laboratory shall be checked during the dedicated laboratory time. Specifically:

1. Compiling and Running Assessment  
2. Basic Input/Output Assessment

Failure to provide the above during the dedicated time will result in a max grade of 10 pts. 

The following will be performed after submission:

1. Code Quality Assessment  
2. Technical Specifications Assessment

The **Program's Deadline is at the end of your Laboratory Session.**

## What to submit 

Submit your JAVA files to the dedicated submission bin in the LMS. Note of the deduction for late submission.

## Grading Assessment

Each Java File will be assessed according to this assessment.

| Points | Description |
| :---: | ----- |
| 50 | All technical requirements are met Student independently demonstrates the ability to compile and run the program from the command line (CLI) The program compiles and runs without errors Correct output is produced for all valid inputs Output format exactly matches the specification Excellent code quality: clear structure, meaningful naming, consistent formatting, appropriate comments, no unnecessary code |
| 40 | One minor technical requirement is missing or partially implemented Student demonstrates the ability to compile and run the program from the CLI The program compiles and runs without errors Correct output for all valid inputs with minor formatting differences Good code quality: readable and organized with minor naming, formatting, or commenting issues |
| 30 | Some technical requirements are missing or incomplete Student demonstrates compiling and running the program from the CLI with minor guidance The program compiles and runs, but may show warnings or minor runtime issues Correct output for at least 50% of test cases Fair code quality: basic structure present, inconsistent formatting or naming, limited comments |
| 20 | Many technical requirements are missing Student struggles to compile or run the program from the CLI and requires significant assistance The program runs only for a limited number of cases or with errors Correct output for less than 50% of test cases Poor code quality: disorganized structure, poor naming and formatting, repetitive or unnecessary code |
| 10 | A student cannot independently compile and run the program from the CLI The program requires substantial instructor intervention to compile or run Output is mostly incorrect Very poor code quality: minimal structure, hard-coded values, incomplete logic, little attention to readability |
| 0 | The student cannot compile or run the program from the CLI The program does not produce correct output for any input Code is missing, non-functional, or unrelated to the assignment |

# 

## Credits 

These materials were developed through the collaboration of  Ms. Bea D. Santiago, Asst. Prof. John D. Ultra, Asst. Prof. Ryan Rey M. Daga, Mr. Kenn Acabal,  and Mr. Samson Rollo. 