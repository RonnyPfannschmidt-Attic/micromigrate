Design Choices
===============



Simplicity
-----------

Inline Metadata
  this allows migrations to be self-contained files
Explicit dependencies to initial migration needed
  no special cases, the only migration that does not
  ned another is the initial one


Real World limitations
------------------------

Incomplete migrations are possible
  there currently are NO sqlite bindings for python
  that handle DDL transactions propperly,
  its simply not fixable as of February 1, 2014
