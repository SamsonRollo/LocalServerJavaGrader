<center>
University of the Philippines <br>
Tacloban College<br>
Division of Natural Sciences and Mathematics<br>
Second Semester AY 2025 – 2026<br>
<br>CMSC 12 — Fundamentals of Programming 2<br>   
Second Semester AY 2025 \- 2026 <br><br>
</center>

# Module 5: Inheritance and Polymorphism
<p style="font-size:150%; color:#666; margin-top:-10px;">Laboratory Guide</p>

## Graded Laboratory Exercise 6

### Problem: Campus Services Asset Tracker in Java

In this laboratory exercise, your task is to design and implement a **campus services asset tracker**. The program will be organized using multiple classes, each with a clearly defined responsibility, applying object-oriented principles such as **inheritance, polymorphism, encapsulation, and separation of concerns**.

The system must represent:

- **Assets** owned or managed by a campus unit, and  
- An **AssetManager** that manages multiple assets.

This exercise must explicitly use:

- **At least one interface**
- **At least one abstract class**
- **Inheritance and polymorphism**
- **Method overriding**
- **Method overloading**
- **ArrayList**
- **HashMap**

The Asset Tracker should provide the following features:

- Create a tracker record (unit name and setup date)
- Define the **maximum number of assets** when creating the manager
- Store assets using an **ArrayList**
- Maintain a **HashMap for fast ID lookup**
- Add assets
- Delete assets
- Edit an asset’s:
  - name
  - status
- Search assets:
  - by ID
  - by name
  - by status
- Assign or unassign an asset to a person
- Display tracker credentials and asset summaries
- Compute each asset’s **days in service**

You will implement the program by writing the following classes/interfaces:

- `AssetConsole` class (**provided**)  
- `Maintainable` interface  
- `Asset` abstract class  
- `Laptop` class  
- `LabEquipment` class  
- `AssetManager` class  
- `AssetStatus` class  
- `InvalidAssetDataException` class  
- `AssetNotFoundException` class  
- `AssetCapacityException` class  

---

# Part 0: The AssetConsole Class (Provided)

`AssetConsole` will be provided and serves as the **driver class** of the program.

It will:

- Create an `AssetManager`
- Accept user input
- Call methods from your classes

You **must not modify** the provided `AssetConsole`.

Your implementation must compile and run when used with the provided console.

---

# Part 1: User-Defined Exceptions

Create the following custom exception classes. Each must:

- Extend `Exception`
- Provide a constructor that accepts an error message.

## Required Exception Classes

- `InvalidAssetDataException`
- `AssetNotFoundException`
- `AssetCapacityException`

Example structure:

```java
public class InvalidAssetDataException extends Exception {
    public InvalidAssetDataException(String message) {
        super(message);
    }
}
```

---

# Part 2: Asset Status Constants

Create a class named `AssetStatus`.

This class must contain **only public static final variables of type `String`** representing valid asset statuses.

The class must define the following variables:

- `AVAILABLE`
- `IN_USE`
- `UNDER_MAINTENANCE`
- `RETIRED`

Each variable’s **value must be exactly the same as its variable name**.

Example:

```java
public class AssetStatus {

    public static final String AVAILABLE = "AVAILABLE";
    public static final String IN_USE = "IN_USE";
    public static final String UNDER_MAINTENANCE = "UNDER_MAINTENANCE";
    public static final String RETIRED = "RETIRED";

}
```

### How to Use `AssetStatus`

Access a constant using the class name:

```java
asset.setStatus(AssetStatus.IN_USE);
```

Compare status values using `.equals()`:

```java
if (asset.getStatus().equals(AssetStatus.AVAILABLE)) {
    System.out.println("Asset is available.");
}
```

Only these constants are valid status values.

---

# Part 3: Interface

## Interface: `Maintainable`

Represents assets that can undergo maintenance actions.

### Required Methods

```java
boolean needsMaintenance();
void performMaintenance(String ticketId) throws InvalidAssetDataException;
```

### Required Static Method

```java
static boolean isValidTicket(String ticketId)
```

A maintenance ticket ID must match the pattern:

```
MT-XXXX
```

Where `X` is a digit.

Example valid ticket:

```
MT-1023
```

Code hint:

```java
public static boolean isValidTicket(String ticketId) {
    if (ticketId == null) return false;
    return ticketId.matches("MT-\\d{4}");
}
```

---

# Part 4: The Asset Abstract Class

Each campus asset is a specialized type of `Asset`.

## Required Instance Variables (private)

```
int id
String name
String status
LocalDate purchaseDate
String assignedTo
```

Encapsulation is required. Fields must be **private**.

---

## Static Members

```
private static int nextId;
```

Use a **static block** to initialize the ID counter.

Example:

```java
static {
    nextId = 5000;
}
```

---

## Constructor Requirements

The constructor must accept:

```
name
purchaseDate
```

The constructor must:

- Generate a unique ID using the static counter
- Set status to `AssetStatus.AVAILABLE`
- Set `assignedTo` to `null`
- Validate inputs

Throw `InvalidAssetDataException` if:

- name is null or empty
- purchaseDate is null
- purchaseDate is in the future

---

## Required Methods

### Getters

Provide getters for all instance variables.

### Setters (with validation)

```
setName(String name)
setStatus(String status)
setAssignedTo(String person)
```

Validation rules:

- name must not be empty
- status must not be null
- assignedTo may be null, but if not null must not be empty

---

### Days in Service

```
int getDaysInService()
```

Return the number of **full days** between `purchaseDate` and today.

Code hint:

```java
return (int) ChronoUnit.DAYS.between(purchaseDate, LocalDate.now());
```

---

### Abstract Method

```
abstract String getAssetType();
```

---

### Summary Method

```
String getSummary()
```

Must return a **one-line summary** exactly in the format:

```
ID | TYPE | NAME | STATUS | assignedTo=VALUE | days=DAYS
```

Example:

```
5001 | Laptop | Dell-IT-01 | AVAILABLE | assignedTo=Juan D. | days=120
```

If the asset is not assigned:

```
assignedTo=None
```

---

### toString Override

Override `toString()` to return:

```
getSummary()
```

---

# Part 5: Concrete Asset Types

Implement **two subclasses** of `Asset`.

Both classes must:

- Extend `Asset`
- Override `getAssetType()`
- Override `getSummary()`
- Implement `Maintainable`

---

## Class 1: Laptop

### Additional private fields

```
String serialNumber
int ramGB
```

Validation rules:

- serialNumber must not be empty
- ramGB must be positive

### Asset type

```
"Laptop"
```

### Maintenance logic

```
needsMaintenance()
```

Return `true` if:

```
getDaysInService() > 365
```

### performMaintenance

Validate ticket using:

```
Maintainable.isValidTicket(ticketId)
```

If invalid, throw `InvalidAssetDataException`.

If valid:

```
status = AssetStatus.AVAILABLE
```

---

## Class 2: LabEquipment

### Additional private fields

```
String labRoom
LocalDate calibrationDueDate
```

Validation rules:

- labRoom must not be empty
- calibrationDueDate must not be null

### Asset type

```
"LabEquipment"
```

### Maintenance logic

Maintenance is required if:

```
calibrationDueDate is today or earlier
```

---

# Part 6: Method Overloading Requirement

In `AssetManager`, implement the following **overloaded search methods**.

```
Asset search(int id)
Asset search(String name)
ArrayList<Asset> search(String status)
```

Requirements:

- `search(int)` must use the **HashMap**
- `search(String name)` must be **case-insensitive**
- `search(String status)` returns **all assets with that status**

---

# Part 7: The AssetManager Class

The `AssetManager` manages all assets.

## Required instance variables (private)

```
String unitName
LocalDate setupDate
ArrayList<Asset> assets
HashMap<Integer, Asset> byId
int capacity
```

---

## Constructor

The constructor must accept:

```
unitName
setupDate
capacity
```

Throw `InvalidAssetDataException` if:

- unitName is null or empty
- setupDate is null or in the future
- capacity <= 0

---

## Required Methods

### Getters

```
getUnitName()
getSetupDate()
getAssets()
getCapacity()
getSize()
```

---

### Add Asset

```
boolean addAsset(Asset asset)
```

Behavior:

- Throw `AssetCapacityException` if size equals capacity
- Add asset to:
  - `ArrayList`
  - `HashMap`

Return `true` if successful.

---

### Delete Asset

```
boolean deleteAsset(int id)
```

Behavior:

- If asset does not exist → throw `AssetNotFoundException`
- Remove from:
  - `ArrayList`
  - `HashMap`

Return `true`.

---

### Get Asset by ID

```
Asset getById(int id)
```

Must use the **HashMap**.

Throw `AssetNotFoundException` if not found.

---

### Update Status

```
boolean updateStatus(int id, String newStatus)
```

Throw:

```
AssetNotFoundException
InvalidAssetDataException
```

---

### Assign Asset

```
void assignAsset(int id, String person)
```

---

### Unassign Asset

```
void unassignAsset(int id)
```

---

### Print All Assets

```
void printAll()
```

Must demonstrate **polymorphism** by printing assets as:

```java
System.out.println(asset);
```

This will call the overridden `toString()` method in each asset type.

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