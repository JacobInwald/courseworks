[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-24ddc0f5d75046c5622901739e7c5dd533143b0c8e959d652212380cedb1ea36.svg)](https://classroom.github.com/a/ky87KGlJ)
[![Open in Codespaces](https://classroom.github.com/assets/launch-codespace-7f7980b617ed060a017424585567c406b6ee15c891e84e1186181d67ecf80aa0.svg)](https://classroom.github.com/open-in-codespaces?assignment_repo_id=14004484)
![BuildAndTest](../../workflows/BuildAndTest/badge.svg?branch=main) ![Points badge](../../blob/badges/.github/badges/points.svg)

# CT 2023/24 | Coursework 2 - Semantic Analysis

**Deadline:** Fri, 08.03.2024, 12:00pm  
**Instructors:** Amir Shaikhha  
**TAs:** Nikos Mavrogeorgis, Mahdi Ghorbani, Kim Stonehouse  
**Demonstrators:** Amir Khordadi, Pei Mu, Maks Kret

## Provided

This coursework already provides two semantic analyses:

 1) **Check Assign Target**:
 This analysis checks that the LHS of an assignment contains only expressions that can serve as targets of an assignment.
 2) **Name Analysis**:
 This analysis checks that only variable and function names are used that have previously been introduced.

## Tasks
1. Core: Type Checking
2. Expert: Dead Code Analysis


## Quick Install (for DICE-like environments)

### Download This Coursework

First, you will need to **clone** the repository. If you used GitHub before, you will already have either an HTTPS access token, or an SSH key. If you do not have either, you will need to create this. You can use either, just follow the guides below:
  - To create an SSH key, use [this](https://docs.github.com/en/authentication/connecting-to-github-with-ssh/generating-a-new-ssh-key-and-adding-it-to-the-ssh-agent)
  - To create an HTTPS token, use [this](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token)
    At some point, you will be asked to specify what you want to do with the token: feel free to tick all the boxes.

  At this point, you can clone the repository:
  - if you used HTTPS above, use the command
    ```
    git clone https://github.com/compiling-techniques/REPOSITORY_NAME.git
    ```
  - if you used SSH, use the command
    ```
    git clone git@github.com:compiling-techniques/REPOSITORY_NAME.git
    ```
Now enter the repository directory: `cd REPOSITORY_NAME`. If this is your first time using Git, you will need to set up a bit of configuration:
  ```
  git config --global user.name "your_github_username"
  git config --global user.email "your_github_email"
  ```
  This will set your username and email globally (for all repositories, unless they overwrite this), so all future GitHub repositories will already have this set up. If you do not wish to do that, just omit the `--global`.
  You can verify the setup using `git config -l`, which will just tell you what settings you set.

### Installation

You can create an isolated python environment using [venv](https://packaging.python.org/en/latest/guides/installing-using-pip-and-virtual-environments/#creating-a-virtual-environment).
To set up `venv` for the assignment, follow the steps below (a summary is given below the bulleted list):

1. Set up a virtual environment for the assignment with `python3.10 -m venv env`.
   This creates a subdirectory called `env` in the current folder that creates an isolated version of Python.
2. Activate the virtual environment by [`source`ing](https://linuxcommand.org/lc3_man_pages/sourceh.html) the activation file: `source env/bin/activate`
3. Confirm that you are in the virtual environment by running `which python`. The output should be `/path/to/coursework/env/bin/python`.
4. Upgrade pip with `pip install --upgrade pip`.
5. Run `pip install -U -r requirements.txt` to install dependencies within the virtual environment.
6. Run `pip install -e .` to install the ChocoPy compiler as a package.
7. If you are using PyCharm, please configure PyCharm to work with the environment by following the instructions on
   this page of the PyCharm manual: [Configure a virtual environment](https://www.jetbrains.com/help/pycharm/creating-virtual-environment.html).

In summary, the process looks as follows:

```bash
/path/to/coursework$ python3.10 -m venv env # set up virtual environment called `env`

/path/to/coursework$ source env/bin/activate # run activation file

(env) /path/to/coursework$ # (env) shows up

(env) /path/to/coursework$ which python # confirm python path
/path/to/coursework/env/bin/python

/path/to/coursework$ pip install --upgrade pip # upgrade pip

(env) /path/to/coursework$ pip install -U -r requirements.txt # install dependencies

(env) /path/to/coursework$ pip install -e . # install ChocoPy as a package

(env) /path/to/coursework$ # get to hacking, and best of luck! :)
```

#### PyCharm

It would be convenient for you, if you used a modern IDE for Python.
A popular choice, `PyCharm`, comes pre-installed in your DICE desktop environment.

If you decide to use `PyCharm`, in order to install the packages, you should open the embedded terminal (`Alt+F12` by default)
and follow the previous instructions using `pip install -U -r requirements.txt`.

#### Using GitHub code spaces

Instead of cloning the repository to your local machine, you can also use GitHub codespaces to do your coursework. This is a beta-test, so it is an optional offer that is delivered on a best-effort basis. To use GitHub codespaces click on the green "Code" button at the top of this repository, select "code spaces" and create your personal codespace. Then enter the console and run:

```bash
$ export PATH=/home/codespace/.local/lib/python3.10/site-packages/bin/:$PATH
$ pip install -U -r requirements.txt # install dependencies
$ pip install -e . # install ChocoPy as a package
$ # get to hacking, and best of luck! :)
```

### Test your solutions

You can use `lit` to automatically test your code, which is include in the `requirements.txt`.

To run it locally, do:

```bash
lit -v tests/type-checking/
```

This will examine recursively all the files with valid formats inside the above directory.
The `-v` flag adds a verbose output with more information in case some tests fail.
You can also leverage the `--timeout <seconds>` flag, in order to bound the time allowed for your test cases to run.
This way you can detect if your implementation loops infinitely in some test cases.

For more details on the configuration of `lit`, see `tests/lit.cfg`.
For more info on `lit` check the [online documentation](https://filecheck.readthedocs.io/en/latest/01-what-is-filecheck.html).

## Task 1 - Type Checking

The goal of task 1 is to write a type checker for the [ChocoPy Language](https://chocopy.org) in order to check if a syntactically valid program satisfies ChocoPy's type system and reject programs with meaningless or invalid code.
We call a program that has passed type checking *well typed*.

The template already provides a partial implementation of the type checker.
You will have to implement the rest.

### 1. Getting Started
**First read this README completely and carefully!**
It explains the type system of ChocoPy by looking at the [types](#2-types-of-chocopy), [typing environments](#3-typing-environments), and [type checking rules](#4-type-checking-rules).
We have also added some [hints](#5-hints) that are useful for this coursework.

To get started coding look at the file `choco/type_checking.py` which contains an incomplete implementation of the type checker.

The file contains of:

- Python classes representing the ChocoPy types.
- The operations on types: `is_subtype`, `is_assignment_compatible`, and `join`.
You will use them when implementing typing rules.
- Helper functions that will throw a `SemanticError` if their checks fail.
You can use them while implementing your type checking.
- The class `FunctionInfo` representing the information about functions stored in the environment.
- The `LocalEnvironment` type that is represented as a Python dictionary.
- A function `type_checking` that is the entry point for the type checker.
- A function `build_env` that builds the initial local environment.
- The "dispatch" functions: `check_stmt_or_def_list`, `check_stmt_or_def`, and `check_expr`.
These functions traverse the AST and must decide which typing rule to invoke for a given AST node.
**You will need to complete their implementations**. `check_stmt_or_def_list` is already given.
- The typing rules, each implemented by a Python function. **You will need to complete their implementations.** 

#### A good strategy for this coursework is to:
1. Read the file carefully and understand how the overall type checking process works.
2. Identify an existing or write a new test where the type checking does not work correctly yet.
3. Identify the typing rules that are missing to make the test pass.
4. Implement the typing rules by corresponding functions.
5. Modify the dispatch functions to call the new typing rules.
6. Go back to 2. until you have covered all typing rules.

#### We suggest the following order when implementing the typing rules:
1. Single variable assignment and list creation. (VAR-ASSIGN-STMT, LIST-DISPLAY, NIL)
2. Logical operators and conditional expressions. (AND, OR, NOT, IS)
3. Index operation. (STR-SELECT, LIST-SELECT)
4. Pass statement, control flow statements. (PASS, IF-ELSE, WHILE, FOR-STR, FOR-LIST)
5. Comparison operators. (INT-COMPARE, STR-COMPARE, BOOL-COMPARE)
6. Arithmetic operators. (NEGATE, ARITH, LIST-CONCAT, STR-CONCAT) 
7. Complex assign statements. (LIST-ASSIGN-STMT, MULT-ASSIGN-STMT)
8. Function definitions. (FUNC-DEF, INVOKE, RETURN-E, RETURN)

The `tests/type-checking` folder contains a directory for each section, making it easier
to check your progress.
Note that it is important to have all the tests in the first section, `assign-and-list`,
entirely correct, since the typing rules tested there are used throughout all tests.

### 2. Types of ChocoPy
From the grammar of [CW1](https://github.com/compiling-techniques/cw1-template) we know that a ChocoPy user can write the following types:
```
type := type_name | `[` type `]`
type_name := object | int | bool | str
```
In addition, ChocoPy has the following types that can not be written explicitly by the user:
 - `<Empty>` is the type of the expression `[]`
 - `<None>` is the type of the expression `None`
 - The [bottom type](https://en.wikipedia.org/wiki/Bottom_type) `⊥` (the type that has no value)

#### Type Hierarchy
All types are organized into a _type hierarchy_, which is 
visualized in the following diagram:
```
                             object
        ______________________/ \__________________________
       /      |     |      |           |         |         \
      int   bool   str   [int]  …  [[bool]]  <Empty>   <None>
       \______|_____|______|__   ______|_________|_________/
                              \ /
                               ⊥
```
#### Subtyping relationship
We can provide a precise description of the type hierarchy by defining a _subtyping_ relationship.<br/>
A type `T₁` is considered a subtype of `T₂` (written as `T₁ ≤ T₂`>) iff at least one of the following is true:
 - `T ≤ T` for all types `T`
 - `int ≤ object`
 - `bool ≤ object`
 - `str ≤ object`
 - `[T] ≤ object` for all types `T`
 - `<Empty> ≤ object`
 - `<None> ≤ object`
 - `⊥ ≤ T` for all types `T`

#### Assignment compatibility
To describe assignments, passing arguments to functions, and returning values form functions, we define _assignment compatibility_. The idea is that we may assign a value of type `T₁` to something of type `T₂` iff `T₁` is assignment compatible with `T₂`.<br/>
A type `T₁` is assignment compatible with `T₂` (written as `T₁ ≤a T₂`) iff at least one of the following is true:
 - `T₁ ≤ T₂` (i.e., `T₁` is a subtype of `T₂`)
 - `T₁` is `<None>` and `T₂` is not `int`, `bool`, `str`, or `⊥`
 - `T₂` is a list type `[T]` and `T₁` is `<Empty>`
 - `T₂` is a list type `[T]` and `T₁` is `[<None>]`, where `<None> ≤a T`.

The last rule allows us to write programs such as:
```python
x: [object] = [None, None]
```

#### Join of two types
Sometimes (e.g, when type checking an `if-then-else` expression), we need to find a single type that can be used to represent the two original types. For this, we define the _join_ operator.<br/>
The join of two types `T₁` and `T₂` (written as `T₁ ⨆ T₂`) is:
 - `T₂` if `T₁ ≤a T₂`
 - `T₁` if `T₂ ≤a T₁`
 - `object` otherwise, as it is the *least common ancestor* of `T₁` and `T₂`


### 3. Typing Environments
To type check a program, we will traverse its AST and inspect every program term.
When checking a term we will investigate its sub-terms to determine and check its type.
For example, to check the type of the term `1 + 4` we investigate `1` and `4`, conclude that both are of type `int` and, therefore, the addition is also of type `int` and is well typed.

We cannot determine the type of term without knowing the context of the term. Consider, for example, the call expression `foo(x)`.
We cannot say if this expression is well types, without knowing with what types `x` and `foo` were declared.

To capture this contextual information, we use a _typing environment_.
Our typing environment consists of two parts:
 - the *local environment* `O` which records information about currently declared variables and their types as well as information about the declared functions;
 - the *return type* `R` of the current function.

The content of typing environment changes when we traverse the AST, always representing the context of the sub-term we are currently investigating.

For a variable `v` we write: `O(v) = T` to record that the variable has type `T`.

For a function `f` we store more information in the local environment and write:

```
O(f) = {T₁ ⨯  … ⨯  Tₙ → T₀; x₁, …, xₙ; v₁: T'₁, …, vₘ: T'ₘ}
```
to record:

 - the *function type* of `f` with:
   - `T₁`, …, `Tₙ` the types of the function parameters
   - `T₀` the function return type
 - `x₁`, …, `xₙ` the names of the function parameters.
 - `v₁: T'₁`, …, `vₘ: T'ₘ` the identifiers and types of variables declared in the body of the function.

`R` is set to `⊥` when we are inspecting a term outside any function.

When type checking function definitions, we create a new typing environment to type check the body of the function.
This new environment is initialized with the content of the typing environment from the current scope.
We then need to update or add the parameters and their types to the new typing environment.
We write `O[T/c]` to add or update the binding of a variable, that is:
  - `O[T/c](c) = T`
  - `O[T/c](d) = O(d)` if `d ≠ c`


### 4. Type checking rules
The type checking rules describe how to check the type for a specific program term.
The general form of a type checking rule is:
```
     ⋮
---------------
 O, R ⊢ e : T
```
The rule consists of two parts:
 - zero, one, or multiple *premises* above the line, and
 - a *conclusion* below the line.

The rule states, that if the premises are true, then the conclusion is true as well.

`O, R ⊢ e : T` is a *typing judgement*, where the turnstyle `⊢` separates the typing environment from the proposition.
This judgement should be read as:
> "In the type environment with the local environment `O` and the return type `R` the expression `e` is well typed and has type `T`".

#### Discussion of some Typing Rules

A first example, is the typing rule for the negation operation (i.e., `-x`).
This rule states, that in the environment `O, R` we can conclude that `-e` is well typed and has type `int` if the sub-expression `e` has type `int` in the same environment:

```
 O, R ⊢  e : int 
------------------ [NEGATE]
 O, R ⊢ -e : int
```


---
When defining and initializing a variable, the rule states that in the environment `O, R` we can conclude that `id : T = e₁` is well typed, if:
 - `id` has the type `T` in the environment `O`;
 - the sub-expression `e₁` has type `T₁` in the same environment;
 - `T₁` is assignment compatible to `T`:

```
 O(id) = T
 O, R ⊢ e₁ : T₁
 T₁ ≤a T
--------------------- [VAR-INIT]
 O, R ⊢ id : T = e₁
```
The `:` used in the conclusion of the rule is here the syntax for type annotations.

---
For conditional expressions we use the `join` operation in the conclusion:
```
 O, R ⊢ e₀ : bool
 O, R ⊢ e₁ : T₁
 O, R ⊢ e₂ : T₂
------------------------------------ [COND]
 O, R ⊢ e₁ if e₀ else e₂ : T₁ ⨆ T₂
```

---
The rule for function definitions is the most complicated.

```
 T = T₀ if return type is present, <None> otherwise
 O(f) = {T₁ ⨯  … ⨯  Tₙ → T; x₁, …, xₙ; v₁: T'₁, …, vₘ: T'ₘ}
 O[T₁/x₁]…[Tₙ/xₙ][T'₁/v₁]…[T'ₘ/vₘ], R ⊢ b
------------------------------------------------------------------ [FUNC-DEF]
 O, R ⊢ def f(x₁: T₁, …, xₙ: Tₙ) ⟦→ T₀⟧? : b
```
Here, we determine the return type `T` depending on the return type annotation.
Then, we look of the function information in the environment `O(f)`.
Finally, we check the type of the function body `b` using a different environment:
 - where we have added the function parameters and nested variable definitions to the local environment `O`; and
 - where we use the return type `R`.

#### Complete set of Typing Rules

---
*Variables*

When reading a variable, the rule states that if the environment `O, R` assigns an identifier `id` a type `T`,
then the expression `id` has type `T`:

```
 O(id) = T; where T is not a function type.
-------------------------------------------- [VAR-READ]
 O, R ⊢ id : T
```

- `id` has the type `T` in the environment `O`;
- `T` is not a function type (like the `{T₁ ⨯ … ⨯ Tₙ -> T₀; x₁, …, xₙ}` which was described before)

We must, however, prohibit identifiers with function types when reading values
(that is, when identifiers are used as expressions in the syntax).
This simply reflects the fact that ChocoPy does not treat functions
as first-class (assignable, storable) values.

---
*Variable definitions and assignments*

```
 O(id) = T
 O, R ⊢ e₁ : T₁
 T₁ ≤a T
--------------------- [VAR-INIT]
 O, R ⊢ id : T = e₁
```

```
 O(id) = T
 O, R ⊢ e₁ : T₁
 T₁ ≤a T
------------------------- [VAR-ASSIGN-STMT]
 O, R ⊢ id = e₁
```

---
*Statement and Definitions list*: Type check all the component definitions and statements.

```
 O, R ⊢ s₁
 O, R ⊢ s₂
    …
 O, R ⊢ sₙ
 n ≥ 1
---------------------------------------------- [STMT-DEF-LIST]
 O, R ⊢ s₁ NEWLINE s₂ NEWLINE … sₙ NEWLINE
```

---
*Pass Statements*
```
------------------------- [PASS]
 O, R ⊢ pass
```

---
*Expression Statements*
```
 O, R ⊢ e : T
------------------------- [EXPR-STMT]
 O, R ⊢ e
```

---
*Literals*
```
------------------------- [BOOL-FALSE]
 O, R ⊢ False : bool
```

```
------------------------- [BOOL-TRUE]
 O, R ⊢ True : bool
```

```
 i is an integer literal
------------------------- [INT]
 O, R ⊢ i : int
```

```
 s is an string literal
------------------------- [STR]
 O, R ⊢ s : str
```

The None literal is assigned the (unmentionable) type `<None>`:

```
------------------------- [NONE]
 O, R ⊢ None : <None>
```

---
*Arithmetic and numerical relational operators*
```
 O, R ⊢ e : int
------------------------- [NEGATE]
 O, R ⊢ -e : int
```

```
 O, R ⊢ e₁ : int
 O, R ⊢ e₂ : int
 op ∈ {+, -, *, //, %}
------------------------- [ARITH]
 O, R ⊢ e₁ op e₂ : int
```

```
 O, R ⊢ e₁ : int
 O, R ⊢ e₂ : int
 ⨝ ∈ {<, <=, >, >=, ==, !=}
---------------------------- [INT-COMPARE]
 O, R ⊢ e₁ ⨝ e₂ : bool
```

```
 O, R ⊢ e₁ : bool
 O, R ⊢ e₂ : bool
 ⨝ ∈ {==, !=}
------------------------- [BOOL-COMPARE]
 O, R ⊢ e₁ ⨝ e₂ : bool
```

---
*Logical Operators*
```
 O, R ⊢ e₁ : bool
 O, R ⊢ e₂ : bool
-------------------------- [AND]
 O, R ⊢ e₁ and e₂ : bool
```

```
 O, R ⊢ e₁ : bool
 O, R ⊢ e₂ : bool
------------------------- [OR]
 O, R ⊢ e₁ or e₂ : bool
```

```
 O, R ⊢ e : bool
------------------------- [NOT]
 O, R ⊢ not e : bool
```

---
*Conditional expressions*
```
 O, R ⊢ e₀ : bool
 O, R ⊢ e₁ : T₁
 O, R ⊢ e₂ : T₂
----------------------------------- [COND]
 O, R ⊢ e₁ if e₀ else e₂ : T₁ ⨆ T₂
```

---
*String operations*
```
 O, R ⊢ e₁ : str
 O, R ⊢ e₂ : str
 ⨝ ∈ {==, !=}
------------------------- [STR-COMPARE]
 O, R ⊢ e₁ ⨝ e₂ : bool
```

```
 O, R ⊢ e₁ : str
 O, R ⊢ e₂ : str
------------------------- [STR-CONCAT]
 O, R ⊢ e₁ + e₂ : str
```

```
 O, R ⊢ e₁ : str
 O, R ⊢ e₂ : int
------------------------- [STR-SELECT]
 O, R ⊢ e₁[e₂] : str
```

---
*The 'is' operator*
```
 O, R ⊢ e₁ : T₁
 O, R ⊢ e₂ : T₂
 T₁, T₂ are not one of int, bool, str
------------------------------------- [IS]
 O, R ⊢ e₁ is e₂: bool
```

---
*List Displays*
```
 n ≥ 1
 O, R ⊢ e₁ : T₁
 O, R ⊢ e₂ : T₂
 …
 O, R ⊢ en : Tₙ
 T = T₁ ⨆ T₂ ⨆ … ⨆ Tₙ
--------------------------------- [LIST-DISPLAY]
 O, R ⊢ [e₁, e₂, …, en] : [T]
```

The empty list is a special case.
```
------------------------- [NIL]
 O, R ⊢ [] : <Empty>
```

---
List Operators
```
 O, R ⊢ e₁ : [T₁]
 O, R ⊢ e₂ : [T₂]
 T = T₁ ⨆ T₂
------------------------- [LIST-CONCAT]
 O, R ⊢ e₁ + e₂ : [T]
```


```
 O, R ⊢ e₁ : [T]
 O, R ⊢ e₂ : int
------------------------- [LIST-SELECT]
 O, R ⊢ e₁[e₂] : T
```

---
```
 O, R ⊢ e₁ : [T₁]
 O, R ⊢ e₂ : int
 O, R ⊢ e₃ : T₃
 T₃ ≤a T₁
------------------------- [LIST-ASSIGN-STMT]
 O, R ⊢ e₁[e₂] = e₃
```

---
*Multiple assignments*: Multiple assignment is type-checked by decomposing into individual single assignments, as follows:
```
 n > 1
 O, R ⊢ e₀ : T₀
 O, R ⊢ e₁ = e₀
 …
 O, R ⊢ en = e₀
 T₀ ≠ [<None>]
--------------------------------- [MULTI-ASSIGN-STMT]
 O, R ⊢ e₁ = e₂ = … = eₙ = e₀
```

The restriction that `T₀ ≠ [<None>]` avoids a subtle type-safety issue.
It is dangerous to allow there to be two different views of a list with differing element types.
The type `[<None>]` can only arise from list displays.
As long as the value of such a display is immediately consumed by assignment to a single variable,
parameter, or operand (`+`for lists), there will be only be one opinion as to its type subsequently.
But, multiple assignment opens the possibility of programs like this:

```python
x: [object] = None
y: [[int]] = None
x = y = [None]      # Trouble ahead!
x[0] = 5
print(y[0][0])      # ???
```

There is another very subtle point lurking here in the case where e₀ has type `<Empty>` (the type of the empty list).
In this case, however, we need no special rule because in ChocoPy, there is no **.append** method to allow elements to be added to an empty list.
Were that not the case, we could get this situation:

```python
A: [int] = None
B: [str] = None
A = B = []
A.append(3)
```

and we would subsequently have `B[0]` returning the value 3, which is certainly not a string.

---
*Function applications*
```
 O, R ⊢ e₁ : T''₁
 O, R ⊢ e₂ : T''₂
 …
 O, R ⊢ eₙ : T''ₙ
 n ≥ 0
 O(f) = {T₁ ⨯ … ⨯ Tₙ -> T₀; x₁, …, xₙ; v₁ : T'₁, …, vₘ : T'ₘ}
 ∀ 1 ≤ i ≤ n : T''ᵢ ≤a Tᵢ
-------------------------------------------------------------------- [INVOKE]
 O, R ⊢ f(e₁, e₂, …, eₙ) : T₀
```

To type check a function invocation, each of the arguments to the function must be first type checked.
The type of each argument must conform to the types of the corresponding formal parameter of the function.
The invocation expression is assigned the function’s declared return type.


---
*Return Statements*: This is where the return-type environment comes into play:
```
 O, R ⊢ e : T
 T ≤a R
------------------------- [RETURN-E]
 O, R ⊢ return e
```

---
```
 <None> ≤a R
------------------------- [RETURN]
 O, R ⊢ return
```

---
*Conditional statements*
```
 O, R ⊢ c : bool
 O, R ⊢ b₀
 O, R ⊢ b₁
------------------------------------------------------ [IF-ELSE]
 O, R ⊢ if c:b₀ else:b₁
```

---
*While statements*
```
 O, R ⊢ e : bool
 O, R ⊢ b
------------------------- [WHILE]
 O, R ⊢ while e:b
```

---
*For statements*
```
 O, R ⊢ e : str
 O(id) = T
 str ≤a T
 O, R ⊢ b
------------------------- [FOR-STR]
 O, R ⊢ for id in e:b
```

---
```
 O, R ⊢ e : [T₁]
 O(id) = T
 T₁ ≤a T
 O, R ⊢ b
------------------------- [FOR-LIST]
 O, R ⊢ for id in e:b
```

---
*Function Definitions*
```
 T = T₀ if return type is present, <None> otherwise
 O(f) = {T₁ x … x Tₙ → T; x₁, …, xₙ; v₁: T'₁, …, vₘ: T'ₘ}
 O[T₁/x₁]…[Tₙ/xₙ][T'₁/v₁]…[T'ₘ/vₘ], T ⊢ b
------------------------------------------------------------------ [FUNC-DEF]
 O, R ⊢ def f(x₁: T₁, …, xₙ: Tₙ) ⟦→ T₀⟧? : b
```

---
*The Global Typing Environment*: The following functions are predefined globally:

```
O(len) = {object -> int; arg}
O(print) = {object -> <None>; arg}
O(input) = {-> str}
```

### 5. Hints

#### Accessing the nodes of the AST

As shown in the type checking skeleton, in order to type check the AST nodes, you need to be able to access their fields properly.
The node fields are either attributes, which give information about the node, or regions.

Attributes can be accessed directly.
For the regions, you are interested in accessing the operations contained in the region.
In the case of `VarDef`, we have the following code:

```python
if isinstance(op, choco_ast.VarDef):
        typed_var = op.typed_var.op
        assert isinstance(typed_var, choco_ast.TypedVar)
        id = typed_var.var_name.data
        e1 = op.literal.op
```

So, `op` is a `VarDef` node.
We access the typed variable by accessing the `.typed_var` region of the node and use `.op` to access the operation in it.

Later, we access the name of the typed variable through the ".data" property of the attribute `.var_name`.

In the last statement, we get the expression `e1` assigned to the literal operation.

Other nodes will have more operations in their blocks, instead of just one. In this case we can use `.ops` instead of `.op`.

See again `dialects/choco_ast.py` for more info.

#### Updated choco-opt

As mentioned, the current coursework already provides a pass that checks the assignment targets,
as well as a name analysis check.
The `choco-opt` tool has been updated to enable this extra functionality with the `-p` flag,
which takes `check-assign-target` and `name-analysis` as arguments:

```bash
cd /path/to/coursework
tools/choco_opt.py -p name-analysis tests/name-analysis/global_write.mlir  # Gives semantic error

# Easier way to invoke tools/choco_opt.py
choco-opt -p name-analysis tests/name-analysis/global_write.mlir  # Gives semantic error

choco-opt -p check-assign-target tests/type-checking/assign-and-list/assign/assign_int.mlir  # Passes
choco-opt -p check-assign-target tests/check-assign-target/addition.mlir  # Gives semantic error
```

The type checking functionality is triggered with the argument `type-checking`.
The other flags are also active in the given type checking test cases.

You can try the current minimal type-checking functionality by running:
```bash
cd /path/to/coursework
choco-opt -p check-assign-target,name-analysis,type-checking tests/type-checking/base-rules/empty.mlir  # Passes
```

Note that you can run the current type-checking directly on a chocopy file by giving a `.choc` file instead of a `.mlir` file:
```bash
cd /path/to/coursework
choco-opt -p check-assign-target,name-analysis,type-checking your-test.choc
```

Note that you need to keep all three passes activated when developing your code.
As a shortcut, you can use the keyword `type` as a pass, instead of typing all of them:

```bash
cd /path/to/coursework
choco-opt -p type tests/type-checking/base-rules/empty.mlir  # Passes
```

Finally, you are only interested in passing the test cases of the `tests/type-checking` folder (these will be the visible ones).

#### Function definition

The function `build_env` has already built the local environment, so it already provides the type information for each function.
The goal of the function definition rule is, given the function's type information, to type check the function body.

To this end, you need to carefully read the rule of the function definition, which requires to type check the function body
using a *different* local environment that you will update with the information you got from the function.

#### Global/nonlocal

Given that these features are checked by the name analysis pass (you can see the code to find out how), there isn't anything special you need to do about them.

## Task 2 - Dead Code Analysis (Expert Task)
[Dead code](**https://en.wikipedia.org/wiki/Dead_code**) is a section of source code that can either never be executed at run-time or whose result is never used in any computation.
Removing the dead code will, therefore, not change the programs' observable behaviour.

The goal of task 2 is to write a pass that warns the programmer of dead code in the input program.
You should not remove the dead code, but only warn the programmer about it.

Of course there exist many possible forms of dead code. We give examples of three different forms below.

### Getting Started
The file `choco/warn_dead_code.py` contains a function `warn_dead_code` that is the entry point for the dead code warning pass. This function should print a warning if the program contains dead code.

To invoke the dead code analysis, add the `warn-dead-code` pass in `choco-opt`:

```bash
cd /path/to/coursework
choco-opt -p check-assign-target,name-analysis,type-checking,warn-dead-code your-test.choc
```

As a shortcut, you can use the keyword `warn` as a pass, instead of typing all of them:

```bash
cd /path/to/coursework
choco-opt -p warn your-test.choc
```

You can use any way you like to access and analyse the AST of the program.
We recommend that you make use of the `choco/ast_visitor.py`, that we have discussed in the Lecture and that is used for example in the `choco/name_analysis.py` pass.

Use the provided exceptions to print a warning that the program contains dead code. If multiple forms of dead code are present,
you can report any of them.

### Dead Code Categories

Here are all the type of dead code we will grade you on.

#### Unreachable code - Unreachable expressions
The following program has unreachable code
```python
def foo():
    return
    print("DEAD") # Unreachable statement
    return        # Unreachable statement
```

Here, the `print` statement is never executed, as the first `return` statement will finish the execution of the function.
A statement can be unreachable for multiple reasons, such as because it is after a `return` statement, or in
an `if/else` branch that is never executed. Note that since `pass` statements are ignored, an empty branch of an `if/else`
statement is not considered unreachable if it is never executed.

Expressions can also be unreachable, such as the right hand side of an `and`
expression that has the left hand side always evaluated to `False`, since `and` is short-circuiting.

Statements should be reported with `UnreachableStatementsError`, while expressions should be reported with `UnreachableExpressionError`.
Note that none of the exceptions require any arguments.

As a final example, consider:

```python
def foo():
    print("foo")

5 if True else foo()
```

This would give an unreachable expression, since the last statement itself is executed, but part of the expression inside the statement is not executed.
Hence, you should report `UnreachableExpressionError`.

#### Unused store
```python
x: int = 0
x = 5 # Unused store
```
Here the first assignment `x = 5` is dead code, because its result is not used.
Note that initialization values (like `0` here) are not considered dead code.

The following example has also an unused store, because it is overriden by the next assignment:
```python
x: int = 0
x = 2 # Unused store
x = 6
print(x)
```

We limit the scope of unused stores to variables, ignoring the indices case. In particular, this means that we do not consider this program to have dead code:

```python
x: [int] = None
x = [2, 3]
x[0] = 5
x[0] = 6
print(x[0])
```

Also, note that even if stores have side effects, they can be considered dead code, since it's the store itself
that is not used. For instance, the following program is considered to have dead code:

```python
def f(x: int) -> int:
    print(x)
    return x

x: int = 0
x = f(3) # Unused store
x = 6
print(x)
```

An unused store should be reported with `UnusedStoreError`. It should have as parameter the `Assign` operation
that is unused.

#### Unused variable / argument / function
```python
x: int = 0
```
Here, the variable declaration `x: int = 0` is dead code, as the variable is never used.
Note that a variable is only considered unused if it is not used in any way. If it is used
in an unreachable expression or statement, it is still considered used.

These warnings should be reported with `UnusedVariableError`, `UnusedArgumentError`, and `UnusedFunctionError`.
These exceptions are parametrized by the name of the unused variable, argument, or function.

As final example, consider:

```python
def foo():
	print("hello")

if False:
	foo()
```

We do not consider this function unused, but the statement that calls it unreachable.
If a function is not used because an expression or statement is unreachable, then we should warn about the expression or statement first, since the function is still called (though never executed).
Thus, you should return an `UnreachableStatementsError`.

#### Unused expression

```python
x: int = 5
x * 2    # Unused expression
```

Here, the expression `x * 2` is dead code, as the result of the expression is never used,
is not `None`, and has no side-effects.

Be aware that expressions may have side-effects, such as `print`, or `x[5]` (which will
raise an error if `x` is not long enough). However, if you can guarantee that the expression
has no side-effects, then it is dead code.

These warnings should be reported with `UnusedExpressionError`. You should give as parameter the
expression that is unused.

### Features to implement

Dead code may require complex analyses to be detected. In fact,
dead code analysis is undecidable in our language. Like compiler engineers,
you should first focus your analysis on simple cases that are easy to handle,
and then try more complex analyses to detect more complex features.

To simplify your analysis, we will only consider programs with the following
operators: `. if . else .`, `or`, `and`, `not`, `==`, `<`, `+`, `-(binary)`,
`*`, `//`, `-(unary)`, `[](index)`, `[](list initialization)`. Note that all
statements can still appear. We also will not test your code on programs that
use `nonlocal` and `global` statements, or nested assignments (`x = y = z`).
Your analysis should also not take into account overflows, but should take into
account that runtime errors (e.g. division by zero) are side-effects.

We recommend you to first implement a simple dead code analysis that only works
when expressions are constant (like `if True: ...`), and then try to extend it
with a constant analysis.

We will evaluate task 2 strictly on our test cases, contrary to the task 2 of coursework 1 where you could provide your own.

## Implementation guidelines

### Commit and push your changes to GitHub

You are encouraged to commit your changes regularly.
This allows you to track
the history of your changes so that you can revert to an earlier version of your code if you need to.
It also protects you from losing any of your work in the case of a computer failure.

Furthermore, every time you commit and push your changes in the `main` branch, your points are updated,
giving you continuous feedback on your implementation.

### Check your points

This badge shows how many successful test cases you've had so far.

 ![Points badge](../../blob/badges/.github/badges/points.svg)

These points are **provisional** and are not related to the final grade.
The number of successful test cases is only an indicator of how strong your implementation is,
with respect to how many language features it covers.
Your implementation will be tested also on other test cases,
so it is important that you write your own tests to ensure that your code is thoroughly tested.

Once you have pushed all of your changes to GitHub and you are happy with your code and your points, you're finished! We will grade your last submission on the `main` branch.
Submissions after the deadline, will result in penalties without an approved extension. See "Assessment" on Learn for details.

## Misc

Follow our academic guidelines and take advantage of Piazza to discuss any open questions.

For the following courseworks, the full lexer and parser will be provided.

### Guidelines
Please remember the good scholarly practice requirements of the University regarding work for credit.
You can find guidance at the School page:

https://web.inf.ed.ac.uk/infweb/admin/policies/academic-misconduct

This also has links to the relevant University pages.

The number of passing test cases is intended to give you an idea of the quality of the code.
However, the actual grading of your coursework takes place after the deadline and takes into account public and hidden automatic tests, as well as potential manual reviews.

Submitted code will be checked for similarity with other submissions using the MOSS system. MOSS has been effective in the past at finding similarities and it is not fooled by name changes or reordering of code blocks. Courseworks are INDIVIDUAL, and we expect everyone to turn in their sole, independent work.

Extensions: Please refer to the "Assessment" page on Learn for information on extensions.

### Questions
If you have questions, you should consult the lecture slides and recordings. If you have questions about the coursework, please start by **checking existing discussions on Piazza**. If you can't find the answer to your question, start a new discussion. It is quite possible that other students will have encountered and solved the same problem and will be able to help you. The TA will also monitor Piazza and clarify things as necessary, after allowing time for student discussion to take place.
