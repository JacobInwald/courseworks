from typing import List, Union
from xdsl.dialects.builtin import ModuleOp
from xdsl.ir import Operation

import choco.dialects.choco_ast as ast
from choco.lexer import Lexer, Token, TokenKind

class Parser:
    """
    A Simple ChocoPy Parser

    Parse the given tokens from the lexer and call the xDSL API to create an AST.
    """

    def __init__(self, lexer: Lexer):
        """
        Create a new parser.

        Initialize parser with the corresponding lexer.
        """
        self.lexer = lexer

    def check(self, expected: Union[List[TokenKind], TokenKind]) -> bool:
        """
                Check that the next token is of a given kind. If a list of n TokenKinds
                is given, check that the next n TokenKinds match the next expected
                ones.

                :param expected: The kind of the token we expect or a list of expected
                                 token kinds if we look ahead more than one token at
                                 a time.
                :returns: True if the next token has the expected token kind, False
        ￼                 otherwise.
        """

        if isinstance(expected, list):
            tokens = self.lexer.peek(len(expected))
            assert isinstance(tokens, list), "List of tokens expected"
            return all([tok.kind == type_ for tok, type_ in zip(tokens, expected)])

        token = self.lexer.peek()
        assert isinstance(token, Token), "Single token expected"
        return token.kind == expected

    def match(self, expected: TokenKind) -> Token:
        """
        Match a token by first checking the token kind. In case the token is of
        the expected kind, we consume the token.  If a token with an unexpected
        token kind is encountered, an error is reported by raising an
        exception.

        The exception shows information about the line where the token was expected.

        :param expected: The kind of the token we expect.
        :returns: The consumed token if the next token has the expected token
                  kind, otherwise a parsing error is reported.
        """
        if self.check(expected):
            token = self.lexer.peek()
            assert isinstance(token, Token), "A single token expected"
            self.lexer.consume()
            return token
        
        token = self.lexer.peek()
        assert isinstance(token, Token), "A single token expected"
        
        if token.kind == TokenKind.INDENT:
            print(self.error(f'Unexpected indentation.'))
        elif token.kind == TokenKind.RROUNDBRACKET:
            print(self.error('unmatched \')\'.'))
        elif token.kind == TokenKind.ASSIGN:
            print(self.error('No left-hand side in assign statement.'))
        elif self.is_decl_token(token) and expected == TokenKind.NEWLINE:
            print(self.error('Variable declaration after non-declaration statement.'))
        else:    
            print(self.error(f'token of kind {expected} not found.'))
        exit(0)
    
    def error(self, error_message: str, token: Token = None) -> str:
        """
        Construct an error message.
        """
        token = self.lexer.peek() if token is None else token
        
        msg = f"SyntaxError (line {token.pos[0]}, column {token.pos[1]}): {error_message}\n"
        msg += f">>>{self.lexer.tokenizer.get_token_line(token)}\n"
        msg += f">>>{''.join(['-' for _ in range(token.pos[1] - 1)])}^"
        return msg
        
    def parse_program(self) -> ModuleOp:
        """
        Parse a ChocoPy program.

        program ::= def_seq stmt_seq EOF

        :returns: The AST of a ChocoPy Program.
        """
        defs = self.parse_def_seq()
        stmts = self.parse_stmt_seq()
        # self.match(TokenKind.EOF)
        return ModuleOp([ast.Program(defs, stmts)])

    # Literals and Types
    
    def parse_literal(self) -> Operation:
        """Parse a literal.

        literal := INTEGER | STRING | `None` | `True` | `False`
        """
        token = self.lexer.peek()
        if token.kind in [TokenKind.INTEGER, TokenKind.STRING, TokenKind.NONE, TokenKind.TRUE, TokenKind.FALSE]:
            self.match(token.kind)
            match(token.kind):
                case TokenKind.NONE:
                    return ast.Literal(None)
                case TokenKind.TRUE:
                    return ast.Literal(True)
                case TokenKind.FALSE:
                    return ast.Literal(False)
                case _:
                    return ast.Literal(token.value)
        print(self.error('Unknown literal.'))
        exit(0)
    
    def parse_type(self) -> Operation:
        """Parse a type.

        type := `object` | `int` | `bool` | `str`

        """
        token = self.lexer.peek()
        if token.kind in [TokenKind.OBJECT, TokenKind.INT, TokenKind.BOOL, TokenKind.STR]:
            self.match(token.kind)
            return ast.TypeName(token.value)

        # Parse List Types
        if token.kind == TokenKind.LSQUAREBRACKET:
            self.match(token.kind)
            type = self.parse_type()
            self.match(TokenKind.RSQUAREBRACKET)
            return ast.ListType(type)
        
        print(self.error('Unknown type.'))
        exit(0)
    
    # Variable Declarations
    
    def parse_global_decl(self) -> Operation:
        """
        Parse a global variable definition.

        global_var_def := `global` ID NEWLINE

        """
        self.match(TokenKind.GLOBAL)
        var_name = self.match(TokenKind.IDENTIFIER)
        self.match(TokenKind.NEWLINE)

        return ast.GlobalDecl(var_name.value)
    
    def parse_nonlocal_decl(self) -> Operation:
        """
        Parse a nonlocal variable definition.

        nonlocal_var_def := `nonlocal` ID NEWLINE

        """
        self.match(TokenKind.NONLOCAL)
        var_name = self.match(TokenKind.IDENTIFIER)
        self.match(TokenKind.NEWLINE)

        return ast.NonLocalDecl(var_name.value)
    
    def parse_typed_var(self) -> Operation:
        """
        Parse a variable definition.

        var_def := ID `:` type NEWLINE

        """
        var_name = self.match(TokenKind.IDENTIFIER)
        self.match(TokenKind.COLON)
        var_type = self.parse_type()
        return ast.TypedVar(var_name.value, var_type)
    
    def parse_var_def(self) -> Operation:
        """
        Parse a variable definition.

        var_def := typed_var `=` literal NEWLINE | typed_var NEWLINE
        """
        
        # ? typed_var `=` literal NEWLINE
        var_name = self.parse_typed_var()
        if self.check(TokenKind.NEWLINE):
            self.match(TokenKind.NEWLINE)
            return var_name
        
        # ? typed_var `=` literal NEWLINE
        self.match(TokenKind.ASSIGN)
        literal = self.parse_literal()
        self.match(TokenKind.NEWLINE)
        
        return ast.VarDef(var_name, literal)
    
    # Declaration Sequence
    
    def parse_def(self) -> Operation:
        e1, e2 = self.lexer.peek(2)
        match(e1.kind, e2.kind):
            case TokenKind.DEF, _:
                return self.parse_function()
            case TokenKind.GLOBAL, _:
                return self.parse_global_decl()
            case TokenKind.NONLOCAL, _:
                return self.parse_nonlocal_decl()
            case TokenKind.IDENTIFIER, TokenKind.COLON:
                return self.parse_var_def()
        return None
    
    def parse_def_seq(self) -> List[Operation]:
        """
        Parse a sequence of function and variable definitions.

        def_seq ::= [func_def | var_def]*

        :returns: A list of function and variable definitions.
        """

        defs: List[Operation] = []
        while self.lexer.peek().kind in [TokenKind.DEF, TokenKind.GLOBAL, TokenKind.NONLOCAL, TokenKind.IDENTIFIER]:
            d = self.parse_def()
            if d is None:
                break
            defs.append(d)
        return defs

    # Function Definitions
    
    def parse_typed_var_list(self) -> List[Operation]:
        """
        Parse a list of typed variables.

        typed_var_list := typed_var [`,` typed_var]*

        :returns: A list of typed variables.
        """
        typed_vars: List[Operation] = []
        while self.check(TokenKind.IDENTIFIER):
            typed_vars.append(self.parse_typed_var())
            if self.check(TokenKind.COMMA):
                self.match(TokenKind.COMMA)
            else:
                break
        return typed_vars
    
    def parse_function(self) -> Operation:
        """
        Parse a function definition.

            func_def := `def` ID `(` [typed_var [`,` typed_var]*]? `)` [`->` type]? `:` NEWLINE INDENT func_body DEDENT  <- point to improve
            func_body :=  def_seq stmt+

        :return: Operation
        """
        self.match(TokenKind.DEF)
        # ? Function Name
        function_name = self.match(TokenKind.IDENTIFIER)
        
        # ! Syntax Error: Non-closed function definition
        if not self.check(TokenKind.LROUNDBRACKET):
            print(self.error('token of kind TokenKind.LROUNDBRACKET not found.'))
            exit(0)
        self.match(TokenKind.LROUNDBRACKET)

        # ! Function Parameters
        parameters: List[Operation] = []
        parameter_types: List[Operation] = []
        
        while self.check(TokenKind.IDENTIFIER):
            parameters.append(self.parse_typed_var()) # Parse a typed variable
            
            if self.check(TokenKind.COMMA):
                self.match(TokenKind.COMMA)
            else:
                break
         
        # ! Syntax Error: Comma expected   
        if self.check(TokenKind.IDENTIFIER):
            print(self.error('expression found, but comma expected.'))
            exit(0)

        self.match(TokenKind.RROUNDBRACKET)

        # ? Return type: default is <None>.
        return_type = ast.TypeName('<None>')
        if self.check(TokenKind.RARROW):
            self.match(TokenKind.RARROW)
            return_type = self.lexer.peek().kind
            return_type = ast.TypeName(self.match(return_type).value)
        
        # ? Function Body
        
        self.match(TokenKind.COLON)
        self.match(TokenKind.NEWLINE)
        
        # ? Syntax Error: Expected an indented block
        if not self.check(TokenKind.INDENT):
            print(self.error('expected at least one indented statement in function.', self.lexer.peek()))
            exit(0)
            
        self.match(TokenKind.INDENT)
        
        # ! Definitions and Declarations
        defs_and_decls: List[Operation] = [ast.TypedVarDef(p, t) for p, t in zip(parameters, parameter_types)]
        for d in self.parse_def_seq():
            defs_and_decls.append(d)
        # ? Statements
        stmt_seq = self.parse_stmt_seq()
        self.match(TokenKind.DEDENT)
        
        # ! Syntax Error: Expected an indented block
        if not stmt_seq:
            print(self.error('expected at least one indented statement in function.'))
            exit(0)
        
        # Combine the definitions, declarations and statements to form the function body
        func_body = defs_and_decls + stmt_seq

        return ast.FuncDef(function_name.value, parameters, return_type, func_body)
    
    # Statement Sequences
    
    def parse_stmt_seq(self) -> List[Operation]:
        """
        Parse a sequence of statements.

        stmt_seq ::= stmt*
        """
        stmts: List[Operation] = []
        while self.lexer.peek().kind not in [TokenKind.NEWLINE, TokenKind.EOF, TokenKind.DEDENT]:
            stmt = self.parse_stmt()
            stmts.append(stmt)
            
        return stmts
    
    def parse_block(self) -> Operation:
        """
        Parse a block.

        block := INDENT stmt_seq DEDENT
        """
        self.match(TokenKind.NEWLINE)
        # ! Syntax Error: Expected an indented block
        if not self.check(TokenKind.INDENT):
            print(self.error('expected at least one indented statement in block.'))
            exit(0)
        
        self.match(TokenKind.INDENT)
        stmt_seq = self.parse_stmt_seq()
        self.match(TokenKind.DEDENT)
        return stmt_seq
    
    # Statements

    # ! not done
    
    def parse_stmt(self) -> Operation:
        """Parse a statement.

        stmt := simple_stmt NEWLINE
                | if_stmt
                | `while` expr `:` block
                | `for` ID `in` expr `:` block
        """
        t = self.lexer.peek().kind
        match(t):
            case TokenKind.IF:
                return self.parse_if_stmt()
            case TokenKind.WHILE:
                self.match(TokenKind.WHILE)
                cond = self.parse_expr()
                self.match(TokenKind.COLON)
                block = self.parse_block()
                return ast.While(cond, block)
            case TokenKind.FOR:
                self.match(TokenKind.FOR)
                var = self.match(TokenKind.IDENTIFIER)
                self.match(TokenKind.IN)
                iterable = self.parse_expr()
                self.match(TokenKind.COLON)
                block = self.parse_block()
                return ast.For(var.value, iterable, block)
            case _:
                stmt = self.parse_simple_stmt()
                self.match(TokenKind.NEWLINE)
                return stmt
    
    def parse_if_stmt(self, start_token=TokenKind.IF) -> Operation:
        """
        Parse an if statement.
        if_stmt := `if` expr `:` block [`elif` expr `:` block]* [`else` `:` block]? <- point to improve
        """
        self.match(start_token)
        if start_token != TokenKind.ELSE:
            cond = self.parse_expr()
        self.match(TokenKind.COLON)
        block = self.parse_block()
        if self.lexer.peek().kind in [TokenKind.ELIF, TokenKind.ELSE]:
            return ast.If(cond, block, orelse=[self.parse_if_stmt(self.lexer.peek().kind)])
        else:
            return ast.If(cond, block, orelse=[])

    # ! not done
    def parse_simple_stmt(self) -> Operation:
        """Parse a simple statement.

        simple_stmt := `pass`
                    | expr
                    | `return` [expr]?
                    | [expr `=`]+ expr <- implement correctly
        """
        t = self.lexer.peek().kind
        match(t):
            case TokenKind.PASS:
                self.match(t)
                return ast.Pass()
            case TokenKind.RETURN:
                self.match(TokenKind.RETURN)
                if self.check(TokenKind.NEWLINE):
                    return ast.Return(None)
                return ast.Return(self.parse_expr())
            
        e = self.parse_expr()
        
        # while self.check(TokenKind.ASSIGN):
        #     self.match(TokenKind.ASSIGN)
        #     e = ast.Assign(e, self.parse_expr())
            
        return e

    # Parse Expressions
    
    def parse_expr_terminal(self) -> Operation:
        """
        expr_terminal := cexpr
                        | cexpr bin_op cexpr
                        | `not` expr
        """
        
        if self.check(TokenKind.NOT):
            t = self.match(TokenKind.NOT)
            return ast.UnaryExpr(t.value, self.parse_expr())
        
        e1 = self.parse_cexpr()
        
        if self.lexer.peek().kind in [TokenKind.PLUS, TokenKind.MINUS, TokenKind.MUL, TokenKind.DIV, TokenKind.MOD, \
                TokenKind.LT, TokenKind.GT, TokenKind.LE, TokenKind.GE, TokenKind.EQ, \
                TokenKind.NE, TokenKind.IS]:
                e1 = self.parse_bin_op(e1)
        
        return e1

    def parse_or(self, e1) -> Operation:
        """Parse a binary boolean operation.

        or := `or`
        """
        if e1 is None:
            e1 = self.parse_and()
        op = self.lexer.peek().kind
        
        if op == TokenKind.OR:
            op = self.match(op)
            e2 = self.parse_and()
            return ast.BinaryExpr(op.value, e1, e2)
        
        return self.parse_and(e1)
    
    def parse_and(self, e1=None) -> Operation:
        """Parse a binary boolean operation.

        and := `and`
        """
        if e1 is None:
            e1 = self.parse_expr_terminal()
            
        op = self.lexer.peek().kind
        if op == TokenKind.AND:
            op = self.match(op)
            e2 = self.parse_expr_terminal()
            return ast.BinaryExpr(op.value, e1, e2)
        
        return e1
        
    def parse_bool_op(self, e1) -> Operation:
        """Parse a binary boolean operation.

        bin_bool_op := `and` | `or`
        """
        
        op = self.lexer.peek().kind
        while op in [TokenKind.OR, TokenKind.AND]:
            e1 = self.parse_or(e1)
            op = self.lexer.peek().kind
        return e1
        
    def parse_expr(self) -> Operation:
        """Parse an expression.

            expr := expr_terminal
                    | expr_terminal bool_op_expr
                    | expr `if` expr `else` expr <-- point to improve
            """
        
        e1 = self.parse_expr_terminal()
        
        if self.lexer.peek().kind in [TokenKind.OR, TokenKind.AND]:
            e1 = self.parse_bool_op(e1)
            
        if self.lexer.peek().kind == TokenKind.IF:
            self.match(TokenKind.IF)
            body = e1
            cond = self.parse_expr()
            self.match(TokenKind.ELSE)
            orelse = self.parse_expr()
            return ast.IfExpr(cond, body, orelse)
        
        if self.lexer.peek().kind == TokenKind.ASSIGN:
            self.match(TokenKind.ASSIGN)
            return ast.Assign(e1, self.parse_expr())
        
        return e1
    
    # ! parse cexpr
    
    def parse_call(self, id: Token):
        id = id.value
        self.match(TokenKind.LROUNDBRACKET)
        args = []
        if not self.check(TokenKind.RROUNDBRACKET):
            args = [self.parse_expr()]
            while self.check(TokenKind.COMMA):
                self.match(TokenKind.COMMA)
                args.append(self.parse_expr())
        # ! Syntax Error: Comma expected 
        if not self.check(TokenKind.RROUNDBRACKET) and not (self.check(TokenKind.NEWLINE) or self.check(TokenKind.EOF)):
            print(self.error('expression found, but comma expected.'))
            exit(0)  
        self.match(TokenKind.RROUNDBRACKET)
        return ast.CallExpr(id, args)
    
    def parse_index_expr(self, c) -> Operation:
        """Parse an index expression.

        index_expr := cexpr `[` expr `]` 
                    | index_expr `[` expr `]`
        """
        # Index Expression
        self.match(TokenKind.LSQUAREBRACKET)
        i = self.parse_expr()
        self.match(TokenKind.RSQUAREBRACKET)
        expr = ast.IndexExpr(c, i)
        # Check if recurring index expressions
        if self.check(TokenKind.LSQUAREBRACKET):
            return self.parse_index_expr(expr)
        else:
            return expr
    
    def parse_simple_cexpr(self) -> Operation:
        """ cexpr := ID
                | literal
                | `[` [expr [`,` expr]*]? `]`
                | `(` expr `)`
                | ID `(` [expr [`,` expr]*]? `)`
                | `-` cexpr
        """
        
        token = self.lexer.peek().kind
        match(token):
            # ? Literal Expressions
            case TokenKind.INTEGER | TokenKind.STRING | TokenKind.NONE | TokenKind.TRUE | TokenKind.FALSE:
                return self.parse_literal()
            # ? ID
            case TokenKind.IDENTIFIER:
                token = self.match(token)
                if self.check(TokenKind.LROUNDBRACKET):
                    return self.parse_call(token)
                return ast.ExprName(token.value)
            # ? Unary Expressions
            case TokenKind.MINUS:
                token = self.match(token)
                return ast.UnaryExpr(token.value, self.parse_cexpr())
            # ? Parenthesized Expressions
            # ? `(` expr `)`
            case TokenKind.LROUNDBRACKET:
                self.match(token)
                token = self.parse_expr()
                if not self.check(TokenKind.RROUNDBRACKET):
                    print(self.error('unmatched \'(\'.'))
                self.match(TokenKind.RROUNDBRACKET)
                return token
            # ? List Expressions
            # ? `[` [expr [`,` expr]*]? `]`
            case TokenKind.LSQUAREBRACKET:
                token = self.match(token)
                elems = []
                if not self.check(TokenKind.RSQUAREBRACKET):
                    elems = [self.parse_expr()]
                    while self.check(TokenKind.COMMA):
                        self.match(TokenKind.COMMA)
                        elems.append(self.parse_expr())
                # ! Syntax Error: Comma expected
                if not self.check(TokenKind.RSQUAREBRACKET) and \
                    not (self.check(TokenKind.NEWLINE) or self.check(TokenKind.EOF)):
                    print(self.error('expression found, but comma expected.'))
                    exit(0)  
                self.match(TokenKind.RSQUAREBRACKET)
                return ast.ListExpr(elems)
            # ! Syntax Error: Unexpected indentation
            case TokenKind.INDENT:
                    t = self.match(TokenKind.INDENT)
                    print(self.error('Unexpected indentation.', t))
                    exit(0)
            # ! Syntax Error: Unexpected indentation
            case TokenKind.ASSIGN:
                    t = self.match(TokenKind.ASSIGN)
                    print(self.error('No left-hand side in assign statement.', t))
                    exit(0)
            # ! Syntax Error: Expected expression 
            case _:
                t = self.match(token)
                print(self.error('Expected expression.', t))
                exit(0)
    
    def parse_cexpr(self) -> Operation:
        """Parse an expression.

        cexpr := simple_cexpr
                | index_expr
        """
        
        e1 = self.parse_simple_cexpr()
        t = self.lexer.peek().kind
        match(t):
            case TokenKind.LSQUAREBRACKET:
                return self.parse_index_expr(e1)
            
        return e1
       

    # ! Binary Operations (with) precedence
    
    def parse_bin_op_prec_5(self, e1=None) -> Operation:
        """
        Parse a binary operation with precedence 5.

        binop_prec_5 := `==` | `!=` | `<` | `>` | `<=` | `>=` | `is`
        """
        if e1 is None:
            e1 = self.parse_bin_op_prec_6()
        op = self.lexer.peek().kind
        if op not in [TokenKind.EQ , TokenKind.NE , TokenKind.LT , TokenKind.GT , TokenKind.LE , TokenKind.GE , TokenKind.IS]:
            return self.parse_bin_op_prec_6(e1)
        else:
            op = self.match(op)
            e2 = self.parse_bin_op_prec_6()
            e1 = ast.BinaryExpr(op.value, e1, e2)
            if self.is_comparison(op.value) and self.is_comparison(self.lexer.peek().value):
                print(self.error('Comparison operators are not associative.', self.lexer.peek()))
                exit(0)
            return e1
     
    def parse_bin_op_prec_6(self, e1=None) -> Operation:
        """
        Parse a binary operation with precedence 6.

        binop_prec_5 := `+` | `-`
        """
        if e1 is None:
            e1 = self.parse_bin_op_prec_7()
        op = self.lexer.peek().kind
        if op not in [TokenKind.PLUS, TokenKind.MINUS]:
            return self.parse_bin_op_prec_7(e1)
        else:
            op = self.match(op)
            e2 = self.parse_bin_op_prec_7()
            return ast.BinaryExpr(op.value, e1, e2)
    
    def parse_bin_op_prec_7(self, e1=None) -> Operation:
        """
        Parse a binary operation with precedence 7.

        binop_prec_5 := `*` | `/` | `%`
        """
        if e1 is None:
            e1 = self.parse_cexpr()
        op = self.lexer.peek().kind
        if op not in [TokenKind.MUL, TokenKind.DIV , TokenKind.MOD]:
            return e1
        else:
            op = self.match(op)
            e2 = self.parse_cexpr()
            return ast.BinaryExpr(op.value, e1, e2)
     
    def parse_bin_op(self, e1) -> Operation:
        """
        Parse a binary operation.
        
        binop := `+` | `-` | `*` | `/` | `%` | `==` | `!=` | `<` | `>` | `<=` | `>=` | `is`
        
        :param e1: The left-hand side expression.
        """
        
        op = self.lexer.peek().kind
        while op in [TokenKind.PLUS, TokenKind.MINUS, TokenKind.MUL, TokenKind.DIV , TokenKind.MOD , \
                     TokenKind.LT , TokenKind.GT , TokenKind.LE , TokenKind.GE , TokenKind.EQ , \
                         TokenKind.NE , TokenKind.IS]:
            e1 = self.parse_bin_op_prec_5(e1)
            op = self.lexer.peek().kind
        return e1
    
    # ? HELPERS
        
    def is_decl_token(self, token: Token) -> bool:
        """Check if a token is a declaration token."""
        return token.kind in [TokenKind.DEF, TokenKind.GLOBAL, TokenKind.NONLOCAL, TokenKind.COLON]
    
    def get_precendence(self, op: str) -> int:
        """Get the precedence of an operator."""
        return {
            'or': 1,
            'and': 2,
            '==': 3,
            '!=': 3,
            '<': 3,
            '>': 3,
            '<=': 3,
            '>=': 3,
            '+': 4,
            '-': 4,
            '*': 5,
            '/': 5,
            '%': 5,
        }.get(op, 0)   
    
    def is_comparison(self, op: str) -> bool:
        """Check if an operator is a comparison operator."""
        return op in ['==', '!=', '<', '>', '<=', '>=']
    
    def is_associative(self, op: str) -> bool:
        """Check if an operator is associative."""
        return op in ['+', '-', '*', '/']