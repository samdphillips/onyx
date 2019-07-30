# Trait Conversion

## Primary objective
Remove inheritance as primary method of code reuse.  Instead use composition of traits.

## Procedure
- Replace all parent classes in ost files with `nil`
  - A lot of things should break!
- Move base functionality from abtract classes (`Object`, `Collection`, etc.) into Traits and add those Traits to classes until tests work again.
- Revise syntax:
  - Replace `<parent-classname> subclass: <classname>` with `Class named: <classname> [ ... ]`
- Revise semantics:
  - Ensure that class evaluation procedes as:
    1. Evaluate Trait expression
    2. Merge Trait methods with Class methods
    3. Assign Class value to name
- Revise method lookup.  Traits should only require one level of lookup.

## Notes
- using `<class> uses: { T1. T2 }.` syntax fails before `Array` is defined.
  - Replace with `<class> uses: T1 + T2.`.
  - There are a few other places like this where `Trait` shorthand doesn't work.  Replacing it with low level manipulators.
- Explicit `super` calls don't work anymore.
  - It is specifically a problem because there is a semi-implicit in the VM superclass linkage on the class side methods.  `<classname> new` needs to be able to work for slotted classes.
  - Solution is probably to ensure that there is a distinction between class and instance method sides of traits.  I can't remember if this was implemented already.
- no hierarchy means that the Exception hierarchy for Exception selectors has to be recreated.
  - will create a protocol to establish kind of hierarchy