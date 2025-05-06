[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-24ddc0f5d75046c5622901739e7c5dd533143b0c8e959d652212380cedb1ea36.svg)](https://classroom.github.com/a/vFhDeSjJ)
![BuildAndTest](../../workflows/BuildAndTest/badge.svg?branch=main) ![Points badge](../../blob/badges/.github/badges/points.svg)

# CT 2023/24 | Coursework 1 - Parsing

**Deadline:** Fri, 16.02.2024, 12:00pm  
**Instructors:** Amir Shaikhha  
**TAs:** Nikos Mavrogeorgis, Mahdi Ghorbani, Kim Stonehouse  
**Demonstrators:** Amir Khordadi, Pei Mu, Maks Kret

**Tasks:**
1. Core: Implement a ChocoPy parser
2. Expert: Add diagnostic messages for syntax errors

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

1. Set up a virtual environment for the assignment with `python3 -m venv env`.
   This creates a subdirectory called `env` in the current folder that creates an isolated version of Python.
2. Activate the virtual environment by [`source`ing](https://linuxcommand.org/lc3_man_pages/sourceh.html) the activation file: `source env/bin/activate`
3. Confirm that you are in the virtual environment by running `which python`. The output should be `/path/to/coursework/env/bin/python`.
4. Run `pip install -U -r requirements.txt` to install dependencies within the virtual environment.
5. Run `pip install -e .` to install the ChocoPy compiler as a package.
6. If you are using PyCharm, please configure PyCharm to work with the environment by following the instructions on
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
lit -v tests/parser
```

This will examine recursively all the files with valid formats inside the above directory.
The `-v` flag adds a verbose output with more information in case some tests fail.

You can also leverage the `--timeout <seconds>` flag, in order to bound the time allowed for your test cases to run.
This way you can detect if your parser loops infinitely in some test cases.

For more details on the configuration of `lit`, see `tests/lit.cfg`.
For more info on `lit` check the [online documentation](https://filecheck.readthedocs.io/en/latest/01-what-is-filecheck.html).

## Task 1 - Implement a ChocoPy parser

The goal of task 1 is to write a parser for the [ChocoPy Language](https://chocopy.org/.),
in order to obtain its Abstract Syntax Tree (AST).
To this end, you will work on two basic passes of the compiler frontend, that are given as classes:

1. `Lexer`: the lexer reads the input file as a stream of characters and transforms it into a stream of tokens. Each token represents a lexeme (i.e. a word in natural languages).
2. `Parser`: the parser consumes the tokens and determines if the input conforms to the rules of the grammar. As it examines each rule, it constructs the AST of the input program.

We provide some partial implementations of the lexer and parser.
You will have to implement the rest.
We strongly encourage you to write a recursive descent parser.
For this, we have provided utility functions in the lexer class to allow tokenization
and in the parser class to allow lookahead of tokens.
The parser also contains the minimum functionality to parse the following ChocoPy programs:

```
# An empty program
```

```python
def foo():
    pass
```

### 0. ChocoPy language
We strongly encourage you to familiarise yourself with ChocoPy before starting implementing the compiler.
The lexical structure, syntax, type rules, and semantics of the language are explained in the [reference manual](https://chocopy.org/chocopy_language_reference.pdf).
**However, the exact grammar you need to implement is described in Section 2** .
ChocoPy is designed to be a subset of Python.
It is advised that you write several programs in ChocoPy to get familiar with it, 
especially if you are not already familiar with Python. 
More importantly, this will help you create your own test suite, which will later be necessary to evaluate your compiler's progress.

Example: ChocoPy program illustrating functions, variables, and static typing (source: ChocoPy Language
reference).

```python
def is_zero(items: [int] , idx: int) -> bool:
    val: int = 0 		# Type is explicitly declared
    val = items[idx]
    return val == 0

mylist: [int] = None
mylist = [1, 0, 1]
print(is_zero(mylist,1)) 	# Prints ’True ’
```

### 1. Lexing
The file `choco/lexer.py` contains an implementation of:

* a scanner
* a tokenizer that leverages the scanner
* a lexer that uses the tokenizer
 
Do not remove the existing methods, e.g. `check` and `match`.
The tokens that your lexer recognizes are given in the `TokenKind` class.

For Linux environments, you can try the lexer functionality by running the `choco-lexer` tool (location `tools/choco_lexer.py`, but invokable also as `choco-lexer`):
```bash
cd /path/to/coursework
choco-lexer tests/parser/simple-statements/ops_coverage/single_stmt_pass.choc
./tools/choco_lexer.py tests/parser/simple-statements/ops_coverage/single_stmt_pass.choc # equivalent with the above
```

### 2. Grammar
Your next job will be to take the ChocoPy grammar expressed in EBNF form and transform it into an equivalent context-free **LL(2) grammar** .
The target grammar on which you will be working follows. 

Keywords and symbols are denoted with backquotes `` ` ` ``, 
the rest of the terminals with capital letters, and non_terminals with lowercase letters.
The brackets are used to group terms and are always followed either by: a `*` to represent a Kleene closure, a `+` for a positive closure, or a `?` for an optional group.

```
program := [var_def | func_def]* stmt* EOF
func_def := `def` ID `(` [typed_var [`,` typed_var]*]? `)` [`->` type]? `:` NEWLINE INDENT func_body DEDENT
func_body :=  [global_decl | nonlocal_decl | var_def]∗ stmt+
typed_var := ID `:` type
type := type_name | `[` type `]`
type_name := `object`
   | `int`
   | `bool`
   | `str`
global_decl := `global` ID NEWLINE
nonlocal_decl := `nonlocal` ID NEWLINE
var_def := typed_var `=` literal NEWLINE
stmt := simple_stmt NEWLINE
   | `if` expr `:` block [`elif` expr `:` block]* [`else` `:` block]?
   | `while` expr `:` block
   | `for` ID `in` expr `:` block
simple_stmt := `pass`
   | expr
   | `return` [expr]?
   | [expr `=`]+ expr
block := NEWLINE INDENT stmt+ DEDENT
literal := `None`
   | `True`
   | `False`
   | INTEGER
   | STRING
expr := cexpr
   | `not` expr
   | expr [`and` | `or`] expr
   | expr `if` expr `else` expr
cexpr := ID
   | literal
   | `[` [expr [`,` expr]*]? `]`
   | `(` expr `)`
   | index_expr
   | ID `(` [expr [`,` expr]*]? `)`
   | cexpr bin_op cexpr
   | `-` cexpr
bin_op := `+` | `-` | `*` | `//` | `%` | `==` | `!=` | `<=` | `>=` | `<` | `>` | `is`
index_expr := cexpr `[` expr `]`
```

Please note that the `simple_stmt` operator allows assignments like `-1 = 2` to be valid.
Even though our parser accepts that, it is something that will be caught later as an error in subsequent passes.
In general, at this stage, our test cases examine only the syntax of the program, not the semantics (e.g., assigning to a variable without defining it).

Also, please note that operators in ChocoPy have specific precedence and associativity rules.
These are described in the following table:

| Precedence | Operators                | Associativity  |
|------------|--------------------------|----------------|
| 1          | · if · else ·            | Right          |
| 2          | or                       | Left           |
| 3          | and                      | Left           |
| 4          | not                      | Not applicable |
| 5          | ==, !=, <, >, <=, >=, is | None           |
| 6          | +, - (binary)            | Left           |
| 7          | *, //, %                 | Left           |
| 8          | - (unary)                | Not applicable |
| 9          | []                       | Left           |

Operators that lie on the same line have the same precedence.

Also, note that the comparison operators are nonassociative.
So ChocoPy, unlike Python 3, does not allow expressions such as:
```
x < y < z
x == y > z
```

On the other hand, the conditional expression `· if · else ·` is associative.
To better understand the associativity of this ternary operator, you can treat it as a binary operator with an extra expression in the middle, that acts as a condition:

```
left-expr `if` condition `else` right-expr
```

Now, it is a binary operator that acts upon `left-expr` and `right-expr`.
And, since it is right-associative, the following:

```
expr1 `if` condition1 `else` expr2 `if` condition2 `else` expr3
```

is equivalent to:

```
expr1 `if` condition1 `else` (expr2 `if` condition2 `else` expr3)
```

Finally, "Not applicable" means that it is meaningless to talk about associativity for `not` or the unary `-`, since they are unary operators, not binary/ternary/etc.
Therefore, they don’t have both a left- and right-hand side, so we can’t talk about associativity.

 
### 3. Parser
After having transformed the grammar into a LL(2)-grammar you will have to complete the implementation of the parser.
A partial implementation of a recursive-decent parser has already been provided inside the `Parser` class of `choco/parser.py`.

In addition, the `Parser` class contains some utility methods, e.g.:

* `check(expected)` takes a variable number of expected tokens and returns whether the next tokens in the input are the same as the `expected`.
* `match(expected)` attempts to match the given `expected` tokens and consumes them, failing otherwise.

These methods are used by the parsing methods of each non-terminal to facilitate parsing.

An effective way to develop your parser would be to implement incrementally parsing subroutines for some of your grammar's non-terminals.

More specifically, the ChocoPy features for which you are required to implement parsing rules are the following:

| Feature                               | Notes                                                                                                           |
|---------------------------------------|-----------------------------------------------------------------------------------------------------------------|
| Literals and identifiers              | identifiers, integers, strings, `True`, `False`, `None`                                                         |
| Variable definitions and declarations | types, variable definitions, `global`/`nonlocal` declarations                                                   |
| Function prototypes and definitions   | typed argument list, return types, (uses parsing function for `func_def`)                                       |
| Complex expressions - I               | index expressions, lists, function calls                                                                        |
| Control flow                          | `if`, `while`, `for`                                                                                            |
| Simple statements                     | `return`, assignments, (uses parsing function for `expr`)                                                       |
| Arithmetic and comparison operators   | unary `-`, `==`, `!=`, `<=`, `>=`,`<`, `>`, `is`, `+`, `-`, `*`, `//`, `%` + right precedence and associativity |
| Logical and conditional operators     | `· if · else ·`, `and`, `or`, `not` + right precedence and associativity                                        |
| Complex expressions - II              | parenthesized expressions, mixed features                                                                       |

We recommend that you implement your parser by following the order of the table.
This will help you build your parser incrementally, by parsing more and more complex programs.

For Linux environments, you can try the current minimal parser functionality by running the `choco-opt` tool (location `tools/choco_opt.py`, but invokable also as `choco-opt`):
```bash
cd /path/to/coursework
choco-opt tests/parser/simple-statements/ops_coverage/single_stmt_pass.choc
./tools/choco_opt.py tests/parser/simple-statements/ops_coverage/single_stmt_pass.choc # equivalent with the above
```


### 4. AST

During the parsing phase, you are also expected to generate the AST of the input program.
This will be done using the API of a suitable AST dialect for ChocoPy.
You can find it in `choco/dialects/choco_ast.py`.
There, you can find python classes for every ChocoPy construct you need, along with their respective constructors.

Each class represents a node in the ChocoAST.
Each node has a distinct name, along with some optional further fields, that are either properties or regions.
You can think of an property as a property of the node itself, and the regions as groups of one or more other nodes,
that serve as the children of the node in the AST.

For example, the `BinaryExpr` class has the following fields:
```python
class BinaryExpr(IRDLOperation):
    name = "choco.ast.binary_expr"

    op: StringAttr = prop_def(StringAttr)
    lhs: Region = region_def("single_block")
    rhs: Region = region_def("single_block")
```

Moreover, the `Literal` class has the following fields:

```python
class Literal(IRDLOperation):
    name = "choco.ast.literal"

    value: StringAttr | IntegerAttr[IntegerType] | BoolAttr | NoneAttr = prop_def(
        StringAttr | IntegerAttr[IntegerType] | BoolAttr | NoneAttr
    )
```

An instance of the `BinaryExpr` is the following:

```
  "choco.ast.binary_expr"() <{"op" = "+"}> ({
    "choco.ast.literal"() <{"value" = 0 : i32}> : () -> ()
  }, {
    "choco.ast.literal"() <{"value" = 1 : i32}> : () -> ()
  }) : () -> ()
```

We can see that the identifier of the node is `"choco.ast.binary_expr"()`.
Also, we can see this node represents the operation `+`, which was the `op` property in the class fields.
Finally, this node has two regions as children, each containing one node: `lhs` and `rhs` are nodes representing literals.
Both nodes have the same name (`choco.ast.literal`), but different properties, which represent different values (`"value" = 0 : i32` and `"value" = 1 : i32` respectively).
Their values also happen to be integers of the same size (`i32`).

In general, the properties enclosed in `<{ ... }>` represent compile-time information of the operation, e.g., a literal with value 5.
And the regions `({...})` represent the nesting of operations, e.g., in the case of a while/for loop.

To see how to instantiate each class, you can examine its constructor definition (`__init__()` function) in the `choco_ast.py` file.

The AST representation when printed can be verbose, e.g., note the brackets `<{ ... }>`, the empty signature `() -> ()`, etc., but it merely reflects the fields of each AST node.
This representation will be more clear in later courseworks.
Nevertheless, the test cases have the full AST that is expected to be printed, so make sure you check against those if you are unsure about the output of your parser.

### 5. Hints

Some *hints* to guide your implementation are the following:

#### Precedence

A simple way to achieve the desired precedence for the operators is to unfold the parsing rules in a hierarchical way.

An example of how to give the multiplication operator higher precedence than of addition is this:

```
# Same precedence
E := INTEGER `+` E
   | INTEGER `*` E
   | INTEGER

# `*` has higher precedence
E := T `+` E
   | T
T := INTEGER `*` T
   | INTEGER
```

The second block of rules would parse the expression `1 + 2 * 3` as `1 + (2 * 3)`.

Therefore, in order to encode precendence in the grammar, new non-terminals have to be introduced.
We recommend that while you transform your grammar, you first introduce the necessary non-terminals to reflect the precedence, before encoding the correct associativity or eliminating the left recursion.

#### Associativity

Getting the correct associativity can be implemented with the correct rule definition:

```
# `+` is right associative
E := T `+` E
   | T

# `+` is left associative
E := E `+` T  # Be aware of left recursion!
   | T
```

#### Left recursion elimination

The aforementioned example has left recursion:

```
E := E `+` T
   | T
```

As you have learned on the lectures, this can be eliminated by introducing a new auxiliary non-terminal `E_aux`:

```
    E := T E_aux
E_aux := `+` T E_aux
       | epsilon
```

As mentioned in the lectures, this is equivalent with:

```
E := T (`+` T)*
```

Therefore, in order to remove left recursion, you have two implementation options:

1. Introduce a new non-terminal and create an additional parsing function:

```python
def parse_E():
    parse_T()
    parse_E_aux()

def parse_E_aux():
    if check(PLUS):
        match(PLUS)
        parse_T()
        parse_E_aux()
```

2. Parse the Kleene closure, without introducing a new non-terminal:

```python
def parse_E():
    parse_T()
    while (check(PLUS)):
        match(PLUS)
        parse_T()
```

Both implementations are equivalent.


#### Implementing `elif`

The `elif` logic is essentially syntactic sugar for nested `if` statements, so you need to remove the `elif` when you create the AST.

The following code:

```
if {expr1}:
    {body1}
elif {expr2}:
    {body2}
elif {expr3}:
    {body3}
```

is equivalent to:

```
if {expr1}:
    {body1}
else:
    if {expr2}:
        {body2}
    else:
        if {expr3}:
            {body3}
```
#### First Sets auxiliary functions

You can make use of the `is_expr_first_set` and `is_stmt_first_set` functions.
These functions have only one token as lookahead.
Their purpose is to return true if the next token belongs to the First set of expressions and statements respectively.
Let's focus on `is_expr_first_set`.

In the lectures, it has been discussed that the First set of `α ∈ N | T`, is the set of terminals that appear first in some string that derives from `α`.
So, the First set of the `expr` nonterminal is the set of all the possible terminals that can be "first" in a string produced by `expr`.

For example, there is a rule ``expr -> `not` expr``.
This means that this rule can produce something like `not (x+y)`, or `not 3`, or many other strings that start with `not` and are followed by an expression.
The common characteristic of all these strings is that they begin with `not`.
That's why we say that `` `not` `` belongs to the First set of `expr`.

Also, there is a rule `expr -> cexpr`, which can be expanded to ``expr -> `(` expr `)``.
This rule can produce things like `(x + y)`, `(3)`, `((not True))`.
 The common characteristic of all these strings is that they begin with `(`.
That's why we say that the left round bracket `` `(` `` belongs to the First set of `expr`.

So far, we have found two terminals of the expression First set, and there are more.

The method `is_expr_first_set` just looks at the next token and tells you whether it belongs to the First set of `expr`.
For example, it would return true if the next token is `not` or `(` (and for some others also), but would return false for `)`.

The purpose of this function is to just help with your code, in case you need to check if the next token belongs to the First set of `expr`.
Instead of having to check:

```
if self.check(TokenKind.NOT) or self.check(TokenKind.LROUNDBRACKET) or ... :
    ....
```

you can call the `is_expr_first_set`.

It is not necessary to use it, but mostly for convenience and as a "hint" that at some point you may need it.
The same applies to `is_stmt_first_set`.

#### Hint on grading

Task 1 is the central task. If executed flawlessly you should be able to attain an excellent (A3) grade.

## Task 2 - Add diagnostic messages for syntax errors

The goal of task 2 is to modify the given lexer and extend the parser you implemented in task 1,
in order to add syntax error handling.

To this end, you need to understand the internals of the `Scanner`, `Tokenizer` and `Lexer` classes.
You also need to extend your parser with the necessary syntax error recovery mechanisms.

The main idea is that for every syntax error your parser encounters, it should catch it and print helpful information on
the error in the form of a message:
```
SyntaxError (line <row number>, column <column number>): <message>
>>>erroneous source line
>>>visual pointer to the line
```

For example, consider the following program which should give a syntax error:

```python
  for i [1,2]
    pass
```

The `in` token is missing, so the expected message would need to be of the form:

```
# CHECK-NEXT: SyntaxError (line 1, column 9): token of kind TokenKind.IN not found.
# CHECK-NEXT: >>>  for i [1,2]
# CHECK-NEXT: >>>--------^
```

Things to notice here:
* In the 1st line we see that the error occurs in line number 1.
* In the 1st line we see that the error occurs in column number 9, i.e. where we found `[` while expecting `in`.
* In the 1st line we see the message is informing that the token `TokenKind.IN` was not found.
* The second line starts with `>>>`.
* The second line continues with exactly the full line of the source code where the error was, i.e. `  for i [1,2]`.
* The source code line is printed until the end of line, i.e. the parser doesn't stop, until it finds the `NEWLINE` token.
* The source code line is printed with all the trailing spaces in the beginning (2 spaces in the example).
* The third line starts with `>>>`.
* The 3rd line uses hyphens (`-`) followed by a caret (`^`) to point to the error that happened.
* The hyphens start at column `1`, relative to the source code line, and end right before the caret.
* The caret points right at column `9`, relative to the source code line, where the first character of the wrong token occurred.

You need to extend your lexer to provide location information, which will be used to print the location of the syntax error.
Also, you need to extend your parser to catch the following syntax errors:

| Error | Message |
| --- | --- |
| Unmatched token | token of kind \<expected\> not found. |
| Wrong indentation | Unexpected indentation. |
| Missing comma in a parameter/expression list | expression found, but comma expected. |
| Function without at least one properly indented statement | expected at least one indented statement in function. |
| Wrong type | Unknown type. |
| Block without at least one properly indented statement | expected at least one indented statement in block. |
| Empty left-hand side in assignment | No left-hand side in assign statement. |
| Expression missing in statement | Expected expression. |
| Declaring a variable among a statement sequence | Variable declaration after non-declaration statement. |
| Right round bracket with no left counterpart | unmatched ')'. |
| Chain of comparison operators | Comparison operators are not associative. |

When your parser catches the above errors, it should print the respective messages, with the format described before.
Hint: to make testing easier choco-opt should return with a zero exit code even if an error is found.

#### Deciding which message to print

In general, when you are sure about the token you expect, and you encounter something else, we expect you to give the `token of kind <expected> not found` message.
For example, there must always be a `:` after `)` in function definition.

That said, there are cases where you don’t know necessarily what token should follow, but you know what tokens *shouldn't* follow.
For example, when you have `foo(x` , you don’t necessarily expect `)` after x, because also a `,` could follow.
But, if you see another expression, e.g., `y`, then the string `foo(x y` has definitely a syntax error.
And since there are two expressions, the parser assumes that a comma is missing between these two.

It could also assume that `)` should be there, instead of `y`, but that isn’t very likely as an error from a programmer’s perspective, and the error messages' purpose is to help pinpoint the most probable root cause of the error.
So it can help the programmer amend it.

As another example, consider the code:

```python
if True:
    pass
    else:   <--- syntax error here
        pass
```

The `if` statement is followed by a block. Blocks should end with `DEDENT`.
Now, the parser encounters `else` before a `DEDENT` is found, so `token of kind TokenKind.DEDENT not found` is a reasonable error to output.

However, in this example:

```python
if True:
    pass
        else:   <--- syntax error here
        pass
```

Now, the parser encounters specifically `INDENT` before a `DEDENT` was found, so `Unexpected indentation.` is a reasonable error to output, as a more specific kind of error.

You can find more details on what the syntax errors look like and what is the expected behavior of your parser in `tests/parser/syntax-errors`.

Hint on grading: Task 2 is -- by design -- less documented, touches larger
parts of the compiler, and is overall expected to be more difficult. Solving
this task is seen as highly exceptional. If you feel you went even beyond what
is expected in Task 2, please put at most five new test cases of less than
50 lines each into `tests/parser/syntax-errors/outstanding-parsing-errors` that
demonstrate additional outstanding features your parser provides.


## Implementation guidelines

###  Commit and push your changes to GitHub

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
Your parser will be tested also on other test cases,
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
