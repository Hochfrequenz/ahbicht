AHB Condition Expression Parser (AHBicht)
=========================================

|Unittests status badge| |Coverage status badge| |Linting status badge|
|Black status badge|

.. raw:: html

   <a href="https://ahbicht.readthedocs.io">
       <img src="../docs/_static/ahbicht-logo.png"
            alt="ahbicht logo"
            height="150px"
            align="right">
   </a>

A python package that parses condition expressions from EDI@Energy
Anwendungshandbücher (AHB). Since it's based on lark, we named the
module AHBicht.

What is this all about?
-----------------------

The German energy market uses `EDIFACT`_ as an intercompany data
exchange format. The rules on how to structure and validate the EDIFACT
messages are written in

-  one **M**\ essage **I**\ mplementation **G**\ uide (MIG) per EDIFACT
   format (for example UTILMD or MSCONS)
-  one **A**\ *\ nwendungs\ *\ **h**\ *\ and\ *\ **b**\ *\ uch* (AHB,
   en. manual) per use case group (for example `GPKE`_ or
   *Wechselprozesse im Messwesen* (WiM))

According to the legislation for the German energy market, the
organisations in charge of maintaining the documents described above
(AHB and MIGs) are the
**B**\ *\ undesverband*\ **d**\ *\ er*\ **E**\ *\ nergie-
und*\ **W**\ *\ asserwirtschaft* (BDEW) and the
**B**\ *\ undes\ *\ **netza**\ *\ gentur* (BNetzA). They form a working
group named "Arbeitsgruppe EDI@Energy". This work group publishes the
MIGs and AHBs on `edi-energy.de`_. The documents are published as PDFs
which is better than faxing them but far from ideal.

The AHBs contain information on how to structure single EDIFACT
messages. To create messages that are valid according to the respective
AHB, you have to process information of the kind:
|UTILMD_AHB_WiM_3_1b_20201016.pdf page 90|

In this example: **This library parses the string
``Muss [210] U ([182] X ([90] U [183]))`` and allows determining whether
"Details der Prognosegrundlage" is an obligatory field according to the
AHB, iff the individual status of the conditions is given.** We call
this "expression evaluation".

Note that determining the individual status of ``[210]``, ``[182]``,
``[90]`` and ``[183]`` itself (the so called "content evaluation", see
below) is **not** within the scope of this parsing library.

Usage
-----

.. code:: python

   from ahbicht import foo
   do something
   # todo: add mwe on how to use this library

.. _code-quality--production-readiness:

Code Quality / Production Readiness
-----------------------------------

-  The code has at least a 95% unit test coverage. ✔️
-  The code is rated 10/10 in pylint. ✔️
-  The code is MIT licensed. ✔️
-  There are only `few dependencies`_. ✔️

.. _expression-evaluation--parsing-the-condition-string:

Expression Evaluation / Parsing the Condition String
----------------------------------------------------

Evaluating expressions like ``Muss [59] U ([123] O [456])`` from

.. _EDIFACT: https://en.wikipedia.org/wiki/EDIFACT
.. _GPKE: https://de.wikipedia.org/wiki/Gesch%C3%A4ftsprozesse_zur_Kundenbelieferung_mit_Elektrizit%C3%A4t
.. _edi-energy.de: https://edi-energy.de/
.. _few dependencies: requirements.in

.. |Unittests status badge| image:: https://github.com/Hochfrequenz/ahbicht/workflows/Unittests/badge.svg
.. |Coverage status badge| image:: https://github.com/Hochfrequenz/ahbicht/workflows/Coverage/badge.svg
.. |Linting status badge| image:: https://github.com/Hochfrequenz/ahbicht/workflows/Linting/badge.svg
.. |Black status badge| image:: https://github.com/Hochfrequenz/ahbicht/workflows/Black/badge.svg
.. |UTILMD_AHB_WiM_3_1b_20201016.pdf page 90| image:: ../docs/_static/wim-ahb-screenshot.png
