# AHB Condition Expression Parser (AHBicht)

![Unittests status badge](https://github.com/Hochfrequenz/ahbicht/workflows/Unittests/badge.svg)
![Coverage status badge](https://github.com/Hochfrequenz/ahbicht/workflows/Coverage/badge.svg)
![Linting status badge](https://github.com/Hochfrequenz/ahbicht/workflows/Linting/badge.svg)
![Black status badge](https://github.com/Hochfrequenz/ahbicht/workflows/Black/badge.svg)

<a href="https://ahbcep.readthedocs.io">
    <img src="./media/ahbicht-logo.png"
         alt="ahbicht logo"
         height="150px"
         align="right">
</a>

A python package that parses condition expressions from EDI@Energy Anwendungshandbücher (AHB).
Since it's based on lark, we named the module AHBicht.

## What is this all about?

The German energy market uses [EDIFACT](https://en.wikipedia.org/wiki/EDIFACT) as an intercompany data exchange format.
The rules on how to structure and validate the EDIFACT messages are written in

- one **M**essage **I**mplementation **G**uide (MIG) per EDIFACT format (for example UTILMD or MSCONS)
- one _**A**nwendungs**h**and**b**uch_ (AHB, en. manual) per use case group (for example [GPKE](https://de.wikipedia.org/wiki/Gesch%C3%A4ftsprozesse_zur_Kundenbelieferung_mit_Elektrizit%C3%A4t) or _Wechselprozesse im Messwesen_ (WiM))

According to the legislation for the German energy market, the organisations in charge of maintaining the documents described above (AHB and MIGs) are the _**B**undesverband **d**er **E**nergie- und **W**asserwirtschaft_ (BDEW) and the _**B**undes**netza**gentur_ (BNetzA).
They form a working group named "Arbeitsgruppe EDI@Energy". This work group publishes the MIGs and AHBs on [edi-energy.de](https://edi-energy.de/).
The documents are published as PDFs which is better than faxing them but far from ideal.

The AHBs contain information on how to structure single EDIFACT messages.
To create messages that are valid according to the respective AHB, you have to process information of the kind:
![UTILMD_AHB_WiM_3_1b_20201016.pdf page 90](wim_ahb_screenshot.png)

In this example: **This library parses the string `Muss [210] U ([182] X ([90] U [183]))` and allows determining whether _"Details der Prognosegrundlage"_ is an obligatory field according to the AHB, iff the individual status of the conditions is given.**
We call this "expression evaluation".

Note that determining the individual status of `[210]`, `[182]`, `[90]` and `[183]` itself (the so called "content evaluation", see below) is **not** within the scope of this parsing library.

## Usage

```python
from ahbicht import foo
do something
# todo: add mwe on how to use this library
```

## Code Quality / Production Readiness

- The code has at least a 95% unit test coverage. ✔️
- The code is rated 10/10 in pylint. ✔
- The code is MIT licensed. ✔
- There are only [few dependencies](requirements.in). ✔

## Expression Evaluation / Parsing the Condition String

Evaluating expressions like `Muss [59] U ([123] O [456])` from the AHBs by parsing it with the [parsing library `lark`](https://lark-parser.readthedocs.io/en/latest/) and combining the parsing result with information about the state of `[59]`, `[123]`, `[456]` is called **expression evaluation**.
Determining the state of each single condition (f.e. `[59]` is fulfilled, `[123]` is not fulfilled, `[456]` is unknown) for a given message is part of the **content evaluation** (see next chapter).

If you're new to this topic, please read [edi-energy.de → Dokumente → Allgemeine Festlegungen](https://www.edi-energy.de/index.php?id=38&tx_bdew_bdew%5Buid%5D=956&tx_bdew_bdew%5Baction%5D=download&tx_bdew_bdew%5Bcontroller%5D=Dokument&cHash=ae3c1bd6fe3f664cd90f5e94f9714e3e) first.
This document contains German explanations, how the Bedingungen are supposed to be read.

### Functionality

- Expressions can contain single numbers e.g. `[47]` or numbers combined with `U`/`O`/`X` which are translated to boolean operators `and`/`or`/`exclusive or`, e.g. `[45]U[2]` or they can be combined **without** an operator, e.g. `[930][5]` in the case of FormatConstraints.
- Expressions can contain random whitespaces.
- Input conditions are passed in form of a `ConditionNode`, see below.
- Bedingungen/`RequirementConstraints` with a boolean value, Hinweise/`Hints` and Formatdefinitionen/`FormatConstraints` are so far functionally implemented as the result returns if the condition expression is fulfilled and which Hints and FormatConstraints are relevant.
- The boolean logic follows 'brackets `( )` before `then_also` before `and` before `or`'.
- Hints and UnevaluatedFormatConstraints are implemented as `neutral` element, so not changing the boolean outcome of an expression for the evaluation regarding the requirement constraints and raising errors when there is no sensible logical outcome of the expression.
- A `condition_fulfilled` attribute can also take the value `unknown`.
- Brackets e.g. `([43]O[4])U[5]`
- Requirement indicators (i.e `Muss`, `Soll`, `Kann`, `X`, `O`, `U`) are seperated from the condition expressions and also seperated into single requirement indicator expressions if there are more than one (for modal marks).
- `Format Constraint Expressions` that are returned after the requirement condition evaluation can now be parsed and evaluated.
- Evaluate several modal marks in one ahb_expression: the first one that evaluates to fulfilled is the valid one.

#### In planning:

- Evaluate requirement indicators:
  - Soll, Kann, Muss, X, O, U -> is_required, is_forbidden, etc...

### Definition of terms:

| Term                                           | Description                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   | Example                                                                                                               |
| ---------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| `condition`                                    | single operand                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                | `[53]`                                                                                                                |
| `condition_key`                                | `int` or `str`, the number of the condition                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   | `53`                                                                                                                  |
| `operator`                                     | combines two conditions                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       | `U`, `O`                                                                                                              |
| `composition`                                  | two parts of an expression combined by an operator <br> used in the context of the parsing and evaluation of the expression                                                                                                                                                                                                                                                                                                                                                                                                   | `([4]U[76])O[5]` consists of an `and_composition` of `[4]` and `[76]` and an `or_composition` of `[4]U[76]` and `[5]` |
| `ahb expression`                               | an expression as given from the ahb <br> Consists of at least one single requirement indicator expression. <br> In case of several model mark expressions the first one will be evaluated and if not fulfilled, it will be continued with the next one.                                                                                                                                                                                                                                                                       | `X[59]U[53]`<br> `Muss[59]U([123]O[456])Soll[53]`                                                                     |
| `single requirement indicator expression`      | An expression consisting of exactly one requirement indicator and their respective condition expression. <br> If there is only one requirement indicator in the ahb expression, then both expressions are identical.                                                                                                                                                                                                                                                                                                          | `Soll[53]`                                                                                                            |
| `condition expression`                         | one or multiple conditions combined with or (in case of FormatConstraints) also without operators <br> used as input for the condition parser                                                                                                                                                                                                                                                                                                                                                                                 | `[1]` <br> `[4]O[5]U[45]`                                                                                             |
| `format constraint expression`                 | Is returned after the evaluation of the RequirementConstraints <br> consist only of FormatConstraints                                                                                                                                                                                                                                                                                                                                                                                                                         | `[901]X[954]`                                                                                                         |
| `requirement indicator`                        | The Merkmal/modal_mark or Operator/prefix_operator of the data element/data element group/segment/segment group.                                                                                                                                                                                                                                                                                                                                                                                                              | `Muss`, `Soll`, `Kann`, `X`, `O`, `U`                                                                                 |
| `Merkmal` / `modal_mark`                       | as defined by the EDI Energy group (see [edi-energy.de → Dokumente → Allgemeine Festlegungen](https://www.edi-energy.de/index.php?id=38&tx_bdew_bdew%5Buid%5D=956&tx_bdew_bdew%5Baction%5D=download&tx_bdew_bdew%5Bcontroller%5D=Dokument&cHash=ae3c1bd6fe3f664cd90f5e94f9714e3e)) <br> Stands alone or before a condition expression, can be the start of several requirement indicator expressions in one ahb expression                                                                                                    | `Muss`, `Soll`, `Kann`                                                                                                |
| `Muss`                                         | Is required for the correct structure of the message <br> If the following condition is not fulfilled, the information **must not** be given.                                                                                                                                                                                                                                                                                                                                                                                 |
| `Soll`                                         | Is required for technical reasons. <br> Always followed by a condition. <br> If the following condition is not fulfilled, the information **must not** be given.                                                                                                                                                                                                                                                                                                                                                              |
| `Kann`                                         | Optional                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| `prefix operator`                              | Operator which does not function to combine conditions, but as requirement indicator. <br> Stands alone or in front of a condition expression.                                                                                                                                                                                                                                                                                                                                                                                | `X`, `O`, `U`                                                                                                         |
| `tree`, `branches`, `token`                    | as used by lark                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| `ConditionNode`                                | Defines the nodes of the tree as they are passed, evaluated und returned. <br> There are different kinds of conditions (`Bedingung`, `Hinweis`, `Format`) as defined by the EDI Energy group (see [edi-energy.de → Dokumente → Allgemeine Festlegungen](https://www.edi-energy.de/index.php?id=38&tx_bdew_bdew%5Buid%5D=956&tx_bdew_bdew%5Baction%5D=download&tx_bdew_bdew%5Bcontroller%5D=Dokument&cHash=ae3c1bd6fe3f664cd90f5e94f9714e3e)) and also a `EvaluatedComposition` after a composition of two nodes is evaluated. | `RequirementConstraint`, `FormatConstraint`, `Hint`, `EvaluatedComposition`                                           |
| `Bedingung` / `RequirementConstraint` (`rc`)   | - are true or false, has to be determined <br> - keys between `[1]` and `[499]`                                                                                                                                                                                                                                                                                                                                                                                                                                               | "falls SG2+IDE+CCI == EHZ"                                                                                            |
| `Hinweis` / `Hint`                             | - just a hint, even if it is worded like a condition <br> - keys from `[500]` onwards, starts with 'Hinweis:'                                                                                                                                                                                                                                                                                                                                                                                                                 | "Hinweis: 'ID der Messlokation'" <br> "Hinweis: 'Es ist der alte MSB zu verwenden'"                                   |
| `Formatdefinition` / `FormatConstraint` (`fc`) | - a constraint for how the data should be given <br> - keys between `[901]` and `[999]`, starts with 'Format:' <br>Format Constraints are "collected" while evaluating the rest of the tree, meaning the evaluated composition of the Mussfeldprüfung contains an expression that consists only of format constraints.                                                                                                                                                                                                        | "Format: Muss größer 0 sein" <br> "Format: max 5 Nachkommastellen"                                                    |
| `UnevaluatedFormatConstraint`                  | A format constraint that is just "collected" during the requirement constraint evaluation. To have a clear separation of conditions that affect whether a field is mandatory or not and those that check the format of fields without changing their state it will become a part of the `format_constraint_expression` which is part of the `EvaluatedComposition`.                                                                                                                                                           |
| `EvaluatableFormatConstraint`                  | An evaluatable FormatConstraint will (other than the `UnevaluatedFormatConstraint`) be evaluated by e.g. matching a regex, calculating a checksum etc. This happens _after_ the Mussfeldprüfung. (_details to be added upon implementing_)                                                                                                                                                                                                                                                                                    |
| `EvaluatedComposition`                         | is returned after a composition of two nodes is evaluated                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| `neutral`                                      | Hints and UnevaluatedFormat Constraints are seen as neutral as they don't have a condition to be fulfilled or unfulfilled and should not change the requirement outcome. See truth table below.                                                                                                                                                                                                                                                                                                                               |
| `unknown`                                      | If the condition can be fulfilled but we don't know (yet) if it is or not. See truth table below.                                                                                                                                                                                                                                                                                                                                                                                                                             | "Wenn vorhanden"                                                                                                      |

The decision if a requirement constraint is met / fulfilled / true is made in the content evaluation module.

### Program structure

The following diagram shows the structure of the condition check for more than one condition. If it is only a single condition or just a requirement indicator, the respective tree consists of just this token and the result equals the input.

![grafik](src/ahbicht/expressions/Condition_Structure_with_more_than_one_condition.png)

The raw and updated data for this diagram can be found in the [draw_io_charts repository](https://github.com/Hochfrequenz/draw_io_charts/tree/main/wimbee/conditions) and edited under [app.diagrams.net](https://app.diagrams.net/#HHochfrequenz%2Fdraw_io_charts%2Fmain%2Fwimbee%2Fconditions%2FCondition_Structure_with_more_than_one_condition.drawio) with your GitHub Account.

### Truth tables

Additionally to the usual boolean logic we also have `neutral` elements (e.g. `Hints`, `UnevaluatedFormatConstraints` and in some cases `EvaluatedCompositions`) or `unknown` requirement constraints. They are handled as follows:

#### `and_composition`

| A       | B       | A U B   |
| ------- | ------- | ------- |
| Neutral | True    | True    |
| Neutral | False   | False   |
| Neutral | Neutral | Neutral |
| Unknown | True    | Unknown |
| Unknown | False   | False   |
| Unknown | Unknown | Unknown |
| Unknown | Neutral | Unknown |

#### `or_composition`

| A       | B       | A O B               | note                                             |
| ------- | ------- | ------------------- | ------------------------------------------------ |
| Neutral | True    | does not make sense |
| Neutral | False   | does not make sense |
| Neutral | Neutral | Neutral             | no or_compositions of hint and format constraint |
| Unknown | True    | True                |
| Unknown | False   | Unknown             |
| Unknown | Unknown | Unknown             |
| Unknown | Neutral | does not make sense |

#### `xor_composition`

| A       | B       | A X B               | note                                              |
| ------- | ------- | ------------------- | ------------------------------------------------- |
| Neutral | True    | does not make sense |
| Neutral | False   | does not make sense |
| Neutral | Neutral | Neutral             | no xor_compositions of hint and format constraint |
| Unkown  | True    | Unknown             |
| Unkown  | False   | Unknown             |
| Unkown  | Unknown | Unknown             |
| Unkown  | Neutral | does not make sense |

Link to automatically generate HintsProvider Json content: https://regex101.com/r/za8pr3/5

## Content Evaluation

Evaluation is the term used for the processing of _single_ unevaluated conditions.
The results of the evaluation of all relevant conditions inside a message can then be used to validate a message.
The latter is **not** part of the evaluation.

This library does _not_ provide content evaluation code for all the conditions used in the available AHBs.
You can use the Content Evaluation class stubs though.
Please contact [@JoschaMetze](https://github.com/joschametze) if you're interested in a ready-to-use solution to validate your EDIFACT messages according to the latest AHBs.
We probably have you covered.

### EvaluatableData (Edifact Seed and others)

For the evaluation of a condition (that is referenced by its key, e.g. "17") it is necessary to have a data basis that allows to decide whether the respective condition is met or not met.
This data basis that is stable for all conditions that are evaluated in on evaluation run is called **`EvaluatableData`**.
These data usually contain the **edifact seed** (a JSON representation of the EDIFACT message) but may also hold other information.
The `EvaluatableData` class acts a container for these data.

### EvaluationContext (Scope and others)

While the data basis is stable, the context in which a condition is evaluated might change during on evaluation run.
The same condition can have different evaluation results depending on e.g. in which scope it is evaluated.
A **scope** is a (json) path that references a specific subtree of the edifact seed.
For example one "Vorgang" (`SG4 IDE`) in UTILMD could be a scope.
If a condition is described as

> There has to be exactly one xyz per Vorgang (SG4+IDE)

Then for `n` Vorgänge there are `n` scopes:

- one scope for each Vorgang (pathes refer to an edifact seed):
  - `$["Dokument"][0]["Nachricht"][0]["Vorgang"][0]`
  - `$["Dokument"][0]["Nachricht"][0]["Vorgang"][1]`
  - ...
  - `$["Dokument"][0]["Nachricht"][0]["Vorgang"][<n-1>]`

Each of the single vorgang scopes can have a different evaluation result.
Those results are relevant for the user when entering data, probably based in a somehow Vorgang-centric manner.

The **`EvaluationContext`** class is a container for the scope and other information that are relevant for a single condition and a single evaluation only but (other than `EvaluatableData`) might change within an otherwise stable message.

![grafik](src/ahbicht/content_evaluation/EvaluatingConditions.png)

<!-- The raw and updated data for this diagram can be found in the [draw_io_charts repository](https://github.com/Hochfrequenz/draw_io_charts/tree/main/wimbee/) and edited under [app.diagrams.net](https://app.diagrams.net/#HHochfrequenz%2Fdraw_io_charts%2Fmain%2Fwimbee%2FEvaluatingConditions.drawio) with your Hochfrequenz GitHub Account. -->

## Contributing

You are very welcome to contribute to this repository by opening a pull request against the main branch.

### How to use this Repository on Your Machine

This introduction assumes that you have tox installed already (see [installation instructions](https://tox.readthedocs.io/en/latest/install.html)) and that a `.toxbase` environment
has been created.

If this is the case, clone this repository and create the `dev` environment on your machine.

```bash
tox -e dev
```

#### How to use with PyCharm

1. Create a new project using existing sources with your local working copy of this repository as root directory. Choose
   the path `your_repo/.tox/dev/` as path of the "previously configured interpreter".
2. Set the
   default [test runner of your project](https://www.jetbrains.com/help/pycharm/choosing-your-testing-framework.html) to
   pytest.
3. Set
   the [working directory of the unit tests](https://www.jetbrains.com/help/pycharm/creating-run-debug-configuration-for-tests.html)
   to the project root (instead of the unittest directory)

#### How to use with VS Code

1. Open the folder with VS Code.
2. **Select the python interpreter** which is created by tox. Open the command pallett with `CTRL + P` and type `Python: Select Interpreter`. Select the interpreter which is placed in `.tox/dev/Scripts/python.exe` under Windows or `.tox/dev/bin/python` under Linux and macOS.
3. **Setup pytest and pylint**. Therefore we open the file `.vscode/settings.json` which should be automatically generated during the interpreter setup. Insert the following lines into the settings:

```json
    "python.testing.unittestEnabled": false,
    "python.testing.nosetestsEnabled": false,
    "python.testing.pytestEnabled": true,
    "pythonTestExplorer.testFramework": "pytest",
    "python.testing.pytestArgs": [
        "unittests"
    ],
    "python.linting.pylintEnabled": true
```

4. Enjoy 🤗
