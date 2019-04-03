grammar minizinc;

/*
    All the comments above every rule are the definition of that rule on the Minizinc website.
    The grammar can be found at https://www.minizinc.org/doc-2.2.3/en/spec.html#full-grammar.
    Note: currently there are some typo on the grammar, but here it is correct.
    
    Where there is the ADDED comment, it means that that particular rule is not of Minizinc but it is
        something added by us.
*/

/*
    Parser Rules
*/

// ITEMS:

// <model> ::= [ <item> ";" ... ]
minizinc : (item SEMICOLON)* ;

// <item>  ::= <include-item> | <var-decl-item> | <enum-item> | <assign-item> | <constraint-item> | <solve-item> | <output-item>
//          | <predicate-item> | <test-item> | <function-item> | <annotation-item>
item : include_item | var_decl_item | enum_item | assign_item | constraint_item | solve_item | output_item | predicate_item 
     | test_item | function_item | annotation item | /*ADDED*/ weight_item | query_item ;

// <ti-expr-and-id> ::= <ti-expr> ":" <ident>
ti_expr_and_id : ti_expr COLON ident ;

// <include-item> ::= "include" <string-literal>
include_item : INCLUDE string_literal ;

// <var-decl-item> ::= <ti-expr-and-id> <annotations> [ "=" <expr> ]
var_decl_item : ti_expr_and_id annotations (EQ expr)? ;

// <enum-item>  ::= "enum" <ident> <annotations> [ "=" <enum-cases> ]
enum_item : ENUM ident annotations (EQ enum_cases)? ;

// <enum-cases> ::= "{" <ident> "," ... "}"
enum_cases : LEFT_CURLY_BRACKET ident ( COMMA ident )* RIGHT_CURLY_BRACKET ;

// <assign-item> ::= <ident> "=" <expr>
assign_item : ident EQ expr ;

// <constraint-item> ::= "constraint" <string-annotation> <expr>
constraint_item : CONSTRAINT expr ;

// <solve-item> ::= "solve" <annotations> "satisfy"
//                | "solve" <annotations> "minimize" <expr> 
//                | "solve" <annotations> "maximize" <expr>
solve_item : SOLVE annotations SATISFY | SOLVE annotations MINIMIZE expr | SOLVE annotations MAXIMIZE expr ;

// <output-item> ::= "output" <expr>
output_item : OUTPUT expr ;

// <predicate-item> ::= "predicate" <operation-item-tail>
predicate_item : PREDICATE operation_item_tail ;

// <test-item> ::= "test" <operation-item-tail>
test_item : TEST operation_item_tail ;

// <function-item> ::= "function" <ti-expr> ":" <operation-item-tail>
function_item : FUNCTION ti_expr COLON operation_item_tail ;

// <annotation-item> ::= "annotation" <ident> <params>
annotation_item : ANNOTATION ident params ;

// ADDED
weight_item : WEIGHT COLON expr ;

// ADDED
query_item : QUERY expr ;

// <operation-item-tail> ::= <ident> <params> <annotations> [ "=" <expr> ]
operation_item_tail : ident params annotations (EQ expr)? ;

// <params> ::= [ ( <ti-expr-and-id> "," ... ) ]
params : ( LEFT_ROUND_BRACKET (ti_expr_and_id (COMMA ti_expr_and_id)* )? RIGHT_ROUND_BRACKET )? ;






// Type-Inst Expressions

// <ti-expr> ::= <base-ti-expr>
ti_expr : base_ti_expr ;

// <base-ti-expr> ::= <var-par> <base-ti-expr-tail>
base_ti_expr : var_par base_ti_expr_tail ;

// <var-par> ::= "var" | "par" | ε
var_par : VAR | PAR | /* ε */ ;

// <base-type> ::= "bool" | "int" | "float" | "string"
base_type : BOOL | INT | FLOAT | STRING | ident;

// <base-ti-expr-tail> ::= <ident> | <base-type> | <set-ti-expr-tail> | <ti-variable-expr-tail> | <array-ti-expr-tail> | "ann"
//                      | "opt" <base-ti-expr-tail> | { <expr> "," ... } | <num-expr> ".." <num-expr>
base_ti_expr_tail : base_type | set_ti_expr_tail | ti_variable_expr_tail | array_ti_expr_tail
                  | ANN | OPT base_ti_expr_tail | LEFT_CURLY_BRACKET expr (COMMA expr)* RIGHT_CURLY_BRACKET
                  | num_expr DOTDOT num_expr ;
                  
// <ti-variable-expr-tail> ::= $[A-Za-z][A-Za-z0-9_]*
ti_variable_expr_tail : DOLLAR_IDENT ;

// <set-ti-expr-tail> ::= "set" "of" <base-type>
set_ti_expr_tail : SET OF base_type ;

// <array-ti-expr-tail> ::= "array" [ <ti-expr> "," ... ] "of" <ti-expr> | "list" "of" <ti-expr>
array_ti_expr_tail : ARRAY LEFT_SQUARE_BRACKET ti_expr (COMMA ti_expr)* RIGHT_SQUARE_BRACKET OF ti_expr | LIST OF ti_expr ;







// Expressions

// <expr> ::= <expr-atom> <expr-binop-tail>
expr : expr_atom 
     | expr BACKTICK ident BACKTICK expr
     | <assoc=right> expr PLUSPLUS expr
     | expr INTERSECT expr 
     | expr DIV expr | expr MOD expr | expr IDIV expr | expr MULT expr | expr MINUS expr | expr PLUS expr
     | expr DOTDOT expr
     | expr SYMDIFF expr | expr DIFF expr | expr UNION expr | expr SUPERSET expr | expr SUBSET expr | expr IN expr
     | expr NQ expr | expr EQ expr | expr EQEQ expr | expr GE expr | expr LE expr | expr GT expr | expr LT expr
     | expr AND expr | expr XOR expr | expr OR expr | expr RIMPL expr | expr IMPL expr | expr EQUIV expr ;
     
// <expr-atom> ::= <expr-atom-head> <expr-atom-tail> <annotations>
expr_atom : expr_atom_head expr_atom_tail annotations ;

// <expr-binop-tail> ::= "[" <bin-op> <expr> "]"
// Not used because if used it it will not be possibile to apply precende of operators

// <expr-atom-head> ::= <builtin-un-op> <expr-atom> | "(" <expr> ")" | <ident-or-quoted-op> | "_" | <bool-literal> | <int-literal>
//                  | <float-literal> | <string-literal> | <set-literal> | <set-comp> | <array-literal> | <array-literal-2d>
//                  | <array-comp> | <ann-literal> | <if-then-else-expr> | <let-expr> | <call-expr> | <gen-call-expr>
expr_atom_head : builtin_un_op expr_atom | LEFT_ROUND_BRACKET expr RIGHT_ROUND_BRACKET | ident | UNDERSCORE
               | bool_literal | int_literal | float_literal | string_literal | set_literal | set_comp | array_literal
               | array_literal_2d | array_comp | ann_literal | if_then_else_expr | let_expr | call_expr | gen_call_expr ;
               
// <expr-atom-tail> ::= ε | <array-access-tail> <expr-atom-tail>
expr_atom_tail : array_access_tail expr_atom_tail | /* ε */ ;

// <num-expr> ::= <num-expr-atom> <num-expr-binop-tail>
num_expr : num_expr_atom
         | num_expr BACKTICK ident BACKTICK num_expr
         | num_expr DIV num_expr | num_expr MOD num_expr | num_expr IDIV num_expr | num_expr MULT num_expr
         | num_expr MINUS num_expr | num_expr PLUS num_expr ;

// <num-expr-atom> ::= <num-expr-atom-head> <expr-atom-tail> <annotations>
num_expr_atom : num_expr_atom_head expr_atom_tail annotations ;

// <num-expr-binop-tail> ::= "[" <num-bin-op> <num-expr> "]"
// Not used because if we use it it will not be possibile to apply precende of operators

// <num-expr-atom-head> ::= <builtin-num-un-op> <num-expr-atom> | "(" <num-expr> ")" | <ident-or-quoted-op> | <int-literal>
//                       | <float-literal> | <if-then-else-expr> | <let-expr> | <call-expr> | <gen-call-expr>
num_expr_atom_head : builtin_num_un_op num_expr_atom | LEFT_ROUND_BRACKET num_expr RIGHT_ROUND_BRACKET | ident
                   | int_literal | float_literal | if_then_else_expr | let_expr | call_expr | gen_call_expr ;

// <builtin-op> ::= <builtin-bin-op> | <builtin-un-op>
// NOT USED

// <bin-op> ::= <builtin-bin-op> | ‘<ident>‘
// NOT USED

// <builtin-bin-op> ::= "<->" | "->" | "<-" | "\/" | "xor" | "/\" | "<" | ">" | "<=" | ">=" | "==" | "=" | "!="
//                    | "in" | "subset" | "superset" | "union" | "diff" | "symdiff"
//                    | ".." | "intersect" | "++" | <builtin-num-bin-op>
// NOT USED
                   
// <builtin-un-op> ::= "not" | <builtin-num-un-op>
builtin_un_op : NOT | builtin_num_un_op ;

// <num-bin-op> ::= <builtin-num-bin-op> | ‘<ident>‘
// NOT USED

// <builtin-num-bin-op> ::= "+" | "-" | "*" | "/" | "div" | "mod"
// NOT USED

// <builtin-num-un-op> ::= "+" | "-"
builtin_num_un_op : PLUS | MINUS ;

// <bool-literal> ::= "false" | "true"
bool_literal : FALSE | TRUE ;

// <int-literal> ::= [0-9]+ | 0x[0-9A-Fa-f]+ | 0o[0-7]+
int_literal : INT_DEC | INT_HEX | INT_OCT ;

// <float-literal> ::= [0-9]+.[0-9]+ | [0-9]+.[0-9]+[Ee][-+]?[0-9]+ | [0-9]+[Ee][-+]?[0-9]+
float_literal : FLOAT_VALUE | FLOAT_EXP | INT_EXP ;

// <string-contents> ::= ([^"\n\] | \[^\n(])*
// NOT USED

// <string-literal> ::= """ <string-contents> """ | """ <string-contents> "\(" <string-interpolate-tail>
string_literal : STRING_VALUE ;
               /*| STRING_INTERPOLATE_BEGIN expr string_interpolate_tail ;*/

// <string-interpolate-tail> ::= <expr> ")"<string-contents>""" | <expr> ")"<string-contents>"\(" <string-interpolate-tail>
/*string_interpolate_tail : ')' .+? '\\(' expr string_interpolate_tail 
                        | ')' .+? DOUBLE_QUOTE ; */

// <set-literal> ::= "{" [ <expr> "," ... ] "}"
set_literal : LEFT_CURLY_BRACKET ( expr ( COMMA expr )* )? RIGHT_CURLY_BRACKET ;

// <set-comp> ::= "{" <expr> "|" <comp-tail> "}"
set_comp : LEFT_CURLY_BRACKET expr PIPE comp_tail RIGHT_CURLY_BRACKET ;

// <comp-tail> ::= <generator> [ "where" <expr> ] "," ...
comp_tail : generator ( WHERE expr )? ( COMMA generator ( WHERE expr )? )* ;

// <generator> ::= <ident> "," ... "in" <expr>
generator : ident ( COMMA ident )* IN expr ;

// <array-literal> ::= "[" [ <expr> "," ... ] "]"
array_literal : LEFT_SQUARE_BRACKET ( expr ( COMMA expr )* )? RIGHT_SQUARE_BRACKET ;

// <array-literal-2d> ::= "[|" [ (<expr> "," ...) "|" ... ] "|]"
array_literal_2d : LEFT_2D_SQUARE_BRACKET ( (expr ( COMMA expr )*) PIPE ( (expr ( COMMA expr )*) )* )? RIGHT_2D_SQUARE_BRACKET ;

// <array-comp> ::= "[" <expr> "|" <comp-tail> "]"
array_comp : LEFT_SQUARE_BRACKET expr PIPE comp_tail RIGHT_SQUARE_BRACKET ;

// <array-access-tail> ::= "[" <expr> "," ... "]"
array_access_tail : LEFT_SQUARE_BRACKET expr ( COMMA expr )* RIGHT_SQUARE_BRACKET ;

// <ann-literal> ::= <ident> [ "(" <expr> "," ... ")" ]
ann_literal : ident ( LEFT_ROUND_BRACKET expr ( COMMA expr )* RIGHT_ROUND_BRACKET )? ;

// <if-then-else-expr> ::= "if" <expr> "then" <expr> [ "elseif" <expr> "then" <expr> ]* "else" <expr> "endif"
if_then_else_expr : IF expr THEN expr (ELSEIF expr THEN expr)* ELSE expr ENDIF ;

// <call-expr> ::= <ident-or-quoted-op> [ "(" <expr> "," ... ")" ]
call_expr : ident_or_quoted_op ( LEFT_ROUND_BRACKET expr ( COMMA expr )* RIGHT_ROUND_BRACKET )? ;

// <let-expr> ::= "let" "{" <let-item> ";" ... "}" "in" <expr>
let_expr : LET LEFT_CURLY_BRACKET let_item ( (SEMICOLON|COMMA) let_item )* (SEMICOLON|COMMA)? RIGHT_CURLY_BRACKET IN expr ;

// <let-item> ::= <var-decl-item> | <constraint-item>
let_item : var_decl_item | constraint_item ;

// <gen-call-expr> ::= <ident-or-quoted-op> "(" <comp-tail> ")" "(" <expr> ")"
gen_call_expr : ident_or_quoted_op LEFT_ROUND_BRACKET comp_tail RIGHT_ROUND_BRACKET LEFT_ROUND_BRACKET expr RIGHT_ROUND_BRACKET ;








// Miscellaneous Elements

// <ident> ::= [A-Za-z][A-Za-z0-9_]* | ’[^’\xa\xd\x0]*’
ident : IDENT | IDENT_QUOTED ;

// <ident-or-quoted-op> ::= <ident> | ’<builtin-op>’
ident_or_quoted_op : ident | quoted_op ;

// ADDED
quoted_op : EQUIV_QUOTED | IMPL_QUOTED | RIMPL_QUOTED | OR_QUOTED | XOR_QUOTED | AND_QUOTED
          | LT_QUOTED | GT_QUOTED | LE_QUOTED | GE_QUOTED | EQEQ_QUOTED | EQ_QUOTED | NQ_QUOTED
          | IN_QUOTED | SUBSET_QUOTED | SUPERSET_QUOTED | UNION_QUOTED | DIFF_QUOTED | SYMDIFF_QUOTED
          | DOTDOT_QUOTED | PLUS_QUOTED
          | MINUS_QUOTED | MULT_QUOTED | DIV_QUOTED | IDIV_QUOTED | MOD_QUOTED
          | INTERSECT_QUOTED | POW_QUOTED | NOT_QUOTED | COLONCOLON_QUOTED | PLUSPLUS_QUOTED ;

// <annotations> ::= [ "::" <annotation> ]*
annotations : ( COLONCOLON annotation )* ;

// <annotation> ::= <expr-atom-head> <expr-atom-tail>
annotation : expr_atom_head expr_atom_tail ;

// <string-annotation> ::= "::" <string-literal>
string_annotation : COLONCOLON string_literal ;





/*
    Lexer
*/

COMMENT : (('%' ~[\n\r]*) | ( '/*' (~[*]|[\n\r]|('*'+(~[*/]|[\n\r])))* '*'* '*/' )) -> skip;

VAR : 'var' ;
PAR : 'par' ;
WEIGHT : 'weight' ;
QUERY : 'query' ;
ABSENT : '<>' ;
ANN : 'ann' ;
ANNOTATION : 'annotation' ;
ANY : 'any' ;
ARRAY : 'array' ;
BOOL : 'bool' ;
CASE : 'case' ;
CONSTRAINT : 'constraint' ;
DEFAULT : 'default' ;
ELSE : 'else' ;
ELSEIF : 'elseif' ;
ENDIF : 'endif' ;
ENUM : 'enum' ;
FLOAT : 'float' ;
FUNCTION : 'function' ;
IF : 'if' ;
INCLUDE : 'include' ;
INFINITY : 'infinity' ;
INT : 'int' ;
LET : 'let' ;
LIST : 'list' ;
MAXIMIZE : 'maximize' ;
MINIMIZE : 'minimize' ;
OF : 'of' ;
OPT : 'opt' ;
SATISFY : 'satisfy' ;
OUTPUT : 'output' ;
PREDICATE : 'predicate' ;
RECORD : 'record' ;
SET : 'set' ;
SOLVE : 'solve' ;
STRING : 'string' ;
TEST : 'test' ;
THEN : 'then' ;
TUPLE : 'tuple' ;
TYPE : 'type' ;
UNDERSCORE : '_' ;
VARIANT_RECORD : 'variant_record' ;
WHERE : 'where' ;

TRUE : 'true' ;
FALSE : 'false' ;

LEFT_2D_SQUARE_BRACKET : '[|' ;
RIGHT_2D_SQUARE_BRACKET : '|]' ;
LEFT_SQUARE_BRACKET : '[' ;
RIGHT_SQUARE_BRACKET : ']' ;
LEFT_ROUND_BRACKET : '(' ;
RIGHT_ROUND_BRACKET : ')' ;
LEFT_CURLY_BRACKET : '{' ;
RIGHT_CURLY_BRACKET : '}' ;

QUOTE : '\'' ;
BACKTICK : '`' ;
DOUBLE_QUOTE : '"' ;
COMMA : ',' ;
COLON : ':' ;
SEMICOLON : ';' ;
PIPE : '|' ;

EQUIV_QUOTED : '\'<->\'' ;
IMPL_QUOTED : '\'->\'' ;
RIMPL_QUOTED : '\'<-\'' ;
OR_QUOTED : '\'\\/\'' ;
XOR_QUOTED : '\'xor\'' ;
AND_QUOTED : '\'/\\\'' ;
LT_QUOTED : '\'<\'' ;
GT_QUOTED : '\'>\'' ;
LE_QUOTED : '\'<=\'' ;
GE_QUOTED : '\'>=\'' ;
EQEQ_QUOTED : '\'==\'' ;
EQ_QUOTED : '\'=\'' ;
NQ_QUOTED : '\'!=\'' ;
IN_QUOTED : '\'in\'' ;
SUBSET_QUOTED : '\'subset\'' ;
SUPERSET_QUOTED : '\'superset\'' ;
UNION_QUOTED : '\'union\'' ;
DIFF_QUOTED : '\'diff\'' ;
SYMDIFF_QUOTED : '\'symdiff\'' ;
DOTDOT_QUOTED : '\'..\'' ;
PLUS_QUOTED : '\'+\'' ;
MINUS_QUOTED : '\'-\'' ;
MULT_QUOTED : '\'*\'' ;
DIV_QUOTED : '\'/\'' ;
IDIV_QUOTED : '\'div\'' ;
MOD_QUOTED : '\'mod\'' ;
INTERSECT_QUOTED : '\'intersect\'' ;
POW_QUOTED : '\'^\'' ;
NOT_QUOTED : '\'not\'' ;
COLONCOLON_QUOTED : '\'::\'' ;
PLUSPLUS_QUOTED : '\'++\'' ;

EQUIV : '<->' ;
IMPL : '->' ;
RIMPL : '<-' ;
OR : '\\/' ;
XOR : 'xor' ;
AND : '/\\' ;
LT : '<' ;
GT : '>' ;
LE : '<=' ;
GE : '>=' ;
EQEQ : '==' ;
EQ : '=' ;
NQ : '!=' ;
WEAK_EQ : '~=' ;
IN : 'in' ;
SUBSET : 'subset' ;
SUPERSET : 'superset' ;
UNION : 'union' ;
DIFF : 'diff' ;
SYMDIFF : 'symdiff' ;
DOTDOT : '..' ;
PLUS : '+' ;
MINUS : '-' ;
WEAK_PLUS : '~+' ;
WEAK_MINUS : '~-' ;
MULT : '*' ;
DIV : '/' ;
IDIV : 'div' ;
MOD : 'mod' ;
INTERSECT : 'intersect' ;
WEAK_MULT : '~*' ;
POW : '^' ;
NOT : 'not' ;
PLUSPLUS : '++' ;
COLONCOLON : '::' ;

INT_DEC : [0-9]+ ;
INT_HEX : '0x'[0-9A-Fa-f]+ ;
INT_OCT : '0o'[0-7] ;

FLOAT_VALUE : [0-9]+'.'[0-9]+ ;
FLOAT_EXP : [0-9]+'.'[0-9]+[Ee][-+]?[0-9]+ ;
INT_EXP : [0-9]+[Ee][-+]?[0-9]+ ;

IDENT_QUOTED : '\'' ~[']+ '\'' ;
DOLLAR_IDENT : '$'[A-Za-z][A-Za-z0-9_]* ;
IDENT : [A-Za-z][A-Za-z0-9_]* ;

fragment STRING_CONTENT : ( ~["\n]|'\\"' )* ;
STRING_VALUE : '"' STRING_CONTENT '"' ;

WHITESPACE : [ \t\n\r] -> skip ;
