# SyntaxKind 完整映射表

> 自动生成自 pyslang vunknown
> 生成时间: 2026-04-29

## 概览

| 类别 | 数量 |
|------|------|
| Module/Interface | 11 |
| Class | 8 |
| Declaration | 38 |
| Statement | 39 |
| Expression | 109 |
| Type | 28 |
| Port | 33 |
| Constraint | 10 |
| Cover | 17 |
| Sequence/Property | 40 |
| Clocking | 4 |
| Generate | 5 |
| Package | 2 |
| Other | 192 |

---

## 1. Module/Interface 声明

| SyntaxKind | SystemVerilog |
|------------|---------------|
| `AnonymousProgram` | |
| `ExternInterfaceMethod` | |
| `ExternModuleDecl` | |
| `InterfaceDeclaration` | |
| `InterfaceHeader` | |
| `InterfacePortHeader` | |
| `ModuleDeclaration` | |
| `ModuleHeader` | |
| `ProgramDeclaration` | |
| `ProgramHeader` | |
| `VirtualInterfaceType` | |

---

## 2. Class 相关

| SyntaxKind | SystemVerilog |
|------------|---------------|
| `ClassDeclaration` | |
| `ClassMethodDeclaration` | |
| `ClassMethodPrototype` | |
| `ClassName` | |
| `ClassPropertyDeclaration` | |
| `ClassSpecifier` | |
| `CopyClassExpression` | |
| `NewClassExpression` | |

---

## 3. Declaration 声明

| SyntaxKind | SystemVerilog |
|------------|---------------|
| `CheckerDataDeclaration` | |
| `CheckerDeclaration` | |
| `ClockingDeclaration` | |
| `ConditionalPathDeclaration` | |
| `ConfigDeclaration` | |
| `ConstraintDeclaration` | |
| `CovergroupDeclaration` | |
| `DataDeclaration` | |
| `DefaultDisableDeclaration` | |
| `ForVariableDeclaration` | |
| `ForwardTypedefDeclaration` | |
| `FunctionDeclaration` | |
| `GenvarDeclaration` | |
| `IfNonePathDeclaration` | |
| `LetDeclaration` | |
| `LibraryDeclaration` | |
| `LocalVariableDeclaration` | |
| `ModportDeclaration` | |
| `NetDeclaration` | |
| `NetTypeDeclaration` | |
| `PackageDeclaration` | |
| `PackageExportAllDeclaration` | |
| `PackageExportDeclaration` | |
| `PackageImportDeclaration` | |
| `ParameterDeclaration` | |
| `ParameterDeclarationStatement` | |
| `PathDeclaration` | |
| `PortDeclaration` | |
| `PropertyDeclaration` | |
| `PulseStyleDeclaration` | |
| `SequenceDeclaration` | |
| `SpecparamDeclaration` | |
| `TaskDeclaration` | |
| `TimeUnitsDeclaration` | |
| `TypeParameterDeclaration` | |
| `TypedefDeclaration` | |
| `UdpDeclaration` | |
| `UserDefinedNetDeclaration` | |

... 共 38 个 declaration 类型

---

## 4. Statement 语句

| SyntaxKind | SystemVerilog |
|------------|---------------|
| `AssertPropertyStatement` | |
| `AssumePropertyStatement` | |
| `BlockingEventTriggerStatement` | |
| `CaseStatement` | |
| `CheckerInstanceStatement` | |
| `ConditionalStatement` | |
| `CoverPropertyStatement` | |
| `CoverSequenceStatement` | |
| `DisableForkStatement` | |
| `DisableStatement` | |
| `DoWhileStatement` | |
| `EmptyStatement` | |
| `ExpectPropertyStatement` | |
| `ExpressionStatement` | |
| `ForLoopStatement` | |
| `ForeachLoopStatement` | |
| `ForeverStatement` | |
| `ImmediateAssertStatement` | |
| `ImmediateAssumeStatement` | |
| `ImmediateCoverStatement` | |
| `JumpStatement` | |
| `LibraryIncludeStatement` | |
| `LoopStatement` | |
| `NonblockingEventTriggerStatement` | |
| `ParallelBlockStatement` | |
| `ProceduralAssignStatement` | |
| `ProceduralDeassignStatement` | |
| `ProceduralForceStatement` | |
| `ProceduralReleaseStatement` | |
| `RandCaseStatement` | |
| `RandSequenceStatement` | |
| `RestrictPropertyStatement` | |
| `ReturnStatement` | |
| `SequentialBlockStatement` | |
| `TimingControlStatement` | |
| `VoidCastedCallStatement` | |
| `WaitForkStatement` | |
| `WaitOrderStatement` | |
| `WaitStatement` | |

---

## 5. Expression 表达式

| SyntaxKind | 说明 |
|------------|------|
| `AddAssignmentExpression` | |
| `AddExpression` | |
| `AndAssignmentExpression` | |
| `ArithmeticLeftShiftAssignmentExpression` | |
| `ArithmeticRightShiftAssignmentExpression` | |
| `ArithmeticShiftLeftExpression` | |
| `ArithmeticShiftRightExpression` | |
| `ArrayOrRandomizeMethodExpression` | |
| `AssignmentExpression` | |
| `AssignmentPatternExpression` | |
| `BadExpression` | |
| `BinaryAndExpression` | |
| `BinaryBlockEventExpression` | |
| `BinaryConditionalDirectiveExpression` | |
| `BinaryEventExpression` | |
| `BinaryOrExpression` | |
| `BinaryXnorExpression` | |
| `BinaryXorExpression` | |
| `CaseEqualityExpression` | |
| `CaseInequalityExpression` | |
| `CastExpression` | |
| `ColonExpressionClause` | |
| `ConcatenationExpression` | |
| `ConditionalExpression` | |
| `DefaultPatternKeyExpression` | |
| `DivideAssignmentExpression` | |
| `DivideExpression` | |
| `ElementSelectExpression` | |
| `EmptyQueueExpression` | |
| `EqualityExpression` | |
| `EventControlWithExpression` | |
| `ExpressionConstraint` | |
| `ExpressionCoverageBinInitializer` | |
| `ExpressionOrDist` | |
| `ExpressionPattern` | |
| `ExpressionTimingCheckArg` | |
| `GreaterThanEqualExpression` | |
| `GreaterThanExpression` | |
| `InequalityExpression` | |
| `InsideExpression` | |
| `IntegerLiteralExpression` | |
| `IntegerVectorExpression` | |
| `InvocationExpression` | |
| `LessThanEqualExpression` | |
| `LessThanExpression` | |
| `LogicalAndExpression` | |
| `LogicalEquivalenceExpression` | |
| `LogicalImplicationExpression` | |
| `LogicalLeftShiftAssignmentExpression` | |
| `LogicalOrExpression` | |
| `LogicalRightShiftAssignmentExpression` | |
| `LogicalShiftLeftExpression` | |
| `LogicalShiftRightExpression` | |
| `MemberAccessExpression` | |
| `MinTypMaxExpression` | |
| `ModAssignmentExpression` | |
| `ModExpression` | |
| `MultipleConcatenationExpression` | |
| `MultiplyAssignmentExpression` | |
| `MultiplyExpression` | |

... 共 109 个 expression 类型

---

## 6. Constraint 约束

| SyntaxKind | SystemVerilog |
|------------|---------------|
| `ConditionalConstraint` | |
| `ConstraintBlock` | |
| `ConstraintPrototype` | |
| `DisableConstraint` | |
| `DistConstraintList` | |
| `ElseConstraintClause` | |
| `ImplicationConstraint` | |
| `LoopConstraint` | |
| `SolveBeforeConstraint` | |
| `UniquenessConstraint` | |

---

## 7. Cover 覆盖

| SyntaxKind | SystemVerilog |
|------------|---------------|
| `BinaryBinsSelectExpr` | |
| `BinsSelectConditionExpr` | |
| `BinsSelection` | |
| `BlockCoverageEvent` | |
| `CoverCross` | |
| `CoverageBins` | |
| `CoverageBinsArraySize` | |
| `CoverageIffClause` | |
| `CoverageOption` | |
| `Coverpoint` | |
| `DefaultCoverageBinInitializer` | |
| `IdWithExprCoverageBinInitializer` | |
| `ParenthesizedBinsSelectExpr` | |
| `RangeCoverageBinInitializer` | |
| `SimpleBinsSelectExpr` | |
| `TransListCoverageBinInitializer` | |
| `UnaryBinsSelectExpr` | |

---

## 8. Sequence/Property 序列/属性

| SyntaxKind | SystemVerilog |
|------------|---------------|
| `AcceptOnPropertyExpr` | |
| `AndPropertyExpr` | |
| `AndSequenceExpr` | |
| `CasePropertyExpr` | |
| `ClockingPropertyExpr` | |
| `ClockingSequenceExpr` | |
| `ConcurrentAssertionMember` | |
| `ConditionalPropertyExpr` | |
| `DefaultPropertyCaseItem` | |
| `DeferredAssertion` | |
| `DelayedSequenceElement` | |
| `DelayedSequenceExpr` | |
| `ElsePropertyClause` | |
| `EqualsAssertionArgClause` | |
| `FirstMatchSequenceExpr` | |
| `FollowedByPropertyExpr` | |
| `IffPropertyExpr` | |
| `ImmediateAssertionMember` | |
| `ImplicationPropertyExpr` | |
| `ImpliesPropertyExpr` | |
| `IntersectSequenceExpr` | |
| `OrPropertyExpr` | |
| `OrSequenceExpr` | |
| `ParenthesizedPropertyExpr` | |
| `ParenthesizedSequenceExpr` | |
| `PropertySpec` | |
| `SUntilPropertyExpr` | |
| `SUntilWithPropertyExpr` | |
| `SequenceMatchList` | |
| `SequenceRepetition` | |
| `SimplePropertyExpr` | |
| `SimpleSequenceExpr` | |
| `StandardPropertyCaseItem` | |
| `StrongWeakPropertyExpr` | |
| `ThroughoutSequenceExpr` | |
| `UnaryPropertyExpr` | |
| `UnarySelectPropertyExpr` | |
| `UntilPropertyExpr` | |
| `UntilWithPropertyExpr` | |
| `WithinSequenceExpr` | |

---

## 9. Port 端口

| SyntaxKind | 说明 |
|------------|------|
| `AnsiPortList` | |
| `AnsiUdpPortList` | |
| `AssertionItemPort` | |
| `AssertionItemPortList` | |
| `DefaultFunctionPort` | |
| `EmptyNonAnsiPort` | |
| `EmptyPortConnection` | |
| `ExplicitAnsiPort` | |
| `ExplicitNonAnsiPort` | |
| `FunctionPort` | |
| `FunctionPortList` | |
| `ImplicitAnsiPort` | |
| `ImplicitNonAnsiPort` | |
| `ModportClockingPort` | |
| `ModportExplicitPort` | |
| `ModportNamedPort` | |
| `ModportSimplePortList` | |
| `ModportSubroutinePort` | |
| `ModportSubroutinePortList` | |
| `NamedPortConnection` | |
| `NetPortHeader` | |
| `NonAnsiPortList` | |
| `NonAnsiUdpPortList` | |
| `OrderedPortConnection` | |
| `ParameterPortList` | |
| `PortConcatenation` | |
| `PortReference` | |
| `UdpInputPortDecl` | |
| `UdpOutputPortDecl` | |
| `VariablePortHeader` | |

... 共 33 个 port 类型

---

## 10. Clocking 时钟

| SyntaxKind | SystemVerilog |
|------------|---------------|
| `ClockingDirection` | |
| `ClockingItem` | |
| `ClockingSkew` | |
| `DefaultClockingReference` | |

---

## 11. Generate 生成

| SyntaxKind | SystemVerilog |
|------------|---------------|
| `CaseGenerate` | |
| `GenerateBlock` | |
| `GenerateRegion` | |
| `IfGenerate` | |
| `LoopGenerate` | |

---

## 12. Type 类型

| SyntaxKind | SystemVerilog |
|------------|---------------|
| `BitType` | |
| `ByteType` | |
| `CHandleType` | |
| `DefaultNetTypeDirective` | |
| `EnumType` | |
| `EqualsTypeClause` | |
| `EventType` | |
| `ForwardTypeRestriction` | |
| `ImplicitType` | |
| `IntType` | |
| `IntegerType` | |
| `LogicType` | |
| `LongIntType` | |
| `NamedType` | |
| `PropertyType` | |
| `RealTimeType` | |
| `RealType` | |
| `RegType` | |
| `SequenceType` | |
| `ShortIntType` | |
| `ShortRealType` | |
| `StringType` | |
| `StructType` | |
| `TimeType` | |
| `TypeAssignment` | |
| `TypeReference` | |
| `UnionType` | |
| `VoidType` | |
