# IEEE 1800-2017 SystemVerilog - FSM Recognition

> Source: IEEE 1800-2017 Language Reference Manual, Section 40.4

---

## 40.4 FSM recognition

Coverage tools need to have automatic recognition of many of the common FSM coding idioms in SystemVerilog. This standard does not attempt to describe or require any specific automatic FSM recognition mechanisms. However, this standard does prescribe a means by which nonautomatic FSM extraction occurs. The presence of any of these standard FSM description additions shall override the tool's default extraction mechanism.

Identification of an FSM consists of identifying the following items:
- The state register (or expression)
- The next state register (this is optional)
- The legal states

### 40.4.1 Specifying signal that holds current state

Use the following pragma to identify the vector signal that holds the current state of the FSM:

```systemverilog
/* tool state_vector signal_name */
```

where `tool` and `state_vector` are required keywords. This pragma needs to be specified inside the module definition where the signal is declared.

Another pragma is also required that specifies an enumeration name for the FSM. This enumeration name is also specified for the next state and any possible states, associating them with each other as part of the same FSM. There are two ways to do this:

- Use the same pragma as above:
  ```systemverilog
  /* tool state_vector signal_name enum enumeration_name */
  ```

- Use a separate pragma in the signal's declaration:
  ```systemverilog
  /* tool state_vector signal_name */
  logic [7:0] /* tool enum enumeration_name */ signal_name;
  ```

In either case, `enum` is a required keyword. If using a separate pragma, `tool` is also a required keyword, and the pragma needs to be specified immediately after the bit range of the signal.

### 40.4.2 Specifying part-select that holds current state

A part-select of a vector signal can be used to hold the current state of the FSM. When a coverage tool displays or reports FSM coverage data, it names the FSM after the signal that holds the current state. If a part-select holds the current state in the user's FSM, the user needs to also specify a name for the FSM for the coverage tool to use. The FSM name is not the same as the enumeration name.

Specify the part-select by using the following pragma:

```systemverilog
/* tool state_vector signal_name[n:n] FSM_name enum enumeration_name */
```

### 40.4.3 Specifying concatenation that holds current state

Like specifying a part-select, a concatenation of signals can be specified to hold the current state (when including an FSM name and an enumeration name):

```systemverilog
/* tool state_vector {signal_name, signal_name, ...} FSM_name enum enumeration_name */
```

The concatenation is composed of all the signals specified. Bit-selects or part-selects of signals cannot be used in the concatenation.

### 40.4.4 Specifying signal that holds next state

The signal that holds the next state of the FSM can also be specified with the pragma that specifies the enumeration name:

```systemverilog
logic [7:0] /* tool enum enumeration_name */ signal_name
```

This pragma can be omitted if, and only if, the FSM does not have a signal for the next state.

### 40.4.5 Specifying current and next state signals in same declaration

The tool assumes the first signal following the pragma holds the current state and the next signal holds the next state when a pragma is used for specifying the enumeration name in a declaration of multiple signals.

For example:

```systemverilog
/* tool state_vector cs */
logic [1:0] /* tool enum myFSM */ cs, ns, nonstate;
```

In this example, the tool assumes signal `cs` holds the current state and signal `ns` holds the next state. It assumes nothing about signal `nonstate`.

### 40.4.6 Specifying possible states of FSM

The possible states of the FSM can also be specified with a pragma that includes the following enumeration name:

```systemverilog
parameter /* tool enum enumeration_name */
S0 = 0,
s1 = 1,
s2 = 2,
s3 = 3;
```

Put this pragma immediately after the keyword `parameter`, unless a bit width for the parameters is used, in which case, specify the pragma immediately after the bit width:

```systemverilog
parameter [1:0] /* tool enum enumeration_name */
S0 = 0,
s1 = 1,
s2 = 2,
s3 = 3;
```

### 40.4.7 Pragmas in one-line comments

These pragmas work in both block comments, between the `/*` and `*/` character strings, and one-line comments, following the `//` character string. For example:

```systemverilog
parameter [1:0] // tool enum enumeration_name
S0 = 0,
s1 = 1,
s2 = 2,
s3 = 3;
```

### 40.4.8 Example

See Figure 40-2 for an example of FSM specified with pragmas.
