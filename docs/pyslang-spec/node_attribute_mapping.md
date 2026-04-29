# 节点属性映射表

> 基于实际 pyslang AST 探索生成
> 2026-04-29

## 说明

每个 SyntaxKind 节点都有一组属性。以下是实际解析中遇到的节点类型及其属性。

## 重要节点属性映射

### 声明类

| SyntaxKind | 属性 |
|------------|------|
| `ModuleDeclaration` | attributes, blockName, endmodule, header, kind, members, parent, sourceRange |
| `ClassDeclaration` | attributes, classKeyword, endBlockName, endClass, extendsClause, finalSpecifier, implementsClause, items, kind, name, parameters, parent |
| | ... +3 more |
| `FunctionDeclaration` | attributes, end, endBlockName, items, kind, parent, prototype, semi, sourceRange |
| `ConstraintDeclaration` | attributes, block, keyword, kind, name, parent, qualifiers, sourceRange, specifiers |
| `DataDeclaration` | attributes, declarators, kind, modifiers, parent, semi, sourceRange, type |

### 端口/连接类

| SyntaxKind | 属性 |
|------------|------|
| `FunctionPortList` | closeParen, kind, openParen, parent, ports, sourceRange |
| `FunctionPort` | attributes, constKeyword, dataType, declarator, direction, kind, parent, sourceRange, staticKeyword, varKeyword |
| `AnsiPortList` | closeParen, kind, openParen, parent, ports, sourceRange |
| `ImplicitAnsiPort` | attributes, declarator, header, kind, parent, sourceRange |
| `VariablePortHeader` | constKeyword, dataType, direction, kind, parent, sourceRange, varKeyword |

### 语句类

| SyntaxKind | 属性 |
|------------|------|
| `ReturnStatement` | attributes, kind, label, parent, returnKeyword, returnValue, semi, sourceRange |
| `ExpressionStatement` | attributes, expr, kind, label, parent, semi, sourceRange |
| `AlwaysBlock` | attributes, keyword, kind, parent, sourceRange, statement |
| `AlwaysKeyword` | isMissing, isOnSameLine, kind, location, range, rawText, trivia, value, valueText |
| `TimingControlStatement` | attributes, kind, label, parent, sourceRange, statement, timingControl |
| `SequentialBlockStatement` | attributes, begin, blockName, end, endBlockName, items, kind, label, parent, sourceRange |
| `ConditionalStatement` | attributes, closeParen, elseClause, ifKeyword, kind, label, openParen, parent, predicate, sourceRange |
| `CaseStatement` | attributes, caseKeyword, closeParen, endcase, expr, items, kind, label, matchesOrInside, openParen |

### 约束/类 成员

| SyntaxKind | 属性 |
|------------|------|
| `ClassDeclaration` | attributes, classKeyword, endBlockName, endClass, extendsClause, finalSpecifier, implementsClause, items, kind, name |
| `ClassKeyword` | isMissing, isOnSameLine, kind, location, range, rawText, trivia, value, valueText |
| `ClassPropertyDeclaration` | attributes, declaration, kind, parent, qualifiers, sourceRange |
| `ConstraintDeclaration` | attributes, block, keyword, kind, name, parent, qualifiers, sourceRange, specifiers |
| `ConstraintKeyword` | isMissing, isOnSameLine, kind, location, range, rawText, trivia, value, valueText |
| `ConstraintBlock` | closeBrace, items, kind, openBrace, parent, sourceRange |
| `ExpressionConstraint` | expr, kind, parent, semi, soft, sourceRange |
| `EndClassKeyword` | isMissing, isOnSameLine, kind, location, range, rawText, trivia, value, valueText |
| `ImplicationConstraint` | arrow, constraints, kind, left, parent, sourceRange |
| `DistConstraintList` | closeBrace, dist, items, kind, openBrace, parent, sourceRange |
| `ConditionalConstraint` | closeParen, condition, constraints, elseClause, ifKeyword, kind, openParen, parent, sourceRange |
| `ElseConstraintClause` | constraints, elseKeyword, kind, parent, sourceRange |
| `LoopConstraint` | constraints, foreachKeyword, kind, loopList, parent, sourceRange |
| `SolveBeforeConstraint` | afterExpr, before, beforeExpr, kind, parent, semi, solve, sourceRange |
| `ClassMethodDeclaration` | attributes, declaration, kind, parent, qualifiers, sourceRange |

### 表达式类

| SyntaxKind | 属性 |
|------------|------|
| `IntegerLiteralExpression` | kind, literal, parent, sourceRange |
| `IntegerLiteral` | isMissing, isOnSameLine, kind, location, range, rawText, trivia, value |
| `ExpressionConstraint` | expr, kind, parent, semi, soft, sourceRange |
| `GreaterThanExpression` | attributes, kind, left, operatorToken, parent, right, sourceRange |
| `LessThanExpression` | attributes, kind, left, operatorToken, parent, right, sourceRange |
| `GreaterThanEqualExpression` | attributes, kind, left, operatorToken, parent, right, sourceRange |
| `LessThanEqualExpression` | attributes, kind, left, operatorToken, parent, right, sourceRange |
| `InequalityExpression` | attributes, kind, left, operatorToken, parent, right, sourceRange |
| `UnaryLogicalNotExpression` | attributes, kind, operand, operatorToken, parent, sourceRange |
| `EqualityExpression` | attributes, kind, left, operatorToken, parent, right, sourceRange |
| `ExpressionOrDist` | distribution, expr, kind, parent, sourceRange |
| `ValueRangeExpression` | closeBracket, kind, left, op, openBracket, parent, right, sourceRange |
| `LogicalOrExpression` | attributes, kind, left, operatorToken, parent, right, sourceRange |
| `ParenthesizedExpression` | closeParen, expression, kind, openParen, parent, sourceRange |
| `LogicalAndExpression` | attributes, kind, left, operatorToken, parent, right, sourceRange |
| `AddExpression` | attributes, kind, left, operatorToken, parent, right, sourceRange |
| `IntegerVectorExpression` | base, kind, parent, size, sourceRange, value |
| `InsideExpression` | expr, inside, kind, parent, ranges, sourceRange |
| `InvocationExpression` | arguments, attributes, kind, left, parent, sourceRange |
| `ExpressionStatement` | attributes, expr, kind, label, parent, semi, sourceRange |

---

## 完整属性列表

### 按类别

#### Module/Interface

**EndModuleKeyword**: isMissing, isOnSameLine, kind, location, range, rawText, trivia, value, valueText

**ModuleDeclaration**: attributes, blockName, endmodule, header, kind, members, parent, sourceRange

**ModuleHeader**: imports, kind, lifetime, moduleKeyword, name, parameters, parent, ports, semi, sourceRange

**ModuleKeyword**: isMissing, isOnSameLine, kind, location, range, rawText, trivia, value, valueText

#### Class

**ClassDeclaration**: attributes, classKeyword, endBlockName, endClass, extendsClause, finalSpecifier, implementsClause, items, kind, name, parameters, parent, semi, sourceRange, virtualOrInterface

**ClassKeyword**: isMissing, isOnSameLine, kind, location, range, rawText, trivia, value, valueText

**ClassMethodDeclaration**: attributes, declaration, kind, parent, qualifiers, sourceRange

**ClassMethodPrototype**: attributes, kind, parent, prototype, qualifiers, semi, sourceRange

**ClassPropertyDeclaration**: attributes, declaration, kind, parent, qualifiers, sourceRange

**EndClassKeyword**: isMissing, isOnSameLine, kind, location, range, rawText, trivia, value, valueText

#### Constraint

**ConditionalConstraint**: closeParen, condition, constraints, elseClause, ifKeyword, kind, openParen, parent, sourceRange

**ConstraintBlock**: closeBrace, items, kind, openBrace, parent, sourceRange

**ConstraintDeclaration**: attributes, block, keyword, kind, name, parent, qualifiers, sourceRange, specifiers

**ConstraintKeyword**: isMissing, isOnSameLine, kind, location, range, rawText, trivia, value, valueText

**DistConstraintList**: closeBrace, dist, items, kind, openBrace, parent, sourceRange

**ElseConstraintClause**: constraints, elseKeyword, kind, parent, sourceRange

**ExpressionConstraint**: expr, kind, parent, semi, soft, sourceRange

**ImplicationConstraint**: arrow, constraints, kind, left, parent, sourceRange

**LoopConstraint**: constraints, foreachKeyword, kind, loopList, parent, sourceRange

**SolveBeforeConstraint**: afterExpr, before, beforeExpr, kind, parent, semi, solve, sourceRange

#### Function/Task

**EndFunctionKeyword**: isMissing, isOnSameLine, kind, location, range, rawText, trivia, value, valueText

**FunctionDeclaration**: attributes, end, endBlockName, items, kind, parent, prototype, semi, sourceRange

**FunctionKeyword**: isMissing, isOnSameLine, kind, location, range, rawText, trivia, value, valueText

**FunctionPort**: attributes, constKeyword, dataType, declarator, direction, kind, parent, sourceRange, staticKeyword, varKeyword

**FunctionPortList**: closeParen, kind, openParen, parent, ports, sourceRange

**FunctionPrototype**: keyword, kind, lifetime, name, parent, portList, returnType, sourceRange, specifiers

#### Cover/Coverage

#### Sequence/Property/Assert

**ClassPropertyDeclaration**: attributes, declaration, kind, parent, qualifiers, sourceRange

**SimplePropertyExpr**: expr, kind, parent, sourceRange

**SimpleSequenceExpr**: expr, kind, parent, repetition, sourceRange

